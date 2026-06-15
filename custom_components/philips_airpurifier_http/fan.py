"""Fan platform for Philips Air Purifier HTTP."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_ALLERGY_MODE,
    CONF_SLEEP_SPEED,
    DOMAIN,
    PRESET_ALLERGY,
    PRESET_BACTERIA,
    PRESET_NORMAL,
    PRESET_SLEEP,
    PRESET_SPEED_1,
    PRESET_SPEED_2,
    PRESET_SPEED_3,
    PRESET_TURBO,
)
from .coordinator import PhilipsAirDataCoordinator
from .entity import PhilipsAirEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Philips Air fan entity."""
    coordinator: PhilipsAirDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PhilipsAirFan(coordinator, entry)])


class PhilipsAirFan(PhilipsAirEntity, FanEntity):
    """Philips Air Purifier fan entity."""

    _attr_name = None
    _attr_supported_features = FanEntityFeature.PRESET_MODE

    def __init__(self, coordinator: PhilipsAirDataCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{coordinator.host}_fan"

    @property
    def is_on(self) -> bool:
        return str(self.data.get("pwr")) == "1"

    @property
    def preset_modes(self) -> list[str]:
        modes = [PRESET_NORMAL, PRESET_ALLERGY, PRESET_BACTERIA, PRESET_SPEED_1, PRESET_SPEED_2, PRESET_SPEED_3, PRESET_TURBO]
        if self._entry.data.get(CONF_SLEEP_SPEED, True):
            modes.insert(3, PRESET_SLEEP)
        if not self._entry.data.get(CONF_ALLERGY_MODE, True):
            modes.remove(PRESET_ALLERGY)
            modes.remove(PRESET_BACTERIA)
        return modes

    @property
    def preset_mode(self) -> str | None:
        mode = self.data.get("mode")
        speed = self.data.get("om")
        if mode == "A":
            return PRESET_ALLERGY
        if mode == "B":
            return PRESET_BACTERIA
        if mode == "P":
            return PRESET_NORMAL
        if speed == "s":
            return PRESET_SLEEP
        if speed == "t":
            return PRESET_TURBO
        if speed in ("1", "2", "3"):
            return f"speed_{speed}"
        if mode == "M":
            return PRESET_SPEED_1
        return None

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        if preset_mode:
            await self.async_set_preset_mode(preset_mode)
            return
        await self.coordinator.client.set_values({"pwr": "1"})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_values({"pwr": "0"})
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        values: dict[str, Any]
        if preset_mode == PRESET_NORMAL:
            values = {"pwr": "1", "mode": "P"}
        elif preset_mode == PRESET_ALLERGY:
            values = {"pwr": "1", "mode": "A"}
        elif preset_mode == PRESET_BACTERIA:
            values = {"pwr": "1", "mode": "B"}
        elif preset_mode == PRESET_SLEEP:
            values = {"pwr": "1", "mode": "M", "om": "s"}
        elif preset_mode == PRESET_TURBO:
            values = {"pwr": "1", "mode": "M", "om": "t"}
        elif preset_mode == PRESET_SPEED_1:
            values = {"pwr": "1", "mode": "M", "om": "1"}
        elif preset_mode == PRESET_SPEED_2:
            values = {"pwr": "1", "mode": "M", "om": "2"}
        elif preset_mode == PRESET_SPEED_3:
            values = {"pwr": "1", "mode": "M", "om": "3"}
        else:
            return
        await self.coordinator.client.set_values(values)
        await self.coordinator.async_request_refresh()
