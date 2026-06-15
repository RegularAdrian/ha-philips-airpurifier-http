"""HTTP client for Philips connected air purifiers."""

from __future__ import annotations

import base64
import json
import logging
import secrets
from typing import Any

from aiohttp import ClientError, ClientSession
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

_LOGGER = logging.getLogger(__name__)

G_HEX = (
    "A4D1CBD5C3FD34126765A442EFB99905F8104DD258AC507FD6406CFF14266D31266FEA"
    "1E5C41564B777E690F5504F213160217B4B01B886A5E91547F9E2749F4D7FBD7D3B9"
    "A92EE1909D0D2263F80A76A6A24C087A091F531DBF0A0169B6A28AD662A4D18E73A"
    "FA32D779D5918D08BC8858F4DCEF97C2A24855E6EEB22B3B2E5"
)

P_HEX = (
    "B10B8F96A080E01DDE92DE5EAE5D54EC52C99FBCFB06A3C69A6A9DCA52D23B6160"
    "73E28675A23D189838EF1E2EE652C013ECB4AEA906112324975C3CD49B83BFACCBD"
    "D7D90C4BD7098488E9C219A73724EFFD6FAE5644738FAA31A4FF55BCCC0A151AF"
    "5F0DC8B4BD45BF37DF365C1A65E68CFDA76D4DA708DF1FB2BC2E4A4371"
)

AIR_ENDPOINT = "/di/v1/products/1/air"
FIRMWARE_ENDPOINT = "/di/v1/products/0/firmware"
FILTERS_ENDPOINT = "/di/v1/products/1/fltsts"
SECURITY_ENDPOINT = "/di/v1/products/0/security"


class PhilipsAirError(Exception):
    """Base error for Philips Air API failures."""


class PhilipsAirConnectionError(PhilipsAirError):
    """Raised when the purifier cannot be reached."""


def _pad(data: bytes) -> bytes:
    padding_length = 16 - (len(data) % 16)
    return data + bytes([padding_length]) * padding_length


def _unpad(data: bytes) -> bytes:
    if not data:
        raise PhilipsAirError("Empty encrypted response")
    padding_length = data[-1]
    if padding_length < 1 or padding_length > 16:
        raise PhilipsAirError("Invalid response padding")
    return data[:-padding_length]


def _aes_cbc_decrypt(data: bytes, key: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CBC(bytes(16)))
    decryptor = cipher.decryptor()
    return decryptor.update(data) + decryptor.finalize()


def _aes_cbc_encrypt(data: bytes, key: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CBC(bytes(16)))
    encryptor = cipher.encryptor()
    return encryptor.update(data) + encryptor.finalize()


class PhilipsAirHttpClient:
    """Encrypted HTTP client compatible with newer Philips Air devices."""

    def __init__(self, session: ClientSession, host: str, timeout: int) -> None:
        self._session = session
        self._host = host
        self._timeout = timeout
        self._key: bytes | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self._host}"

    async def get_key(self) -> bytes:
        """Perform the Philips Diffie-Hellman key exchange."""
        p = int(P_HEX, 16)
        g = int(G_HEX, 16)
        private_key = secrets.randbelow(p - 2) + 2
        public_key = pow(g, private_key, p)
        public_hex = f"{public_key:x}"

        try:
            response = await self._session.put(
                f"{self.base_url}{SECURITY_ENDPOINT}",
                json={"diffie": public_hex},
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = await response.json()
        except (ClientError, TimeoutError) as err:
            raise PhilipsAirConnectionError(f"Could not negotiate key with {self._host}: {err}") from err

        shared_secret = pow(int(payload["hellman"], 16), private_key, p)
        shared_bytes = shared_secret.to_bytes((shared_secret.bit_length() + 7) // 8, "big")
        shared_key = shared_bytes[:16]
        decrypted_key = _aes_cbc_decrypt(bytes.fromhex(payload["key"]), shared_key)
        self._key = decrypted_key[:16]
        return self._key

    async def _ensure_key(self) -> bytes:
        if self._key is None:
            return await self.get_key()
        return self._key

    def _decrypt_payload(self, payload: str, key: bytes) -> dict[str, Any]:
        decrypted = _aes_cbc_decrypt(base64.b64decode(payload), key)
        decoded = _unpad(decrypted[2:]).decode("utf-8")
        return json.loads(decoded)

    def _encrypt_payload(self, values: dict[str, Any], key: bytes) -> str:
        plaintext = b"AA" + json.dumps(values, separators=(",", ":")).encode("ascii")
        return base64.b64encode(_aes_cbc_encrypt(_pad(plaintext), key)).decode("ascii")

    async def get_data(self, endpoint: str) -> dict[str, Any]:
        """Read and decrypt an endpoint, refreshing the key once if needed."""
        key = await self._ensure_key()
        try:
            response = await self._session.get(f"{self.base_url}{endpoint}", timeout=self._timeout)
            response.raise_for_status()
            return self._decrypt_payload(await response.text(), key)
        except Exception as first_error:  # noqa: BLE001 - any decrypt/HTTP failure may mean stale key.
            _LOGGER.debug("Refreshing Philips Air HTTP key after read failure: %s", first_error)
            key = await self.get_key()
            try:
                response = await self._session.get(f"{self.base_url}{endpoint}", timeout=self._timeout)
                response.raise_for_status()
                return self._decrypt_payload(await response.text(), key)
            except Exception as err:  # noqa: BLE001
                raise PhilipsAirConnectionError(f"Could not read {endpoint} from {self._host}: {err}") from err

    async def get_status(self) -> dict[str, Any]:
        return await self.get_data(AIR_ENDPOINT)

    async def get_firmware(self) -> dict[str, Any]:
        return await self.get_data(FIRMWARE_ENDPOINT)

    async def get_filters(self) -> dict[str, Any]:
        return await self.get_data(FILTERS_ENDPOINT)

    async def set_values(self, values: dict[str, Any]) -> None:
        key = await self._ensure_key()
        encrypted = self._encrypt_payload(values, key)
        try:
            response = await self._session.put(
                f"{self.base_url}{AIR_ENDPOINT}",
                data=encrypted,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except Exception as err:  # noqa: BLE001
            self._key = None
            raise PhilipsAirConnectionError(f"Could not write values to {self._host}: {err}") from err
