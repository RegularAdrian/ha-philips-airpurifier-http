"""Coordinator for Philips Air Purifier HTTP."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PhilipsAirConnectionError, PhilipsAirHttpClient
from .const import CONF_POLLING_INTERVAL, CONF_TIMEOUT, DEFAULT_POLLING_INTERVAL, DEFAULT_TIMEOUT, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PhilipsAirDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch Philips Air Purifier status on a fixed interval."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.host = entry.data[CONF_HOST]
        self.name = entry.data.get(CONF_NAME, self.host)
        self.client = PhilipsAirHttpClient(
            async_get_clientsession(hass),
            self.host,
            int(entry.options.get(CONF_TIMEOUT, entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT))),
        )
        interval = int(
            entry.options.get(
                CONF_POLLING_INTERVAL,
                entry.data.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL),
            )
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{self.host}",
            update_interval=timedelta(seconds=interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            status = await self.client.get_status()
            try:
                filters = await self.client.get_filters()
                status.update(filters)
            except PhilipsAirConnectionError as err:
                _LOGGER.debug("Filter update failed for %s: %s", self.host, err)
            try:
                firmware = await self.client.get_firmware()
                status.update({f"firmware_{key}": value for key, value in firmware.items()})
            except PhilipsAirConnectionError as err:
                _LOGGER.debug("Firmware update failed for %s: %s", self.host, err)
            return status
        except PhilipsAirConnectionError as err:
            raise UpdateFailed(str(err)) from err
