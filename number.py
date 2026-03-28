"""Number entities for AI Varme Styring."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_ECO_TARGET_C,
    DEFAULT_GLOBAL_TARGET_C,
    DEFAULT_PID_DEADBAND_C,
    DEFAULT_PID_INTEGRAL_LIMIT,
    DEFAULT_PID_KD,
    DEFAULT_PID_KI,
    DEFAULT_PID_KP,
    DEFAULT_PID_OFFSET_MAX_C,
    DEFAULT_PRESENCE_AWAY_MIN,
    DEFAULT_PRESENCE_RETURN_MIN,
    DEFAULT_REVERT_TIMEOUT_MIN,
    DOMAIN,
    RUNTIME_CONFIDENCE_THRESHOLD,
    RUNTIME_ECO_TARGET,
    RUNTIME_GLOBAL_TARGET,
    RUNTIME_PID_DEADBAND_C,
    RUNTIME_PID_INTEGRAL_LIMIT,
    RUNTIME_PID_KD,
    RUNTIME_PID_KI,
    RUNTIME_PID_KP,
    RUNTIME_PID_OFFSET_MAX_C,
    RUNTIME_PRESENCE_AWAY_MIN,
    RUNTIME_PRESENCE_RETURN_MIN,
    RUNTIME_REVERT_TIMEOUT_MIN,
)
from .entity import AiVarmeBaseEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities: list[AiVarmeTargetNumber] = [
        AiVarmeTargetNumber(
            data["coordinator"],
            entry,
            key=RUNTIME_GLOBAL_TARGET,
            name="Global AI-mål",
            unique_suffix="global_target",
            icon="mdi:thermometer",
            default=DEFAULT_GLOBAL_TARGET_C,
            min_value=10.0,
            max_value=30.0,
            step=0.1,
            unit="°C",
        ),
        AiVarmeTargetNumber(
            data["coordinator"],
            entry,
            key=RUNTIME_ECO_TARGET,
            name="Eco AI-mål",
            unique_suffix="eco_target",
            icon="mdi:leaf",
            default=DEFAULT_ECO_TARGET_C,
            min_value=10.0,
            max_value=30.0,
            step=0.1,
            unit="°C",
        ),
        AiVarmeTargetNumber(
            data["coordinator"],
            entry,
            key=RUNTIME_PRESENCE_AWAY_MIN,
            name="Presence away minutter",
            unique_suffix="presence_away_min",
            icon="mdi:timer-outline",
            default=DEFAULT_PRESENCE_AWAY_MIN,
            min_value=1.0,
            max_value=240.0,
            step=1.0,
            unit="min",
        ),
        AiVarmeTargetNumber(
            data["coordinator"],
            entry,
            key=RUNTIME_PRESENCE_RETURN_MIN,
            name="Presence return minutter",
            unique_suffix="presence_return_min",
            icon="mdi:timer-check-outline",
            default=DEFAULT_PRESENCE_RETURN_MIN,
            min_value=1.0,
            max_value=120.0,
            step=1.0,
            unit="min",
        ),
        AiVarmeTargetNumber(
            data["coordinator"],
            entry,
            key=RUNTIME_PID_KP,
            name="PID Kp",
            unique_suffix="pid_kp",
            icon="mdi:tune",
            default=DEFAULT_PID_KP,
            min_value=0.0,
            max_value=5.0,
            step=0.1,
            unit="",
        ),
        AiVarmeTargetNumber(
            data["coordinator"],
            entry,
            key=RUNTIME_PID_KI,
            name="PID Ki",
            unique_suffix="pid_ki",
            icon="mdi:tune",
            default=DEFAULT_PID_KI,
            min_value=0.0,
            max_value=1.0,
            step=0.01,
            unit="",
        ),
        AiVarmeTargetNumber(
            data["coordinator"],
            entry,
            key=RUNTIME_PID_KD,
            name="PID Kd",
            unique_suffix="pid_kd",
            icon="mdi:tune",
            default=DEFAULT_PID_KD,
            min_value=0.0,
            max_value=2.0,
            step=0.05,
            unit="",
        ),
        AiVarmeTargetNumber(
            data["coordinator"],
            entry,
            key=RUNTIME_PID_DEADBAND_C,
            name="PID deadband",
            unique_suffix="pid_deadband",
            icon="mdi:chart-bell-curve-cumulative",
            default=DEFAULT_PID_DEADBAND_C,
            min_value=0.0,
            max_value=1.0,
            step=0.05,
            unit="°C",
        ),
        AiVarmeTargetNumber(
            data["coordinator"],
            entry,
            key=RUNTIME_PID_INTEGRAL_LIMIT,
            name="PID integral limit",
            unique_suffix="pid_integral_limit",
            icon="mdi:math-integral",
            default=DEFAULT_PID_INTEGRAL_LIMIT,
            min_value=0.0,
            max_value=10.0,
            step=0.1,
            unit="",
        ),
        AiVarmeTargetNumber(
            data["coordinator"],
            entry,
            key=RUNTIME_PID_OFFSET_MAX_C,
            name="PID max offset",
            unique_suffix="pid_offset_max",
            icon="mdi:arrow-expand-vertical",
            default=DEFAULT_PID_OFFSET_MAX_C,
            min_value=0.0,
            max_value=3.0,
            step=0.1,
            unit="°C",
        ),
        AiVarmeTargetNumber(
            data["coordinator"],
            entry,
            key=RUNTIME_CONFIDENCE_THRESHOLD,
            name="AI confidence tærskel",
            unique_suffix="ai_confidence_threshold",
            icon="mdi:shield-check-outline",
            default=DEFAULT_CONFIDENCE_THRESHOLD,
            min_value=50.0,
            max_value=100.0,
            step=1.0,
            unit="%",
        ),
        AiVarmeTargetNumber(
            data["coordinator"],
            entry,
            key=RUNTIME_REVERT_TIMEOUT_MIN,
            name="AI revert timeout",
            unique_suffix="ai_revert_timeout",
            icon="mdi:history",
            default=DEFAULT_REVERT_TIMEOUT_MIN,
            min_value=5.0,
            max_value=180.0,
            step=1.0,
            unit="min",
        ),
    ]
    async_add_entities(entities)


class AiVarmeTargetNumber(AiVarmeBaseEntity, NumberEntity, RestoreEntity):
    """Runtime target number."""

    _attr_mode = NumberMode.BOX
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
        min_value: float,
        max_value: float,
        step: float,
        unit: str,
    ) -> None:
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{unique_suffix}"
        self._attr_native_value = default
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit or None

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
