"""Shared entity helpers for Philips Air Purifier HTTP."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PhilipsAirDataCoordinator


class PhilipsAirEntity(CoordinatorEntity[PhilipsAirDataCoordinator]):
    """Base entity for Philips Air Purifier HTTP."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PhilipsAirDataCoordinator) -> None:
        super().__init__(coordinator)
        self._host = coordinator.host

    @property
    def data(self) -> dict[str, Any]:
        return self.coordinator.data or {}

    @property
    def device_info(self) -> DeviceInfo:
        model = self.data.get("modelid") or self.data.get("firmware_modelid")
        sw_version = self.data.get("swversion") or self.data.get("firmware_version")
        serial = self.data.get("DeviceId") or self._host
        return DeviceInfo(
            identifiers={(DOMAIN, self._host)},
            manufacturer="Philips",
            name=self.coordinator.name,
            model=model,
            sw_version=sw_version,
            serial_number=str(serial),
        )
