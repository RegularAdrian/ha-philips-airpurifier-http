"""Sensor platform for Philips Air Purifier HTTP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    PERCENTAGE,
    UnitOfTime,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PhilipsAirDataCoordinator
from .entity import PhilipsAirEntity


@dataclass(frozen=True, kw_only=True)
class PhilipsAirSensorDescription(SensorEntityDescription):
    """Description of a Philips Air sensor."""

    source_key: str | None = None
    value_fn: Callable[[Any], Any] | None = None


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _filter_percent(total_hours: int) -> Callable[[Any], int | None]:
    def convert(value: Any) -> int | None:
        raw = _as_int(value)
        if raw is None:
            return None
        return max(0, min(100, round(raw / total_hours * 100)))

    return convert


def _air_quality_label(value: Any) -> str | None:
    raw = _as_int(value)
    if raw is None:
        return None
    homekit_value = max(1, min(5, (raw + 2) // 3))
    return {
        1: "Excellent",
        2: "Good",
        3: "Fair",
        4: "Inferior",
        5: "Poor",
    }[homekit_value]


def _timer_remaining_minutes(value: Any) -> int | None:
    raw = _as_int(value)
    if raw is None:
        return None
    # Philips reports dtrs as remaining seconds on many models.
    return round(raw / 60)


SENSORS: tuple[PhilipsAirSensorDescription, ...] = (
    PhilipsAirSensorDescription(
        key="pm25",
        name="PM2.5",
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        device_class=SensorDeviceClass.PM25,
        value_fn=_as_int,
    ),
    PhilipsAirSensorDescription(
        key="air_quality",
        source_key="iaql",
        name="Air Quality",
        state_class=None,
        value_fn=_air_quality_label,
    ),
    PhilipsAirSensorDescription(
        key="rh",
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        value_fn=_as_int,
    ),
    PhilipsAirSensorDescription(
        key="temp",
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=_as_int,
    ),
    PhilipsAirSensorDescription(key="iaql", name="Indoor Allergen Index", value_fn=_as_int),
    PhilipsAirSensorDescription(key="aqit", name="Air Quality Type", state_class=None, value_fn=_as_int),
    PhilipsAirSensorDescription(key="ddp", name="Preferred Display", state_class=None),
    PhilipsAirSensorDescription(key="rddp", name="Reported Display", state_class=None),
    PhilipsAirSensorDescription(
        key="dtrs",
        name="Timer Remaining",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=_timer_remaining_minutes,
    ),
    PhilipsAirSensorDescription(
        key="wl",
        name="Water Level",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=_as_int,
    ),
    PhilipsAirSensorDescription(
        key="fltsts0",
        name="Pre-filter Life",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=_filter_percent(360),
    ),
    PhilipsAirSensorDescription(
        key="fltsts1",
        name="HEPA Filter Life",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=_filter_percent(4800),
    ),
    PhilipsAirSensorDescription(
        key="fltsts2",
        name="Carbon Filter Life",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=_filter_percent(4800),
    ),
    PhilipsAirSensorDescription(
        key="wicksts",
        name="Wick Filter Life",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=_filter_percent(4800),
    ),
    PhilipsAirSensorDescription(
        key="err",
        name="Error Code",
        state_class=None,
        value_fn=_as_int,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Philips Air sensors."""
    coordinator: PhilipsAirDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PhilipsAirSensor(coordinator, description) for description in SENSORS])


class PhilipsAirSensor(PhilipsAirEntity, SensorEntity):
    """Philips Air sensor."""

    def __init__(
        self,
        coordinator: PhilipsAirDataCoordinator,
        description: PhilipsAirSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{coordinator.host}_{description.key}"

    @property
    def available(self) -> bool:
        source_key = self.entity_description.source_key or self.entity_description.key
        return super().available and source_key in self.data

    @property
    def native_value(self) -> Any:
        source_key = self.entity_description.source_key or self.entity_description.key
        value = self.data.get(source_key)
        if self.entity_description.value_fn is not None:
            return self.entity_description.value_fn(value)
        return value
