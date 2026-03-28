"""Sensor entities for AI Varme Styring."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import AiVarmeBaseEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AiVarmeStatusSensor(data["coordinator"], entry),
            AiVarmeCheapestSourceSensor(data["coordinator"], entry),
            AiVarmeDeficitSensor(data["coordinator"], entry),
            AiVarmePidStatusSensor(data["coordinator"], entry),
            AiVarmeReportSensor(data["coordinator"], entry),
        ]
    )


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
        if data.get("sensor_error", False):
            return "Sensorfejl"
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
            "legacy_conflicts": data.get("legacy_conflicts", []),
            "ai_factor": data.get("ai_factor"),
            "ai_reason": data.get("ai_reason"),
            "estimeret_besparelse_kwh": data.get("estimated_savings_per_kwh"),
            "estimeret_dagsbesparelse": data.get("estimated_daily_savings"),
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
        return {
            "omhandler": report.get("long", "Afventer data"),
            "punkter": report.get("bullets", []),
            "ai_provider": data.get("ai_provider"),
            "ai_model_fast": data.get("ai_model_fast"),
            "ai_model_report": data.get("ai_model_report"),
            "ai_provider_ready": data.get("ai_provider_ready"),
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
