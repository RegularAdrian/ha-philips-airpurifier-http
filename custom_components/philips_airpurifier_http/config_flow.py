"""Config flow for Philips Air Purifier HTTP."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PhilipsAirConnectionError, PhilipsAirHttpClient
from .const import (
    CONF_ALLERGY_MODE,
    CONF_LIGHT_CONTROL,
    CONF_POLLING_INTERVAL,
    CONF_SLEEP_SPEED,
    CONF_TIMEOUT,
    DEFAULT_NAME,
    DEFAULT_POLLING_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MIN_POLLING_INTERVAL,
)


class PhilipsAirConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Philips Air Purifier HTTP config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            client = PhilipsAirHttpClient(
                async_get_clientsession(self.hass),
                host,
                user_input[CONF_TIMEOUT],
            )
            try:
                status = await client.get_status()
            except PhilipsAirConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                title = user_input.get(CONF_NAME) or status.get("name") or DEFAULT_NAME
                user_input[CONF_HOST] = host
                user_input[CONF_NAME] = title
                return self.async_create_entry(title=title, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.All(int, vol.Range(min=5, max=90)),
                vol.Optional(
                    CONF_POLLING_INTERVAL,
                    default=DEFAULT_POLLING_INTERVAL,
                ): vol.All(int, vol.Range(min=MIN_POLLING_INTERVAL, max=3600)),
                vol.Optional(CONF_SLEEP_SPEED, default=True): bool,
                vol.Optional(CONF_ALLERGY_MODE, default=True): bool,
                vol.Optional(CONF_LIGHT_CONTROL, default=True): bool,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
