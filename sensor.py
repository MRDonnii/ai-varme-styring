"""Sensor entities for AI Varme Styring."""

from __future__ import annotations

import re
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import AiVarmeBaseEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        AiVarmeStatusSensor(data["coordinator"], entry),
        AiVarmeIndicatorSensor(data["coordinator"], entry),
        AiVarmeHeatingModeSensor(data["coordinator"], entry),
        AiVarmeCheapestSourceSensor(data["coordinator"], entry),
        AiVarmeDailySavingsSensor(data["coordinator"], entry),
        AiVarmeMonthlySavingsSensor(data["coordinator"], entry),
        AiVarmeDeficitSensor(data["coordinator"], entry),
        AiVarmeColdRoomsSensor(data["coordinator"], entry),
        AiVarmeRadiatorHelpSensor(data["coordinator"], entry),
        AiVarmeFocusRoomSensor(data["coordinator"], entry),
        AiVarmeHouseLevelSensor(data["coordinator"], entry),
        AiVarmePidStatusSensor(data["coordinator"], entry),
        AiVarmeReportSensor(data["coordinator"], entry),
    ]
    cfg = {**entry.data, **entry.options}
    rooms = cfg.get("rooms", [])
    for room in rooms:
        room_name = str(room.get("room_name", "")).strip()
        if not room_name:
            continue
        entities.append(AiVarmeRoomTemperatureSensor(data["coordinator"], entry, room_name))
        entities.append(AiVarmeRoomStatusSensor(data["coordinator"], entry, room_name))
        entities.append(AiVarmeRoomTargetSensor(data["coordinator"], entry, room_name))
    async_add_entities(entities)


def _room_slug(room_name: str) -> str:
    normalized = room_name.lower()
    normalized = normalized.replace("æ", "ae").replace("ø", "oe").replace("å", "aa")
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return normalized or "rum"


class AiVarmeRoomBaseSensor(AiVarmeBaseEntity, SensorEntity):
    """Base room sensor shown as separate room device."""

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

    def _room_data(self) -> dict[str, Any]:
        rooms = (self.coordinator.data or {}).get("rooms", [])
        for room in rooms:
            if str(room.get("name", "")).strip().lower() == self._room_name.lower():
                return room
        return {}


class AiVarmeRoomStatusSensor(AiVarmeRoomBaseSensor):
    """Per-room status sensor."""

    _attr_icon = "mdi:home-thermometer"

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator, entry, room_name)
        self._attr_name = f"{room_name} status"
        self._attr_unique_id = f"{entry.entry_id}_room_{self._room_slug}_status"

    @property
    def native_value(self) -> str:
        room = self._room_data()
        if not room:
            return "Ukendt"
        if room.get("opening_active"):
            return "Pause pga. åbning"
        deficit = float(room.get("deficit", 0.0))
        surplus = float(room.get("surplus", 0.0))
        if deficit > 0:
            return "Varmebehov"
        if surplus > 0:
            return "Over mål"
        return "Stabil"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        room = self._room_data()
        if not room:
            return {}
        return {
            "temperatur": room.get("temperature"),
            "temperatur_raw": room.get("temperature_raw"),
            "ai_mål": room.get("target"),
            "eco_mål": room.get("eco_target"),
            "eco_away_minutter": room.get("presence_away_min"),
            "eco_return_minutter": room.get("presence_return_min"),
            "underskud": room.get("deficit"),
            "overskud": room.get("surplus"),
            "varmekilde_nu": room.get("active_heat_summary"),
            "varmekilder_aktive": room.get("active_heat_names", []),
            "varmekilder_entity_id": room.get("active_heat_entities", []),
            "leverer_varme_nu": room.get("is_heating_now", False),
            "styrende_enheder": room.get("control_entities", []),
            "ai_rumstyring_aktiv": room.get("room_enabled", True),
            "boost_aktiv": room.get("boost_active", False),
            "boost_delta_c": room.get("boost_delta_c"),
            "boost_varighed_min": room.get("boost_duration_min"),
            "boost_indtil": room.get("boost_until"),
            "åbning_aktiv": room.get("opening_active"),
            "presence_aktiv": room.get("occupancy_active"),
            "presence_eco_tilladt": room.get("presence_eco_enabled", False),
            "learning_tilladt": room.get("learning_enabled", False),
            "vinduespause_tilladt": room.get("opening_pause_enabled", True),
            "eco_aktiv": room.get("eco_active"),
            "varmepumpe": room.get("heat_pump"),
            "radiatorer": room.get("radiators", []),
        }


class AiVarmeRoomTemperatureSensor(AiVarmeRoomBaseSensor):
    """Per-room temperature mirror sensor."""

    _attr_icon = "mdi:thermometer"
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator, entry, room_name)
        self._attr_name = f"{room_name} temperatur"
        self._attr_unique_id = f"{entry.entry_id}_room_{self._room_slug}_temperature"

    @property
    def native_value(self) -> float | None:
        room = self._room_data()
        value = room.get("temperature")
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class AiVarmeRoomTargetSensor(AiVarmeRoomBaseSensor):
    """Per-room AI target mirror sensor."""

    _attr_icon = "mdi:target"
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator, entry, room_name)
        self._attr_name = f"{room_name} AI-mål"
        self._attr_unique_id = f"{entry.entry_id}_room_{self._room_slug}_ai_target"

    @property
    def native_value(self) -> float | None:
        room = self._room_data()
        target = room.get("target")
        if target is None:
            return None
        try:
            return float(target)
        except (TypeError, ValueError):
            return None


class AiVarmeStatusSensor(AiVarmeBaseEntity, SensorEntity):
    """High-level status text."""

    _attr_name = "AI Status"
    _attr_icon = "mdi:information-outline"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_status"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        if not data.get("enabled", False):
            return "Deaktiveret"
        if data.get("legacy_conflicts"):
            return "Konflikt med legacy automations"
        if data.get("provider_error_state", False):
            return "AI-provider fejl"
        if data.get("sensor_error", False):
            return "Sensorfejl"
        if data.get("thermostat_handover", False):
            return "Thermostat takeover"
        if data.get("opening_active", False):
            return "Pause pga. åbning"
        if data.get("presence_eco_active", False):
            return "Eco aktiv"
        if data.get("flow_limited", False):
            return "Flow begrænset"
        return "Aktiv"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "opdateret": data.get("updated_at"),
            "handlinger": data.get("actions", []),
            "rum": data.get("rooms", []),
            "utilgængelige_sensorer": data.get("unavailable_sensors"),
            "presence_eco_aktiveret": data.get("presence_eco_enabled"),
            "presence_eco_sidst_skiftet": data.get("presence_eco_last_changed"),
            "pid_aktiveret": data.get("pid_enabled"),
            "pid_sidst_skiftet": data.get("pid_last_changed"),
            "learning_aktiveret": data.get("learning_enabled"),
            "learning_sidst_skiftet": data.get("learning_last_changed"),
            "sensor_error": data.get("sensor_error", False),
            "ai_confidence": data.get("ai_confidence"),
            "confidence_threshold": data.get("confidence_threshold"),
            "legacy_conflicts": data.get("legacy_conflicts", []),
            "provider_error_state": data.get("provider_error_state", False),
            "thermostat_handover": data.get("thermostat_handover", False),
            "sidste_styringsaktivitet": data.get("last_control_activity"),
            "ai_factor": data.get("ai_factor"),
            "ai_reason": data.get("ai_reason"),
            "estimeret_besparelse_kwh": data.get("estimated_savings_per_kwh"),
            "estimeret_dagsbesparelse": data.get("estimated_daily_savings"),
        }


class AiVarmeIndicatorSensor(AiVarmeBaseEntity, SensorEntity):
    """Compact global AI indicator for cards/chips."""

    _attr_name = "AI indikator"
    _attr_icon = "mdi:robot-outline"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_ai_indicator"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        if not data.get("enabled", False):
            return "Inaktiv"
        if data.get("legacy_conflicts"):
            return "Ikke synk"
        if not data.get("ai_provider_ready", False) or data.get("provider_error_state", False):
            return "Fejl"
        return "Aktiv"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "enabled": data.get("enabled", False),
            "ai_provider_ready": data.get("ai_provider_ready", False),
            "provider_error_state": data.get("provider_error_state", False),
            "legacy_conflicts": data.get("legacy_conflicts", []),
        }


class AiVarmeHeatingModeSensor(AiVarmeBaseEntity, SensorEntity):
    """Global active heating mode: AC / Gas / Mix / Klar."""

    _attr_name = "Varmekilde mode"
    _attr_icon = "mdi:hvac"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_heating_mode"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        rooms = data.get("rooms", [])
        hp_active = False
        rad_active = False
        for room in rooms:
            active = set(room.get("active_heat_entities", []) or [])
            heat_pump = room.get("heat_pump")
            radiators = set(room.get("radiators", []) or [])
            if heat_pump and heat_pump in active:
                hp_active = True
            if radiators.intersection(active):
                rad_active = True
        if hp_active and rad_active:
            return "Mix"
        if hp_active:
            return "AC"
        if rad_active:
            return "Gas"
        return "Klar"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        rooms = data.get("rooms", [])
        hp_rooms: list[str] = []
        rad_rooms: list[str] = []
        for room in rooms:
            name = str(room.get("name", "")).strip()
            active = set(room.get("active_heat_entities", []) or [])
            heat_pump = room.get("heat_pump")
            radiators = set(room.get("radiators", []) or [])
            if name and heat_pump and heat_pump in active:
                hp_rooms.append(name)
            if name and radiators.intersection(active):
                rad_rooms.append(name)
        return {
            "ac_aktive_rum": hp_rooms,
            "gas_aktive_rum": rad_rooms,
            "thermostat_handover": data.get("thermostat_handover", False),
            "flow_limited": data.get("flow_limited", False),
            "enabled": data.get("enabled", False),
        }


class AiVarmeCheapestSourceSensor(AiVarmeBaseEntity, SensorEntity):
    """Cheapest source estimate."""

    _attr_name = "Billigste varmekilde"
    _attr_icon = "mdi:cash"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_cheapest"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        return "Varmepumpe" if data.get("heat_pump_cheaper", False) else "Radiator/Gas"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "elpris": data.get("el_price"),
            "gaspris": data.get("gas_price"),
            "fjernvarmepris": data.get("district_heat_price"),
            "prisbevidst": data.get("price_awareness"),
            "estimeret_besparelse_kwh": data.get("estimated_savings_per_kwh"),
        }


class AiVarmeDailySavingsSensor(AiVarmeBaseEntity, SensorEntity):
    """Estimated daily savings."""

    _attr_name = "Estimeret dagsbesparelse"
    _attr_icon = "mdi:cash-clock"
    _attr_native_unit_of_measurement = "kr"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_estimated_daily_savings"

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        value = data.get("estimated_daily_savings")
        if value is None:
            return None
        return float(value)


class AiVarmeMonthlySavingsSensor(AiVarmeBaseEntity, SensorEntity):
    """Estimated monthly savings."""

    _attr_name = "Estimeret månedsbesparelse"
    _attr_icon = "mdi:cash-multiple"
    _attr_native_unit_of_measurement = "kr"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_estimated_monthly_savings"

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        value = data.get("estimated_monthly_savings")
        if value is None:
            return None
        return float(value)


class AiVarmeDeficitSensor(AiVarmeBaseEntity, SensorEntity):
    """Largest current deficit."""

    _attr_name = "Største underskud"
    _attr_icon = "mdi:thermometer-chevron-up"
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_max_deficit"

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        return data.get("max_deficit")


class AiVarmeColdRoomsSensor(AiVarmeBaseEntity, SensorEntity):
    """Count of cold rooms."""

    _attr_name = "Kolde rum"
    _attr_icon = "mdi:home-thermometer-outline"
    _attr_native_unit_of_measurement = "rum"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_cold_rooms"

    @property
    def native_value(self) -> int:
        data = self.coordinator.data or {}
        return int(data.get("cold_rooms_count", 0))


class AiVarmeRadiatorHelpSensor(AiVarmeBaseEntity, SensorEntity):
    """Count rooms where radiator is heating."""

    _attr_name = "Radiatorhjælp rum"
    _attr_icon = "mdi:radiator"
    _attr_native_unit_of_measurement = "rum"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_radiator_help"

    @property
    def native_value(self) -> int:
        data = self.coordinator.data or {}
        return int(data.get("radiator_help_count", 0))


class AiVarmeFocusRoomSensor(AiVarmeBaseEntity, SensorEntity):
    """Current focus room for heating."""

    _attr_name = "Fokusrum"
    _attr_icon = "mdi:crosshairs-gps"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_focus_room"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        return str(data.get("focus_room", "Ingen"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "delta_c": data.get("focus_room_delta", 0.0),
            "ekstra_rum": data.get("extra_room", "Ingen"),
        }


class AiVarmeHouseLevelSensor(AiVarmeBaseEntity, SensorEntity):
    """Overall house heating level."""

    _attr_name = "Husniveau"
    _attr_icon = "mdi:home-analytics"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_house_level"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        return str(data.get("house_level", "Ukendt"))


class AiVarmeReportSensor(AiVarmeBaseEntity, SensorEntity):
    """AI report sensor."""

    _attr_name = "AI Rapport"
    _attr_icon = "mdi:file-document-outline"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_report"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        report = data.get("report", {})
        return report.get("short", "Afventer data")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        report = data.get("report", {})
        short_text = report.get("short", "Afventer data")
        long_text = report.get("long", "Afventer data")
        bullets = report.get("bullets", [])
        return {
            # Keep both legacy Danish keys and canonical short/long keys,
            # so dashboard cards can render regardless of which keyset they use.
            "short": short_text,
            "long": long_text,
            "omhandler": long_text,
            "punkter": bullets,
            "ai_provider": data.get("ai_provider"),
            "ai_model_fast": data.get("ai_model_fast"),
            "ai_model_report": data.get("ai_model_report"),
            "ai_provider_ready": data.get("ai_provider_ready"),
            "ai_confidence": data.get("ai_confidence"),
            "gasforbrug": data.get("gas_consumption"),
            "fjernvarmeforbrug": data.get("district_heat_consumption"),
            "estimeret_besparelse_kwh": data.get("estimated_savings_per_kwh"),
            "estimeret_dagsbesparelse": data.get("estimated_daily_savings"),
            "opdateret": data.get("updated_at"),
        }


class AiVarmePidStatusSensor(AiVarmeBaseEntity, SensorEntity):
    """PID layer status and per-room monitor."""

    _attr_name = "PID-lag status"
    _attr_icon = "mdi:tune-variant"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_pid_status"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        return data.get("pid_status", "Inaktiv")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "aktiveret": data.get("pid_enabled", False),
            "sidst_skiftet": data.get("pid_last_changed"),
            "kp": data.get("pid_kp"),
            "ki": data.get("pid_ki"),
            "kd": data.get("pid_kd"),
            "deadband_c": data.get("pid_deadband_c"),
            "rum": data.get("pid_rooms", []),
        }
