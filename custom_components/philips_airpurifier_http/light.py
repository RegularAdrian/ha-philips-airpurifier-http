"""Light platform for Philips Air Purifier HTTP."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_LIGHT_CONTROL, DOMAIN
from .coordinator import PhilipsAirDataCoordinator
from .entity import PhilipsAirEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up optional Philips Air light entity."""
    if not entry.data.get(CONF_LIGHT_CONTROL, True):
        return
    coordinator: PhilipsAirDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PhilipsAirLight(coordinator)])


class PhilipsAirLight(PhilipsAirEntity, LightEntity):
    """Display/air-quality light entity."""

    _attr_name = "Light"
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS

    def __init__(self, coordinator: PhilipsAirDataCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.host}_light"

    @property
    def is_on(self) -> bool:
        return str(self.data.get("uil")) == "1" or int(self.data.get("aqil") or 0) > 0

    @property
    def brightness(self) -> int | None:
        value = self.data.get("aqil")
        if value is None:
            return None
        return round(max(0, min(100, int(value))) * 255 / 100)

    async def async_turn_on(self, **kwargs: Any) -> None:
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        level = 100 if brightness is None else round(int(brightness) * 100 / 255)
        await self.coordinator.client.set_values({"aqil": level, "uil": "1"})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_values({"aqil": 0, "uil": "0"})
        await self.coordinator.async_request_refresh()
