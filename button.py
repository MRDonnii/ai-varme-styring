"""Button entities for AI Varme Styring."""

from __future__ import annotations

import re

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ROOM_NAME, CONF_ROOMS, DOMAIN
from .entity import AiVarmeBaseEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities: list[ButtonEntity] = [
        AiVarmeForceAiReviewButton(data["coordinator"], entry),
        AiVarmeForceReportButton(data["coordinator"], entry),
    ]
    cfg = {**entry.data, **entry.options}
    for room_cfg in cfg.get(CONF_ROOMS, []):
        room_name = str(room_cfg.get(CONF_ROOM_NAME, "")).strip()
        if room_name:
            entities.append(AiVarmeRoomBoostButton(data["coordinator"], entry, room_name))
    async_add_entities(entities)


def _room_slug(room_name: str) -> str:
    normalized = room_name.lower()
    normalized = normalized.replace("æ", "ae").replace("ø", "oe").replace("å", "aa")
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return normalized or "rum"


class AiVarmeForceAiReviewButton(AiVarmeBaseEntity, ButtonEntity):
    """Force fast AI decision pass now."""

    _attr_name = "Kør AI-gennemgang nu"
    _attr_icon = "mdi:brain"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_force_ai_review"

    async def async_press(self) -> None:
        await self.coordinator.async_trigger_ai_decision()

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        data = self.coordinator.data or {}
        return {"sidst_kørt": data.get("manual_ai_last_trigger")}


class AiVarmeForceReportButton(AiVarmeBaseEntity, ButtonEntity):
    """Force AI report generation now."""

    _attr_name = "Kør AI-rapport nu"
    _attr_icon = "mdi:file-document-edit-outline"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_force_ai_report"

    async def async_press(self) -> None:
        await self.coordinator.async_trigger_ai_report()

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        data = self.coordinator.data or {}
        return {"sidst_kørt": data.get("manual_report_last_trigger")}


class AiVarmeRoomBoostButton(AiVarmeBaseEntity, ButtonEntity):
    """Trigger room boost for faster warm-up."""

    _attr_icon = "mdi:rocket-launch-outline"

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator, entry)
        self._room_name = room_name
        self._room_slug = _room_slug(room_name)
        self._attr_name = f"{room_name} Boost nu"
        self._attr_unique_id = f"{entry.entry_id}_room_{self._room_slug}_boost_now"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_room_{self._room_slug}")},
            name=f"{entry.title} • {room_name}",
            manufacturer="Local",
            model="AI Varme Styring Rum",
            via_device=(DOMAIN, entry.entry_id),
        )

    async def async_press(self) -> None:
        room = self._room_data()
        delta_c = float(room.get("boost_delta_c", 1.0))
        duration_min = float(room.get("boost_duration_min", 60.0))
        await self.coordinator.async_trigger_room_boost(
            self._room_name,
            delta_c=delta_c,
            duration_min=duration_min,
        )

    def _room_data(self) -> dict:
        rooms = (self.coordinator.data or {}).get("rooms", [])
        for room in rooms:
            if str(room.get("name", "")).strip().lower() == self._room_name.lower():
                return room
        return {}
