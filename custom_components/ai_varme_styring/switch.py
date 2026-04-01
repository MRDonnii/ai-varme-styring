"""Switch entities for AI Varme Styring."""

from __future__ import annotations

import re

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_ROOMS,
    CONF_ROOM_NAME,
    DOMAIN,
    RUNTIME_ENABLED,
    RUNTIME_LEARNING_ENABLED,
    RUNTIME_PID_LAYER_ENABLED,
    RUNTIME_PRESENCE_ECO_ENABLED,
)
from .entity import AiVarmeBaseEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities: list[SwitchEntity] = [
        AiVarmeEnabledSwitch(data["coordinator"], entry),
        AiVarmeAllRoomsEnabledSwitch(data["coordinator"], entry),
        AiVarmePresenceEcoSwitch(data["coordinator"], entry),
        AiVarmePidLayerSwitch(data["coordinator"], entry),
        AiVarmeLearningSwitch(data["coordinator"], entry),
    ]
    cfg = {**entry.data, **entry.options}
    for room_cfg in cfg.get(CONF_ROOMS, []):
        room_name = str(room_cfg.get(CONF_ROOM_NAME, "")).strip()
        if not room_name:
            continue
        entities.append(AiVarmeRoomEnabledSwitch(data["coordinator"], entry, room_name))
        entities.append(AiVarmeRoomPresenceEcoSwitch(data["coordinator"], entry, room_name))
        entities.append(AiVarmeRoomOpeningPauseSwitch(data["coordinator"], entry, room_name))
    async_add_entities(entities)


def _room_slug(room_name: str) -> str:
    normalized = room_name.lower()
    normalized = normalized.replace("æ", "ae").replace("ø", "oe").replace("å", "aa")
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return normalized or "rum"


class AiVarmeEnabledSwitch(AiVarmeBaseEntity, SwitchEntity, RestoreEntity):
    """Master switch for AI motor."""

    _attr_name = "Aktiv styring"
    _attr_icon = "mdi:heat-pump"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_enabled"
        self._attr_is_on = True

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._attr_is_on = bool(self.hass.data[DOMAIN][self.entry.entry_id].get(RUNTIME_ENABLED, True))
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_is_on = last_state.state == "on"
        self.hass.data[DOMAIN][self.entry.entry_id][RUNTIME_ENABLED] = self._attr_is_on

    async def async_turn_on(self, **kwargs) -> None:
        self._attr_is_on = True
        await self.coordinator.async_set_enabled(True)
        self.hass.data[DOMAIN][self.entry.entry_id][RUNTIME_ENABLED] = True
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        self._attr_is_on = False
        await self.coordinator.async_set_enabled(False)
        self.hass.data[DOMAIN][self.entry.entry_id][RUNTIME_ENABLED] = False
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        data = self.coordinator.data or {}
        return {
            "sidst_skiftet": data.get("enabled_last_changed"),
            "sidste_handling": (data.get("actions") or [None])[-1],
        }


class AiVarmePresenceEcoSwitch(AiVarmeBaseEntity, SwitchEntity, RestoreEntity):
    """Runtime switch for Presence-Eco."""

    _attr_name = "Presence-Eco aktiv"
    _attr_icon = "mdi:account-clock"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_presence_eco_enabled"
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._attr_is_on = bool(
            self.hass.data[DOMAIN][self.entry.entry_id].get(RUNTIME_PRESENCE_ECO_ENABLED, False)
        )
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_is_on = last_state.state == "on"
        self.hass.data[DOMAIN][self.entry.entry_id][RUNTIME_PRESENCE_ECO_ENABLED] = self._attr_is_on

    async def async_turn_on(self, **kwargs) -> None:
        self._attr_is_on = True
        await self.coordinator.async_set_presence_eco_enabled(True)
        self.hass.data[DOMAIN][self.entry.entry_id][RUNTIME_PRESENCE_ECO_ENABLED] = True
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        self._attr_is_on = False
        await self.coordinator.async_set_presence_eco_enabled(False)
        self.hass.data[DOMAIN][self.entry.entry_id][RUNTIME_PRESENCE_ECO_ENABLED] = False
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, str | bool | None]:
        data = self.coordinator.data or {}
        return {
            "sidst_skiftet": data.get("presence_eco_last_changed"),
            "eco_i_drift": data.get("presence_eco_active"),
        }


class AiVarmePidLayerSwitch(AiVarmeBaseEntity, SwitchEntity, RestoreEntity):
    """Runtime switch for PID layer."""

    _attr_name = "PID-lag aktiv"
    _attr_icon = "mdi:tune-variant"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_pid_enabled"
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._attr_is_on = bool(
            self.hass.data[DOMAIN][self.entry.entry_id].get(RUNTIME_PID_LAYER_ENABLED, False)
        )
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_is_on = last_state.state == "on"
        self.hass.data[DOMAIN][self.entry.entry_id][RUNTIME_PID_LAYER_ENABLED] = self._attr_is_on

    async def async_turn_on(self, **kwargs) -> None:
        self._attr_is_on = True
        await self.coordinator.async_set_pid_enabled(True)
        self.hass.data[DOMAIN][self.entry.entry_id][RUNTIME_PID_LAYER_ENABLED] = True
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        self._attr_is_on = False
        await self.coordinator.async_set_pid_enabled(False)
        self.hass.data[DOMAIN][self.entry.entry_id][RUNTIME_PID_LAYER_ENABLED] = False
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        data = self.coordinator.data or {}
        return {
            "sidst_skiftet": data.get("pid_last_changed"),
            "pid_status": data.get("pid_status"),
        }


class AiVarmeLearningSwitch(AiVarmeBaseEntity, SwitchEntity, RestoreEntity):
    """Runtime switch for learning mode."""

    _attr_name = "Learning mode aktiv"
    _attr_icon = "mdi:school"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_learning_enabled"
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._attr_is_on = bool(
            self.hass.data[DOMAIN][self.entry.entry_id].get(RUNTIME_LEARNING_ENABLED, False)
        )
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_is_on = last_state.state == "on"
        self.hass.data[DOMAIN][self.entry.entry_id][RUNTIME_LEARNING_ENABLED] = self._attr_is_on

    async def async_turn_on(self, **kwargs) -> None:
        self._attr_is_on = True
        await self.coordinator.async_set_learning_enabled(True)
        self.hass.data[DOMAIN][self.entry.entry_id][RUNTIME_LEARNING_ENABLED] = True
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        self._attr_is_on = False
        await self.coordinator.async_set_learning_enabled(False)
        self.hass.data[DOMAIN][self.entry.entry_id][RUNTIME_LEARNING_ENABLED] = False
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        data = self.coordinator.data or {}
        return {
            "sidst_skiftet": data.get("learning_last_changed"),
            "learning_status": data.get("learning_status"),
        }


class AiVarmeAllRoomsEnabledSwitch(AiVarmeBaseEntity, SwitchEntity):
    """Enable/disable AI room control for all configured rooms."""

    _attr_name = "AI rumstyring alle rum"
    _attr_icon = "mdi:home-group-plus"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_all_rooms_enabled"

    @property
    def is_on(self) -> bool:
        rooms = (self.coordinator.data or {}).get("rooms", [])
        if not rooms:
            return False
        return all(bool(room.get("room_enabled", True)) for room in rooms)

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_all_rooms_enabled(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_all_rooms_enabled(False)
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, int | list[str] | None]:
        rooms = (self.coordinator.data or {}).get("rooms", [])
        total = len(rooms)
        enabled_names = [str(r.get("name", "")).strip() for r in rooms if bool(r.get("room_enabled", True))]
        disabled_names = [
            str(r.get("name", "")).strip() for r in rooms if not bool(r.get("room_enabled", True))
        ]
        return {
            "rum_i_alt": total,
            "rum_aktive": len(enabled_names),
            "rum_deaktiverede": len(disabled_names),
            "deaktiverede_rum": [n for n in disabled_names if n],
            "sidst_skiftet": (self.coordinator.data or {}).get("all_rooms_enabled_last_changed"),
        }


class AiVarmeRoomSwitchBase(AiVarmeBaseEntity, SwitchEntity):
    """Base class for per-room switches."""

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator, entry)
        self._room_name = room_name
        self._room_slug = _room_slug(room_name)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_room_{self._room_slug}")},
            name=f"{entry.title} • {room_name}",
            manufacturer="Local",
            model="AI Varme Styring Rum",
            via_device=(DOMAIN, entry.entry_id),
        )

    def _room_data(self) -> dict:
        rooms = (self.coordinator.data or {}).get("rooms", [])
        for room in rooms:
            if str(room.get("name", "")).strip().lower() == self._room_name.lower():
                return room
        return {}


class AiVarmeRoomPresenceEcoSwitch(AiVarmeRoomSwitchBase):
    """Enable/disable auto eco by room."""

    _attr_icon = "mdi:leaf-circle-outline"

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator, entry, room_name)
        self._attr_name = f"{room_name} Auto-Eco"
        self._attr_unique_id = f"{entry.entry_id}_room_{self._room_slug}_auto_eco"

    @property
    def is_on(self) -> bool:
        return bool(self._room_data().get("presence_eco_enabled", False))

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_room_presence_eco_enabled(self._room_name, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_room_presence_eco_enabled(self._room_name, False)
        await self.coordinator.async_request_refresh()


class AiVarmeRoomEnabledSwitch(AiVarmeRoomSwitchBase):
    """Enable/disable AI control for a specific room."""

    _attr_icon = "mdi:home-cog-outline"

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator, entry, room_name)
        self._attr_name = f"{room_name} AI rumstyring"
        self._attr_unique_id = f"{entry.entry_id}_room_{self._room_slug}_enabled"

    @property
    def is_on(self) -> bool:
        return bool(self._room_data().get("room_enabled", True))

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_room_enabled(self._room_name, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_room_enabled(self._room_name, False)
        await self.coordinator.async_request_refresh()


class AiVarmeRoomOpeningPauseSwitch(AiVarmeRoomSwitchBase):
    """Enable/disable opening pause by room."""

    _attr_icon = "mdi:door-sliding-lock"

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator, entry, room_name)
        self._attr_name = f"{room_name} Vinduespause"
        self._attr_unique_id = f"{entry.entry_id}_room_{self._room_slug}_opening_pause"

    @property
    def is_on(self) -> bool:
        return bool(self._room_data().get("opening_pause_enabled", True))

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_room_opening_pause_enabled(self._room_name, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_room_opening_pause_enabled(self._room_name, False)
        await self.coordinator.async_request_refresh()
