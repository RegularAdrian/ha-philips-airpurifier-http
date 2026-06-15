"""Number entities for Philips Air Purifier HTTP."""

from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PhilipsAirDataCoordinator
from .entity import PhilipsAirEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Philips Air number entities."""
    coordinator: PhilipsAirDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PhilipsAirTimerNumber(coordinator)])


class PhilipsAirTimerNumber(PhilipsAirEntity, NumberEntity):
    """Built-in purifier timer control."""

    _attr_name = "Timer"
    _attr_native_min_value = 0
    _attr_native_max_value = 12
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: PhilipsAirDataCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.host}_timer"

    @property
    def native_value(self) -> int | None:
        value = self.data.get("dt")
        if value is None:
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        hours = max(0, min(12, int(round(value))))
        payload: dict[str, Any] = {"dt": hours}
        if hours == 0:
            payload["dtrs"] = 0
        await self.coordinator.client.set_values(payload)
        await self.coordinator.async_request_refresh()
