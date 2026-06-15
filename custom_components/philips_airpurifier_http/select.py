"""Select entities for Philips Air Purifier HTTP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
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

MODE_NORMAL = "Normal"
MODE_ALLERGY = "Allergy"
MODE_BACTERIA = "Bacteria/Virus"

SPEED_SLEEP = "Sleep"
SPEED_1 = "Speed 1"
SPEED_2 = "Speed 2"
SPEED_3 = "Speed 3"
SPEED_TURBO = "Turbo"


@dataclass(frozen=True)
class PhilipsAirSelectDescription:
    """Description for a select entity."""

    key: str
    name: str
    options: list[str]


SELECTS = (
    PhilipsAirSelectDescription(
        key="auto_mode",
        name="Auto Mode",
        options=[MODE_NORMAL, MODE_ALLERGY, MODE_BACTERIA],
    ),
    PhilipsAirSelectDescription(
        key="fan_speed",
        name="Fan Speed",
        options=[SPEED_SLEEP, SPEED_1, SPEED_2, SPEED_3, SPEED_TURBO],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Philips Air select entities."""
    coordinator: PhilipsAirDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PhilipsAirSelect(coordinator, description) for description in SELECTS])


class PhilipsAirSelect(PhilipsAirEntity, SelectEntity):
    """Select entity for explicit purifier controls."""

    def __init__(
        self,
        coordinator: PhilipsAirDataCoordinator,
        description: PhilipsAirSelectDescription,
    ) -> None:
        super().__init__(coordinator)
        self._description = description
        self._attr_name = description.name
        self._attr_options = description.options
        self._attr_unique_id = f"{coordinator.host}_{description.key}"

    @property
    def current_option(self) -> str | None:
        mode = self.data.get("mode")
        speed = self.data.get("om")

        if self._description.key == "auto_mode":
            if mode == "P":
                return MODE_NORMAL
            if mode == "A":
                return MODE_ALLERGY
            if mode == "B":
                return MODE_BACTERIA
            return None

        if speed == "s":
            return SPEED_SLEEP
        if speed == "1":
            return SPEED_1
        if speed == "2":
            return SPEED_2
        if speed == "3":
            return SPEED_3
        if speed == "t":
            return SPEED_TURBO
        return None

    async def async_select_option(self, option: str) -> None:
        values: dict[str, Any] | None = None

        if self._description.key == "auto_mode":
            values = {
                MODE_NORMAL: {"pwr": "1", "mode": "P"},
                MODE_ALLERGY: {"pwr": "1", "mode": "A"},
                MODE_BACTERIA: {"pwr": "1", "mode": "B"},
            }.get(option)
        else:
            values = {
                SPEED_SLEEP: {"pwr": "1", "mode": "M", "om": "s"},
                SPEED_1: {"pwr": "1", "mode": "M", "om": "1"},
                SPEED_2: {"pwr": "1", "mode": "M", "om": "2"},
                SPEED_3: {"pwr": "1", "mode": "M", "om": "3"},
                SPEED_TURBO: {"pwr": "1", "mode": "M", "om": "t"},
            }.get(option)

        if values is None:
            return
        await self.coordinator.client.set_values(values)
        await self.coordinator.async_request_refresh()
