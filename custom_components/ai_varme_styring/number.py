"""Number entities for AI Varme Styring."""

from __future__ import annotations

import re

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_ROOM_TARGET_STEP_C,
    CONF_ROOMS,
    CONF_ROOM_NAME,
    DEFAULT_AI_DECISION_INTERVAL_MIN,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_ECO_TARGET_C,
    DEFAULT_ROOM_SENSOR_BIAS_C,
    DEFAULT_ROOM_TARGET_STEP_C,
    DEFAULT_ROOM_PAUSE_AFTER_OPEN_MIN,
    DEFAULT_ROOM_RESUME_AFTER_CLOSED_MIN,
    DEFAULT_PID_DEADBAND_C,
    DEFAULT_PID_INTEGRAL_LIMIT,
    DEFAULT_PID_KD,
    DEFAULT_PID_KI,
    DEFAULT_PID_KP,
    DEFAULT_PID_OFFSET_MAX_C,
    DEFAULT_PRESENCE_AWAY_MIN,
    DEFAULT_PRESENCE_RETURN_MIN,
    DEFAULT_REVERT_TIMEOUT_MIN,
    DEFAULT_REPORT_INTERVAL_MIN,
    DOMAIN,
    RUNTIME_AI_DECISION_INTERVAL_MIN,
    RUNTIME_CONFIDENCE_THRESHOLD,
    RUNTIME_PID_DEADBAND_C,
    RUNTIME_PID_INTEGRAL_LIMIT,
    RUNTIME_PID_KD,
    RUNTIME_PID_KI,
    RUNTIME_PID_KP,
    RUNTIME_PID_OFFSET_MAX_C,
    RUNTIME_REPORT_INTERVAL_MIN,
    RUNTIME_REVERT_TIMEOUT_MIN,
)
from .entity import AiVarmeBaseEntity


def _room_target_step(entry: ConfigEntry) -> float:
    cfg = {**entry.data, **entry.options}
    raw = cfg.get(CONF_ROOM_TARGET_STEP_C, DEFAULT_ROOM_TARGET_STEP_C)
    try:
        step = float(raw)
    except (TypeError, ValueError):
        step = float(DEFAULT_ROOM_TARGET_STEP_C)
    return 1.0 if step >= 1.0 else 0.5


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities: list[NumberEntity] = [
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
            key=RUNTIME_AI_DECISION_INTERVAL_MIN,
            name="AI beslutnings-interval",
            unique_suffix="ai_decision_interval_min",
            icon="mdi:timer-cog-outline",
            default=DEFAULT_AI_DECISION_INTERVAL_MIN,
            min_value=1.0,
            max_value=30.0,
            step=1.0,
            unit="min",
        ),
        AiVarmeTargetNumber(
            data["coordinator"],
            entry,
            key=RUNTIME_REPORT_INTERVAL_MIN,
            name="AI rapport-interval",
            unique_suffix="ai_report_interval_min",
            icon="mdi:timer-edit-outline",
            default=DEFAULT_REPORT_INTERVAL_MIN,
            min_value=1.0,
            max_value=120.0,
            step=1.0,
            unit="min",
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
    cfg = {**entry.data, **entry.options}
    for room_cfg in cfg.get(CONF_ROOMS, []):
        room_name = str(room_cfg.get(CONF_ROOM_NAME, "")).strip()
        if not room_name:
            continue
        entities.append(
            AiVarmeRoomTargetControlNumber(
                data["coordinator"],
                entry,
                room_name=room_name,
            )
        )
        entities.append(
            AiVarmeRoomEcoTargetNumber(
                data["coordinator"],
                entry,
                room_name=room_name,
            )
        )
        entities.append(
            AiVarmeRoomSensorBiasNumber(
                data["coordinator"],
                entry,
                room_name=room_name,
            )
        )
        entities.append(
            AiVarmeRoomPresenceAwayNumber(
                data["coordinator"],
                entry,
                room_name=room_name,
            )
        )
        entities.append(
            AiVarmeRoomPresenceReturnNumber(
                data["coordinator"],
                entry,
                room_name=room_name,
            )
        )
        entities.append(
            AiVarmeRoomBoostDeltaNumber(
                data["coordinator"],
                entry,
                room_name=room_name,
            )
        )
        entities.append(
            AiVarmeRoomBoostDurationNumber(
                data["coordinator"],
                entry,
                room_name=room_name,
            )
        )
        entities.append(
            AiVarmeRoomPauseAfterOpenNumber(
                data["coordinator"],
                entry,
                room_name=room_name,
            )
        )
        entities.append(
            AiVarmeRoomResumeAfterClosedNumber(
                data["coordinator"],
                entry,
                room_name=room_name,
            )
        )
    async_add_entities(entities)


def _room_slug(room_name: str) -> str:
    normalized = room_name.lower()
    normalized = normalized.replace("æ", "ae").replace("ø", "oe").replace("å", "aa")
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return normalized or "rum"


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


class AiVarmeRoomTargetControlNumber(AiVarmeBaseEntity, NumberEntity):
    """Direct per-room AI target control."""

    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 10.0
    _attr_native_max_value = 30.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "°C"
    _attr_icon = "mdi:target"

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        *,
        room_name: str,
    ) -> None:
        super().__init__(coordinator, entry)
        self._room_name = room_name
        self._room_slug = _room_slug(room_name)
        self._attr_native_step = _room_target_step(entry)
        self._attr_name = f"{room_name} AI-mål (styring)"
        self._attr_unique_id = f"{entry.entry_id}_room_{self._room_slug}_target_control"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_room_{self._room_slug}")},
            name=f"{entry.title} • {room_name}",
            manufacturer="Local",
            model="AI Varme Styring Rum",
            via_device=(DOMAIN, entry.entry_id),
        )

    @property
    def native_value(self) -> float | None:
        room = self._room_data()
        target = room.get("target")
        if target is None:
            return None
        return float(target)

    @property
    def available(self) -> bool:
        return bool(self._room_data())

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        room = self._room_data()
        return {"mål_helper": str(room.get("target_number_entity", ""))}

    async def async_set_native_value(self, value: float) -> None:
        room = self._room_data()
        target_entity = room.get("target_number_entity")
        target = float(value)
        if target_entity:
            try:
                await self.hass.services.async_call(
                    "input_number",
                    "set_value",
                    {"entity_id": target_entity, "value": target},
                    blocking=True,
                    context=self._context,
                )
            except Exception:
                pass
        await self.coordinator.async_set_room_target_override(self._room_name, target)
        await self.coordinator.async_set_room_target_lock(self._room_name, target)
        self.async_write_ha_state()

    def _room_data(self) -> dict:
        rooms = (self.coordinator.data or {}).get("rooms", [])
        for room in rooms:
            if str(room.get("name", "")).strip().lower() == self._room_name.lower():
                return room
        return {}


class AiVarmeRoomRuntimeNumberBase(AiVarmeBaseEntity, NumberEntity):
    """Base runtime number bound to a room device."""

    _attr_mode = NumberMode.BOX

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


class AiVarmeRoomEcoTargetNumber(AiVarmeRoomRuntimeNumberBase):
    """Per-room eco target."""

    _attr_icon = "mdi:leaf"
    _attr_native_min_value = 10.0
    _attr_native_max_value = 30.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator, entry, room_name)
        self._attr_native_step = _room_target_step(entry)
        self._attr_name = f"{room_name} Eco-mål"
        self._attr_unique_id = f"{entry.entry_id}_room_{self._room_slug}_eco_target"

    @property
    def native_value(self) -> float:
        room = self._room_data()
        return float(room.get("eco_target", DEFAULT_ECO_TARGET_C))

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_room_eco_target(self._room_name, float(value))
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class AiVarmeRoomSensorBiasNumber(AiVarmeRoomRuntimeNumberBase):
    """Per-room temperature sensor calibration."""

    _attr_icon = "mdi:thermometer-chevron-up"
    _attr_native_min_value = -5.0
    _attr_native_max_value = 5.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator, entry, room_name)
        self._attr_name = f"{room_name} Temperatur kalibrering"
        self._attr_unique_id = f"{entry.entry_id}_room_{self._room_slug}_sensor_bias"

    @property
    def native_value(self) -> float:
        room = self._room_data()
        return float(room.get("sensor_bias_c", DEFAULT_ROOM_SENSOR_BIAS_C))

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_room_sensor_bias(self._room_name, float(value))
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class AiVarmeRoomPresenceAwayNumber(AiVarmeRoomRuntimeNumberBase):
    """Per-room away timer for eco activation."""

    _attr_icon = "mdi:timer-outline"
    _attr_native_min_value = 1.0
    _attr_native_max_value = 240.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "min"

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator, entry, room_name)
        self._attr_name = f"{room_name} Eco væk-tid"
        self._attr_unique_id = f"{entry.entry_id}_room_{self._room_slug}_presence_away_min"

    @property
    def native_value(self) -> float:
        room = self._room_data()
        return float(room.get("presence_away_min", DEFAULT_PRESENCE_AWAY_MIN))

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_room_presence_away_min(self._room_name, float(value))
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class AiVarmeRoomPresenceReturnNumber(AiVarmeRoomRuntimeNumberBase):
    """Per-room return timer for eco release."""

    _attr_icon = "mdi:timer-check-outline"
    _attr_native_min_value = 1.0
    _attr_native_max_value = 120.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "min"

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator, entry, room_name)
        self._attr_name = f"{room_name} Eco retur-tid"
        self._attr_unique_id = f"{entry.entry_id}_room_{self._room_slug}_presence_return_min"

    @property
    def native_value(self) -> float:
        room = self._room_data()
        return float(room.get("presence_return_min", DEFAULT_PRESENCE_RETURN_MIN))

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_room_presence_return_min(self._room_name, float(value))
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class AiVarmeRoomBoostDeltaNumber(AiVarmeRoomRuntimeNumberBase):
    """Per-room boost amount in °C."""

    _attr_icon = "mdi:thermometer-plus"
    _attr_native_min_value = 0.5
    _attr_native_max_value = 5.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator, entry, room_name)
        self._attr_name = f"{room_name} Boost temperatur"
        self._attr_unique_id = f"{entry.entry_id}_room_{self._room_slug}_boost_delta_c"

    @property
    def native_value(self) -> float:
        room = self._room_data()
        return float(room.get("boost_delta_c", 1.0))

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_room_boost_delta(self._room_name, float(value))
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class AiVarmeRoomBoostDurationNumber(AiVarmeRoomRuntimeNumberBase):
    """Per-room boost duration in minutes."""

    _attr_icon = "mdi:timer-sand"
    _attr_native_min_value = 5.0
    _attr_native_max_value = 240.0
    _attr_native_step = 5.0
    _attr_native_unit_of_measurement = "min"

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator, entry, room_name)
        self._attr_name = f"{room_name} Boost varighed"
        self._attr_unique_id = f"{entry.entry_id}_room_{self._room_slug}_boost_duration_min"

    @property
    def native_value(self) -> float:
        room = self._room_data()
        return float(room.get("boost_duration_min", 60.0))

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_room_boost_duration(self._room_name, float(value))
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class AiVarmeRoomPauseAfterOpenNumber(AiVarmeRoomRuntimeNumberBase):
    """Per-room minutes before AC pauses after opening/window event."""

    _attr_icon = "mdi:timer-pause-outline"
    _attr_native_min_value = 1.0
    _attr_native_max_value = 120.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "min"

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator, entry, room_name)
        self._attr_name = f"{room_name} Pause efter åbning"
        self._attr_unique_id = f"{entry.entry_id}_room_{self._room_slug}_pause_after_open_min"

    @property
    def native_value(self) -> float:
        room = self._room_data()
        return float(room.get("pause_after_open_min", DEFAULT_ROOM_PAUSE_AFTER_OPEN_MIN))

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_room_pause_after_open_min(self._room_name, float(value))
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class AiVarmeRoomResumeAfterClosedNumber(AiVarmeRoomRuntimeNumberBase):
    """Per-room minutes before AC resumes after all openings are closed."""

    _attr_icon = "mdi:timer-play-outline"
    _attr_native_min_value = 1.0
    _attr_native_max_value = 120.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "min"

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator, entry, room_name)
        self._attr_name = f"{room_name} Genstart efter lukning"
        self._attr_unique_id = f"{entry.entry_id}_room_{self._room_slug}_resume_after_closed_min"

    @property
    def native_value(self) -> float:
        room = self._room_data()
        return float(room.get("resume_after_closed_min", DEFAULT_ROOM_RESUME_AFTER_CLOSED_MIN))

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_room_resume_after_closed_min(self._room_name, float(value))
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
