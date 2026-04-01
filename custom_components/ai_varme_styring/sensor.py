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


def _num_or_zero(value: Any, decimals: int = 1) -> float:
    """Return numeric value, or 0.0 for missing/invalid input."""
    try:
        if value is None:
            return 0.0
        return round(float(value), decimals)
    except (TypeError, ValueError):
        return 0.0


def _openclaw_meta(data: dict[str, Any]) -> dict[str, Any]:
    meta = data.get("ai_openclaw_meta", {})
    return meta if isinstance(meta, dict) else {}


def _payload_summary(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    rooms = payload.get("rooms")
    summary: dict[str, Any] = {
        "keys": sorted(payload.keys()),
    }
    if isinstance(rooms, list):
        summary["room_count"] = len(rooms)
    runtime = payload.get("runtime")
    if isinstance(runtime, dict):
        summary["runtime_keys"] = sorted(runtime.keys())
    prices = payload.get("prices")
    if isinstance(prices, dict):
        summary["price_keys"] = sorted(prices.keys())
    return summary


def _display_engine(value: Any, default: str = "Ingen") -> str:
    text = str(value or "").strip()
    if not text or text.lower() == "none":
        return default
    return text


def _dedupe_lines(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for line in lines:
        clean = str(line or "").strip()
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(clean)
    return result


def _room_summary_from_state(room: dict[str, Any]) -> str:
    name = str(room.get("name", "Rum")).strip() or "Rum"
    try:
        temp = float(room.get("temperature"))
    except (TypeError, ValueError):
        temp = None
    try:
        target = float(room.get("target"))
    except (TypeError, ValueError):
        target = None
    try:
        deficit = float(room.get("deficit", 0.0))
    except (TypeError, ValueError):
        deficit = 0.0
    try:
        surplus = float(room.get("surplus", 0.0))
    except (TypeError, ValueError):
        surplus = 0.0
    try:
        humidity = float(room.get("humidity"))
    except (TypeError, ValueError):
        humidity = None

    heat_summary = str(room.get("active_heat_summary", "")).strip() or "ingen aktiv varmekilde"

    parts = [name]
    if temp is not None and target is not None:
        parts.append(f"{temp:.1f}°C mod mål {target:.1f}°C")
    if deficit > 0:
        parts.append(f"underskud {deficit:.1f}°C")
    elif surplus > 0:
        parts.append(f"overskud {surplus:.1f}°C")
    else:
        parts.append("tæt på mål")
    if humidity is not None:
        parts.append(f"fugt {humidity:.0f}%")
    parts.append(f"varme: {heat_summary}")
    return ", ".join(parts) + "."


def _filtered_report_points(data: dict[str, Any], report: dict[str, Any], bullets: list[Any]) -> list[str]:
    room_analyses_raw = report.get("room_analyses", [])
    room_analyses = room_analyses_raw if isinstance(room_analyses_raw, list) else []

    room_summaries: set[str] = set()
    room_names: set[str] = set()
    for item in room_analyses:
        if not isinstance(item, dict):
            continue
        summary = str(item.get("summary", "")).strip()
        if summary:
            room_summaries.add(summary.lower())
        name = str(item.get("name", "")).strip()
        if name:
            room_names.add(name.lower())

    for room in data.get("rooms", []) if isinstance(data.get("rooms"), list) else []:
        if not isinstance(room, dict):
            continue
        name = str(room.get("name", "")).strip()
        if name:
            room_names.add(name.lower())

    skip_prefixes = (
        "beslutningsmotor:",
        "ai-kilde nu:",
        "fallback-motor:",
        "rapportmotor:",
        "hurtig model:",
        "rapport model:",
        "provider klar:",
        "ai-faktor:",
        "ai-konfidens:",
        "billigste varmekilde",
        "billigste varmevalg:",
        "billigste alternativ",
        "estimeret besparelse:",
        "varmepumpe billigst:",
        "rumvurdering:",
        "alle rum er tæt på måltemperatur.",
        "ingen rum har underskud",
    )

    filtered_points: list[str] = []
    for item in bullets if isinstance(bullets, list) else []:
        clean = str(item or "").strip()
        if not clean:
            continue
        if clean.startswith("- "):
            continue
        lowered = clean.lower()
        if lowered in room_summaries:
            continue
        if lowered.startswith(skip_prefixes):
            continue
        if any(lowered.startswith(f"{name}:") for name in room_names):
            continue
        filtered_points.append(clean)
    return _dedupe_lines(filtered_points)


def _format_report_long(
    data: dict[str, Any],
    report: dict[str, Any],
    short_text: str,
    bullets: list[Any],
    fallback_display: str,
    report_engine_display: str,
) -> str:
    long_text = str(report.get("long", "Afventer data") or "Afventer data").strip()
    if report_engine_display != "OpenClaw":
        return long_text

    room_analyses_raw = report.get("room_analyses", [])
    room_analyses = room_analyses_raw if isinstance(room_analyses_raw, list) else []

    short_clean = str(short_text or "").strip()
    if any(label in short_clean.lower() for label in ("beslutningsmotor:", "ai-kilde nu:", "fallback-motor:", "rapportmotor:")):
        short_clean = ""

    top_lines = _dedupe_lines(
        [
            short_clean,
            f"Beslutningsmotor: {_display_engine(data.get('ai_primary_engine_display'), 'Ukendt')}",
            f"AI-kilde nu: {_display_engine(data.get('ai_decision_source_display'), 'Ukendt')}",
            f"Fallback-motor: {fallback_display}",
            f"Rapportmotor: {report_engine_display}",
            (
                f"OpenClaw model: {data.get('openclaw_model_preferred')}"
                if data.get("openclaw_model_preferred")
                else ""
            ),
            (
                f"OpenClaw fallback: {data.get('openclaw_model_fallback')}"
                if data.get("openclaw_model_fallback")
                else ""
            ),
            (
                f"OpenClaw aktiv model: {(_openclaw_meta(data).get('actual_model') or data.get('openclaw_model_preferred'))}"
                if (data.get("openclaw_model_preferred") or _openclaw_meta(data).get("actual_model"))
                else ""
            ),
            (
                f"AI-faktor: {_num_or_zero(data.get('ai_factor'), 2)}"
                if data.get("ai_factor") is not None
                else ""
            ),
            (
                f"AI-konfidens: {_num_or_zero(data.get('ai_confidence'), 1)}%"
                if data.get("ai_confidence") is not None
                else ""
            ),
            (
                f"Billigste varmevalg: {data.get('cheapest_heat_source')}"
                if data.get("cheapest_heat_source")
                else ""
            ),
            (
                f"Billigste alternativ til varmepumpe: {data.get('cheapest_alt_name')}"
                if data.get("cheapest_alt_name")
                else ""
            ),
        ]
    )

    room_lines: list[str] = []
    room_summaries: set[str] = set()
    for item in room_analyses:
        if not isinstance(item, dict):
            continue
        summary = str(item.get("summary", "")).strip()
        recommendation = str(item.get("recommendation", "")).strip()
        if summary:
            line = summary
            if recommendation and recommendation.lower() not in summary.lower():
                line += f" Anbefaling: {recommendation}"
            room_lines.append(f"- {line}")
            room_summaries.add(summary.lower())

    if not room_lines:
        for room in data.get("rooms", []) if isinstance(data.get("rooms"), list) else []:
            if not isinstance(room, dict):
                continue
            summary = _room_summary_from_state(room)
            room_lines.append(f"- {summary}")
            room_summaries.add(summary.lower())

    point_lines = [f"- {line}" for line in _filtered_report_points(data, report, bullets)]

    sections: list[str] = []
    if top_lines:
        sections.append("Kort resume\n" + "\n".join(top_lines))
    if room_lines:
        sections.append("Rum\n" + "\n".join(room_lines))
    if point_lines:
        sections.append("Punkter\n" + "\n".join(point_lines))

    return "\n\n".join(section for section in sections if section).strip() or long_text


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        AiVarmeStatusSensor(data["coordinator"], entry),
        AiVarmeIndicatorSensor(data["coordinator"], entry),
        AiVarmeDecisionSourceSensor(data["coordinator"], entry),
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
        AiVarmeYesterdaySummarySensor(data["coordinator"], entry),
        AiVarmeWeekSummarySensor(data["coordinator"], entry),
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
        wanted_name = str(self._room_name).strip().lower()
        wanted_slug = self._room_slug

        for room in rooms:
            room_name = str(room.get("name", "")).strip()
            room_name_l = room_name.lower()
            room_slug = _room_slug(room_name)
            if room_name_l == wanted_name:
                return room
            if room_slug == wanted_slug:
                return room
            if room_slug.startswith(wanted_slug) or wanted_slug.startswith(room_slug):
                return room
            if room_name_l.startswith(wanted_name) or wanted_name.startswith(room_name_l):
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
            "presence_fallback_aktiv": room.get("occupancy_source_fallback", False),
            "presence_sidst_skiftet": room.get("occupancy_last_change"),
            "presence_sensorer_utilgængelige": room.get("occupancy_unavailable_sensors", []),
            "presence_eco_tilladt": room.get("presence_eco_enabled", False),
            "learning_tilladt": room.get("learning_enabled", False),
            "vinduespause_tilladt": room.get("opening_pause_enabled", True),
            "eco_aktiv": room.get("eco_active"),
            "varmepumpe": room.get("heat_pump"),
            "varmepumpe_effekt_sensor": room.get("heat_pump_power_sensor"),
            "varmepumpe_effekt_w": room.get("heat_pump_power_w"),
            "varmepumpe_intern_temp": room.get("heat_pump_internal_temp"),
            "varmepumpe_intern_bias_c": room.get("heat_pump_internal_bias_c"),
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
        meta = _openclaw_meta(data)
        rooms = data.get("rooms", [])
        actions = data.get("actions", [])
        unavailable = data.get("unavailable_sensors") or []
        room_names = [
            str(room.get("name", "")).strip()
            for room in rooms[:12]
            if isinstance(room, dict) and str(room.get("name", "")).strip()
        ]
        return {
            "opdateret": data.get("updated_at"),
            "handlinger_antal": len(actions) if isinstance(actions, list) else 0,
            "handlinger_preview": actions[:8] if isinstance(actions, list) else [],
            "rum_antal": len(rooms) if isinstance(rooms, list) else 0,
            "rum_navne": room_names,
            "utilgængelige_sensorer": unavailable,
            "utilgængelige_sensorer_antal": len(unavailable) if isinstance(unavailable, list) else 0,
            "presence_eco_aktiveret": data.get("presence_eco_enabled"),
            "presence_eco_sidst_skiftet": data.get("presence_eco_last_changed"),
            "ai_beslutningstype": data.get("ai_structured_decision", {}).get("global", {}).get("mode")
            if isinstance(data.get("ai_structured_decision"), dict)
            else None,
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
            "ai_primary_engine": data.get("ai_primary_engine"),
            "ai_primary_engine_display": data.get("ai_primary_engine_display"),
            "ai_decision_source": data.get("ai_decision_source"),
            "ai_decision_source_display": data.get("ai_decision_source_display"),
            "ai_fallback_count": data.get("ai_fallback_count", 0),
            "openclaw_enabled": data.get("openclaw_enabled", False),
            "openclaw_bridge_url": data.get("openclaw_bridge_url", ""),
            "openclaw_bridge_stats_updated": data.get("openclaw_bridge_stats_updated"),
            "openclaw_run_id": meta.get("openclaw_run_id"),
            "openclaw_request_id": meta.get("request_id"),
            "openclaw_latency_ms": meta.get("latency_ms"),
            "openclaw_model_requested": data.get("openclaw_model_preferred"),
            "openclaw_model_fallback": data.get("openclaw_model_fallback"),
            "openclaw_model_actual": meta.get("actual_model") or data.get("openclaw_model_preferred"),
            "estimeret_besparelse_kwh": _num_or_zero(data.get("estimated_savings_per_kwh"), 3),
            "estimeret_dagsbesparelse": _num_or_zero(data.get("estimated_daily_savings"), 2),
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
        meta = _openclaw_meta(data)
        bridge_stats = data.get("openclaw_bridge_stats", {}) or {}
        return {
            "enabled": data.get("enabled", False),
            "ai_provider_ready": data.get("ai_provider_ready", False),
            "ai_primary_engine": data.get("ai_primary_engine"),
            "ai_primary_engine_display": data.get("ai_primary_engine_display"),
            "provider_error_state": data.get("provider_error_state", False),
            "ai_decision_source": data.get("ai_decision_source"),
            "ai_decision_source_display": data.get("ai_decision_source_display"),
            "ai_fallback_count": data.get("ai_fallback_count", 0),
            "openclaw_bridge_stats_updated": data.get("openclaw_bridge_stats_updated"),
            "openclaw_ok": bridge_stats.get("openclaw_ok"),
            "openclaw_callback_ok": bridge_stats.get("openclaw_callback_ok"),
            "openclaw_callback_received": bridge_stats.get("openclaw_callback_received"),
            "openclaw_run_id": meta.get("openclaw_run_id"),
            "openclaw_request_id": meta.get("request_id"),
            "openclaw_latency_ms": meta.get("latency_ms"),
            "openclaw_model_requested": data.get("openclaw_model_preferred"),
            "openclaw_model_fallback": data.get("openclaw_model_fallback"),
            "openclaw_model_actual": meta.get("actual_model") or data.get("openclaw_model_preferred"),
            "legacy_conflicts": data.get("legacy_conflicts", []),
        }


class AiVarmeDecisionSourceSensor(AiVarmeBaseEntity, SensorEntity):
    """Current AI decision engine/source for dashboards and troubleshooting."""

    _attr_name = "AI beslutningsmotor"
    _attr_icon = "mdi:source-branch"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_ai_decision_source"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        return str(
            data.get("ai_decision_source_display")
            or data.get("ai_primary_engine_display")
            or data.get("ai_decision_source")
            or "Ukendt"
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        meta = _openclaw_meta(data)
        return {
            "ai_primary_engine": data.get("ai_primary_engine"),
            "ai_primary_engine_display": data.get("ai_primary_engine_display"),
            "ai_decision_source": data.get("ai_decision_source"),
            "ai_decision_source_display": data.get("ai_decision_source_display"),
            "ai_provider": data.get("ai_provider"),
            "ai_model_fast": data.get("ai_model_fast"),
            "ai_model_report": data.get("ai_model_report"),
            "ai_decision_payload_summary": _payload_summary(data.get("ai_decision_payload")),
            "ai_decision_payload_openclaw_summary": _payload_summary(
                data.get("ai_decision_payload_openclaw")
            ),
            "ai_decision_payload_provider_summary": _payload_summary(
                data.get("ai_decision_payload_provider")
            ),
            "openclaw_run_id": meta.get("openclaw_run_id"),
            "openclaw_request_id": meta.get("request_id"),
            "openclaw_callback_url": meta.get("callback_url"),
            "openclaw_latency_ms": meta.get("latency_ms"),
            "openclaw_response": meta.get("openclaw_response"),
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

    _attr_name = "Billigste varmevalg"
    _attr_icon = "mdi:cash"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_cheapest"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        if data.get("heat_pump_cheaper", False):
            return "Varmepumpe"
        alt = str(data.get("cheapest_alt_name") or "").strip()
        if alt:
            return alt
        return "Ukendt"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "elpris": _num_or_zero(data.get("el_price"), 3),
            "gaspris": _num_or_zero(data.get("gas_price"), 3),
            "fjernvarmepris": _num_or_zero(data.get("district_heat_price"), 3),
            "prisbevidst": data.get("price_awareness"),
            "varmepumpe_billigst": data.get("heat_pump_cheaper"),
            "billigste_alternativ": data.get("cheapest_alt_name"),
            "estimeret_besparelse_kwh": _num_or_zero(data.get("estimated_savings_per_kwh"), 3),
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
    def native_value(self) -> float:
        data = self.coordinator.data or {}
        value = data.get("estimated_daily_savings")
        return _num_or_zero(value, 2)


class AiVarmeMonthlySavingsSensor(AiVarmeBaseEntity, SensorEntity):
    """Estimated monthly savings."""

    _attr_name = "Estimeret månedsbesparelse"
    _attr_icon = "mdi:cash-multiple"
    _attr_native_unit_of_measurement = "kr"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_estimated_monthly_savings"

    @property
    def native_value(self) -> float:
        data = self.coordinator.data or {}
        value = data.get("estimated_monthly_savings")
        return _num_or_zero(value, 2)


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
        bullets = report.get("bullets", [])
        meta = _openclaw_meta(data)
        fallback_display = _display_engine(data.get("ai_fallback_engine_display"))
        report_engine_display = _display_engine(
            data.get("ai_report_engine_display") or data.get("last_report_model_used") or data.get("ai_model_fast"),
            default="Ukendt",
        )
        long_text = _format_report_long(
            data=data,
            report=report,
            short_text=short_text,
            bullets=bullets,
            fallback_display=fallback_display,
            report_engine_display=report_engine_display,
        )
        clean_points = _filtered_report_points(data, report, bullets)
        return {
            # Keep both legacy Danish keys and canonical short/long keys,
            # so dashboard cards can render regardless of which keyset they use.
            "short": short_text,
            "long": long_text,
            "omhandler": long_text,
            "punkter": clean_points,
            "punkter_raa": bullets,
            "rum_analyse": report.get("room_analyses", []),
            "beslutningsmotor": data.get("ai_primary_engine_display"),
            "fallbackmotor": fallback_display,
            "beslutningskilde": data.get("ai_decision_source_display"),
            "rapportmotor": report_engine_display,
            "rapportmotor_display": report_engine_display,
            "ai_provider": data.get("ai_provider"),
            "ai_primary_engine": data.get("ai_primary_engine"),
            "ai_primary_engine_display": data.get("ai_primary_engine_display"),
            "ai_decision_source": data.get("ai_decision_source"),
            "ai_decision_source_display": data.get("ai_decision_source_display"),
            "ai_openclaw_meta": data.get("ai_openclaw_meta", {}),
            "ai_decision_payload_summary": _payload_summary(data.get("ai_decision_payload")),
            "ai_decision_payload_openclaw_summary": _payload_summary(
                data.get("ai_decision_payload_openclaw")
            ),
            "ai_decision_payload_provider_summary": _payload_summary(
                data.get("ai_decision_payload_provider")
            ),
            "ai_report_payload_summary": _payload_summary(data.get("ai_report_payload")),
            "openclaw_run_id": meta.get("openclaw_run_id"),
            "openclaw_request_id": meta.get("request_id"),
            "openclaw_callback_url": meta.get("callback_url"),
            "openclaw_latency_ms": meta.get("latency_ms"),
            "ai_model_fast": data.get("ai_model_fast"),
            "ai_model_report": data.get("ai_model_report"),
            "openclaw_model_requested": data.get("openclaw_model_preferred"),
            "openclaw_model_fallback": data.get("openclaw_model_fallback"),
            "openclaw_model_actual": meta.get("actual_model") or data.get("openclaw_model_preferred"),
            "rapport_model_brugt": data.get("last_report_model_used"),
            "sidst_genereret": data.get("last_report_generated"),
            "sidst_rapport_kørt": data.get("last_report_generated"),
            "sidst_rapport_anmodet": data.get("manual_report_last_trigger"),
            "kort_footer": (
                f"Sidst kørt: {data.get('last_report_generated') or 'ukendt'} | "
                f"Beslutning: {data.get('ai_primary_engine_display') or 'ukendt'} | "
                f"Fallback: {fallback_display} | "
                f"Kilde: {data.get('ai_decision_source_display') or 'ukendt'}"
            ),
            "ai_beslutnings_interval_min": data.get("ai_decision_interval_min"),
            "ai_rapport_interval_min": data.get("ai_report_interval_min"),
            "ai_provider_ready": data.get("ai_provider_ready"),
            "ai_confidence": data.get("ai_confidence"),
            "elpris": _num_or_zero(data.get("el_price"), 3),
            "gaspris": _num_or_zero(data.get("gas_price"), 3),
            "fjernvarmepris": _num_or_zero(data.get("district_heat_price"), 3),
            "gasforbrug": _num_or_zero(data.get("gas_consumption"), 3),
            "fjernvarmeforbrug": _num_or_zero(data.get("district_heat_consumption"), 3),
            "estimeret_besparelse_kwh": _num_or_zero(data.get("estimated_savings_per_kwh"), 3),
            "estimeret_dagsbesparelse": _num_or_zero(data.get("estimated_daily_savings"), 2),
            "estimeret_månedsbesparelse": _num_or_zero(data.get("estimated_monthly_savings"), 2),
            "opdateret": data.get("updated_at"),
        }


class AiVarmeYesterdaySummarySensor(AiVarmeBaseEntity, SensorEntity):
    """Yesterday operational summary."""

    _attr_name = "Gårsdag rapport"
    _attr_icon = "mdi:calendar-today"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_summary_yesterday"

    @property
    def native_value(self) -> str:
        data = (self.coordinator.data or {}).get("summary_yesterday", {})
        hours = data.get("mode_hours", {})
        ac = float(hours.get("AC", 0.0))
        gas = float(hours.get("Gas", 0.0))
        mix = float(hours.get("Mix", 0.0))
        return f"AC {ac:.1f}h | Gas {gas:.1f}h | Mix {mix:.1f}h"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = (self.coordinator.data or {}).get("summary_yesterday", {})
        return {
            "mode_timer": data.get("mode_hours", {}),
            "gennemsnit_priser": data.get("avg_prices", {}),
            "forbrug": data.get("consumption", {}),
            "estimeret_kost": data.get("cost", {}),
            "samples": data.get("sample_count", 0),
            "opdateret": (self.coordinator.data or {}).get("updated_at"),
        }


class AiVarmeWeekSummarySensor(AiVarmeBaseEntity, SensorEntity):
    """Rolling 7-day operational summary."""

    _attr_name = "7 dage rapport"
    _attr_icon = "mdi:calendar-week"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_summary_week"

    @property
    def native_value(self) -> str:
        data = (self.coordinator.data or {}).get("summary_week", {})
        hours = data.get("mode_hours", {})
        ac = float(hours.get("AC", 0.0))
        gas = float(hours.get("Gas", 0.0))
        mix = float(hours.get("Mix", 0.0))
        return f"AC {ac:.1f}h | Gas {gas:.1f}h | Mix {mix:.1f}h"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = (self.coordinator.data or {}).get("summary_week", {})
        return {
            "mode_timer": data.get("mode_hours", {}),
            "gennemsnit_priser": data.get("avg_prices", {}),
            "forbrug": data.get("consumption", {}),
            "estimeret_kost": data.get("cost", {}),
            "samples": data.get("sample_count", 0),
            "opdateret": (self.coordinator.data or {}).get("updated_at"),
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
