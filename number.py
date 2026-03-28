"""Number entities for AI Varme Styring."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DEFAULT_ECO_TARGET_C,
    DEFAULT_GLOBAL_TARGET_C,
    DOMAIN,
    RUNTIME_ECO_TARGET,
    RUNTIME_GLOBAL_TARGET,
)
from .entity import AiVarmeBaseEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AiVarmeTargetNumber(
                data["coordinator"],
                entry,
                key=RUNTIME_GLOBAL_TARGET,
                name="Global AI-mål",
                unique_suffix="global_target",
                icon="mdi:thermometer",
                default=DEFAULT_GLOBAL_TARGET_C,
            ),
            AiVarmeTargetNumber(
                data["coordinator"],
                entry,
                key=RUNTIME_ECO_TARGET,
                name="Eco AI-mål",
                unique_suffix="eco_target",
                icon="mdi:leaf",
                default=DEFAULT_ECO_TARGET_C,
            ),
        ]
    )


class AiVarmeTargetNumber(AiVarmeBaseEntity, NumberEntity, RestoreEntity):
    """Runtime target number."""

    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 10.0
    _attr_native_max_value = 30.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "°C"

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        *,
        key: str,
        name: str,
        unique_suffix: str,
        icon: str,
        default: float,
    ) -> None:
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{unique_suffix}"
        self._attr_native_value = default

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            try:
                self._attr_native_value = float(last_state.state)
            except (TypeError, ValueError):
                pass
        self.hass.data[DOMAIN][self.entry.entry_id][self._key] = self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = float(value)
        self.hass.data[DOMAIN][self.entry.entry_id][self._key] = self._attr_native_value
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

