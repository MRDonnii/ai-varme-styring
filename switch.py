"""Switch entities for AI Varme Styring."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    RUNTIME_ENABLED,
    RUNTIME_PID_LAYER_ENABLED,
    RUNTIME_PRESENCE_ECO_ENABLED,
)
from .entity import AiVarmeBaseEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AiVarmeEnabledSwitch(data["coordinator"], entry),
            AiVarmePresenceEcoSwitch(data["coordinator"], entry),
            AiVarmePidLayerSwitch(data["coordinator"], entry),
        ]
    )


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
