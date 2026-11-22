"""Base entity for AI Varme Styring."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AiVarmeCoordinator


class AiVarmeBaseEntity(CoordinatorEntity[AiVarmeCoordinator], Entity):
    """Base class for entities in integration."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AiVarmeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Local",
            model="AI Varme Styring",
        )

