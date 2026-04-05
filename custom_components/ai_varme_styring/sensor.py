"""Sensor entities for AI Varme Styring."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
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


def _safe_float(value: Any, default: float | None = None) -> float | None:
    """Return float value or default for missing/invalid input."""
    try:
        if value in (None, "", "unknown", "unavailable", "none", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _openclaw_meta(data: dict[str, Any]) -> dict[str, Any]:
    meta = data.get("ai_openclaw_meta", {})
    if not isinstance(meta, dict):
        return {}
    cleaned = dict(meta)
    response = cleaned.pop("openclaw_response", None)
    if isinstance(response, dict):
        cleaned["openclaw_response_summary"] = {
            "keys": sorted(response.keys()),
            "has_run_id": isinstance(response.get("runId"), str),
            "has_response": bool(response.get("response")),
            "has_output": bool(response.get("output")),
            "has_text": bool(response.get("text")),
            "has_message": bool(response.get("message")),
        }
    elif response is not None:
        cleaned["openclaw_response_summary"] = {
            "type": type(response).__name__,
            "preview": str(response)[:160],
        }
    return cleaned


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
    decision_lines = _current_decision_lines(_current_decision_snapshot(data))
    decision_section_lines = [f"- {line}" if not line.startswith("- ") else line for line in decision_lines]

    sections: list[str] = []
    if top_lines:
        sections.append("Kort resume\n" + "\n".join(top_lines))
    if room_lines:
        sections.append("Rum\n" + "\n".join(room_lines))
    if decision_section_lines:
        sections.append("Aktiv beslutning nu\n" + "\n".join(decision_section_lines))
    if point_lines:
        sections.append("Punkter\n" + "\n".join(point_lines))

    return "\n\n".join(section for section in sections if section).strip() or long_text




@lru_cache(maxsize=1)
def _integration_release_info() -> dict[str, str]:
    base = Path(__file__).resolve().parent
    version = "Ukendt"
    notes = "Ingen release notes fundet."
    try:
        manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
        version = str(manifest.get("version") or "Ukendt")
    except Exception:
        pass
    try:
        lines = (base / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
        capture: list[str] = []
        active = False
        for line in lines:
            if line.startswith("## "):
                if active:
                    break
                if line.strip().lower() == f"## v{version}".lower():
                    active = True
            if active:
                capture.append(line)
        if capture:
            notes = "\n".join(capture).strip()
    except Exception:
        pass
    return {"version": version, "notes": notes}

def _decision_block(data: dict[str, Any]) -> dict[str, Any]:
    decision = data.get("ai_structured_decision", {})
    return decision if isinstance(decision, dict) else {}


def _decision_context(data: dict[str, Any]) -> dict[str, Any]:
    ctx = _decision_block(data).get("context", {})
    return ctx if isinstance(ctx, dict) else {}


def _decision_diagnostics(data: dict[str, Any]) -> dict[str, Any]:
    diag = _decision_block(data).get("diagnostics", {})
    return diag if isinstance(diag, dict) else {}


def _list_text(values: Any) -> str:
    if not isinstance(values, list):
        return "Ingen"
    cleaned = [str(v).strip() for v in values if str(v).strip()]
    return ", ".join(cleaned) if cleaned else "Ingen"


def _bool_text(value: Any, *, unknown: str = "Ukendt") -> str:
    if isinstance(value, bool):
        return "Ja" if value else "Nej"
    return unknown


def _derived_room_names(data: dict[str, Any], predicate) -> list[str]:
    rooms = data.get("rooms", []) if isinstance(data.get("rooms"), list) else []
    names: list[str] = []
    for room in rooms:
        if not isinstance(room, dict):
            continue
        try:
            if predicate(room):
                name = str(room.get("name", "")).strip()
                if name:
                    names.append(name)
        except Exception:
            continue
    return names


def _report_fact_bundle(data: dict[str, Any]) -> dict[str, Any]:
    decision = _decision_block(data)
    context = _decision_context(data)
    diagnostics = _decision_diagnostics(data)
    global_block = decision.get("global", {}) if isinstance(decision.get("global"), dict) else {}
    rooms = decision.get("rooms", []) if isinstance(decision.get("rooms"), list) else []
    meta = _openclaw_meta(data)

    active_heating_rooms = diagnostics.get("active_heating_rooms")
    if not isinstance(active_heating_rooms, list) or not active_heating_rooms:
        active_heating_rooms = _derived_room_names(data, lambda room: bool(room.get("is_heating_now")))

    near_target_rooms = diagnostics.get("near_target_rooms")
    if not isinstance(near_target_rooms, list) or not near_target_rooms:
        near_target_rooms = _derived_room_names(
            data,
            lambda room: abs(float(room.get("deficit") or 0.0)) <= 0.05 and abs(float(room.get("surplus") or 0.0)) <= 0.25,
        )

    overshooting_rooms = diagnostics.get("overshooting_rooms")
    if not isinstance(overshooting_rooms, list) or not overshooting_rooms:
        overshooting_rooms = _derived_room_names(data, lambda room: float(room.get("surplus") or 0.0) > 0.05)

    action_rooms = diagnostics.get("action_rooms")
    if not isinstance(action_rooms, list) or not action_rooms:
        action_rooms = [str(r.get("name", "")).strip() for r in rooms if isinstance(r, dict) and str(r.get("name", "")).strip()]

    dry_rooms = diagnostics.get("dry_rooms")
    if not isinstance(dry_rooms, list) or not dry_rooms:
        dry_rooms = _derived_room_names(data, lambda room: str(room.get("comfort_band", "")).strip().lower() == "t\u00f8r")

    outside_temperature = context.get("outside_temperature")
    if outside_temperature is None:
        outside_temperature = data.get("outdoor_temp")

    heating_active = context.get("heating_active")
    if not isinstance(heating_active, bool):
        heating_active = any(bool(room.get("is_heating_now")) for room in data.get("rooms", []) if isinstance(room, dict))

    cheapest_source = context.get("cheapest_heat_source") or data.get("cheapest_heat_source")
    if not cheapest_source:
        cheapest_source = "Varmepumpe" if data.get("heat_pump_cheaper", False) else (data.get("cheapest_alt_name") or "Ukendt")

    flow_limited = context.get("flow_limited")
    if not isinstance(flow_limited, bool):
        flow_limited = data.get("flow_limited") if isinstance(data.get("flow_limited"), bool) else None

    request_id = decision.get("request_id") or meta.get("request_id")
    run_id = decision.get("run_id") or meta.get("openclaw_run_id")

    override_vurdering = diagnostics.get("override_reason") or diagnostics.get("no_change_reason") or "Ingen s\u00e6rskilt override-begrundelse"
    samlet_vurdering = diagnostics.get("summary") or decision.get("reason") or data.get("ai_reason") or "Ingen ekstra forklaring"

    fokusrum = diagnostics.get("focus_rooms")
    if isinstance(fokusrum, list) and fokusrum:
        fokusrum_text = _list_text(fokusrum)
    else:
        fokusrum_text = data.get("focus_room") or _list_text(action_rooms)
        if not fokusrum_text or fokusrum_text == "Ingen":
            fokusrum_text = "Ingen"

    rum_beslutninger = []
    for room in rooms:
        if not isinstance(room, dict):
            continue
        name = str(room.get("name", "")).strip() or "Rum"
        mode = str(room.get("mode", "")).strip() or "-"
        target = room.get("target_temperature")
        target_text = f"{float(target):.1f}" if isinstance(target, (int, float)) else "-"
        reason = str(room.get("reason", "")).strip()
        line = f"{name} -> {mode} {target_text}"
        if reason:
            line += f" ({reason})"
        rum_beslutninger.append(line)

    return {
        "request_id": request_id or "Ukendt",
        "run_id": run_id or "Ukendt",
        "factor": data.get("ai_factor"),
        "confidence": data.get("ai_confidence"),
        "reason": decision.get("reason") or data.get("ai_reason") or "Ingen \u00e5rsag angivet",
        "mode": str(global_block.get("mode") or "Ukendt"),
        "boost": bool(global_block.get("boost", False)),
        "outside_temperature": outside_temperature,
        "heating_active": heating_active,
        "cheapest_heat_source": cheapest_source,
        "flow_limited": flow_limited,
        "last_decision_age_sec": context.get("last_decision_age_sec") if context.get("last_decision_age_sec") is not None else data.get("last_decision_age_sec"),
        "active_heating_rooms": active_heating_rooms,
        "near_target_rooms": near_target_rooms,
        "overshooting_rooms": overshooting_rooms,
        "action_rooms": action_rooms,
        "dry_rooms": dry_rooms,
        "samlet_vurdering": samlet_vurdering,
        "override_vurdering": override_vurdering,
        "fokusrum": fokusrum_text,
        "rum_beslutninger": rum_beslutninger,
        "updated_at": data.get("updated_at") or data.get("last_report_generated") or "Ukendt",
    }

def _current_decision_snapshot(data: dict[str, Any]) -> dict[str, Any]:
    structured = data.get("ai_structured_decision", {})
    decision = structured if isinstance(structured, dict) else {}
    global_block = decision.get("global", {})
    global_decision = global_block if isinstance(global_block, dict) else {}
    room_rows = decision.get("rooms", [])
    room_directives = room_rows if isinstance(room_rows, list) else []

    active_rooms: list[dict[str, Any]] = []
    for row in room_directives:
        if not isinstance(row, dict):
            continue
        if row.get("should_change") is False:
            continue
        room_name = str(row.get("name", "")).strip() or "Rum"
        active_rooms.append(
            {
                "name": room_name,
                "entity_id": str(row.get("entity_id", "")).strip(),
                "target_temperature": row.get("target_temperature"),
                "mode": str(row.get("mode", "")).strip(),
                "reason": str(row.get("reason", "")).strip(),
            }
        )

    source_display = _display_engine(data.get("ai_decision_source_display"), default="Ukendt")
    source_raw = str(data.get("ai_decision_source", "")).strip()
    prev_source_display = _display_engine(data.get("ai_prev_decision_source_display"), default="Ukendt")
    prev_source_raw = str(data.get("ai_prev_decision_source", "")).strip()
    decision_reason = str(data.get("ai_reason", "")).strip()
    prev_reason = str(data.get("ai_prev_reason", "")).strip()
    try:
        factor = float(data.get("ai_factor"))
    except (TypeError, ValueError):
        factor = None
    try:
        confidence = float(data.get("ai_confidence"))
    except (TypeError, ValueError):
        confidence = None
    try:
        prev_factor = float(data.get("ai_prev_factor"))
    except (TypeError, ValueError):
        prev_factor = None
    try:
        prev_confidence = float(data.get("ai_prev_confidence"))
    except (TypeError, ValueError):
        prev_confidence = None

    return {
        "from_source_display": prev_source_display,
        "from_source": prev_source_raw,
        "source_display": source_display,
        "source": source_raw,
        "transition": str(data.get("ai_decision_transition", "")).strip(),
        "from_factor": prev_factor,
        "from_confidence": prev_confidence,
        "from_reason": prev_reason,
        "factor": factor,
        "confidence": confidence,
        "reason": decision_reason,
        "global": {
            "mode": str(global_decision.get("mode", "")).strip(),
            "boost": bool(global_decision.get("boost", False)),
        },
        "room_decisions_count": len(active_rooms),
        "room_decisions": active_rooms,
    }


def _current_decision_lines(snapshot: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    transition = str(snapshot.get("transition", "")).strip()
    if transition:
        lines.append(f"Fra -> til: {transition}")
    else:
        from_src = str(snapshot.get("from_source_display", "")).strip()
        to_src = str(snapshot.get("source_display", "")).strip()
        if from_src or to_src:
            lines.append(f"Fra -> til: {from_src or 'Ukendt'} -> {to_src or 'Ukendt'}")

    source_display = str(snapshot.get("source_display", "")).strip()
    if source_display:
        lines.append(f"Kilde: {source_display}")

    from_factor = snapshot.get("from_factor")
    from_confidence = snapshot.get("from_confidence")
    if isinstance(from_factor, (int, float)) or isinstance(from_confidence, (int, float)):
        from_factor_text = f"{float(from_factor):.2f}" if isinstance(from_factor, (int, float)) else "ukendt"
        from_conf_text = f"{float(from_confidence):.1f}%" if isinstance(from_confidence, (int, float)) else "ukendt"
        lines.append(f"Fra faktor: {from_factor_text} | Fra konfidens: {from_conf_text}")

    factor = snapshot.get("factor")
    confidence = snapshot.get("confidence")
    if isinstance(factor, (int, float)) or isinstance(confidence, (int, float)):
        factor_text = f"{float(factor):.2f}" if isinstance(factor, (int, float)) else "ukendt"
        conf_text = f"{float(confidence):.1f}%" if isinstance(confidence, (int, float)) else "ukendt"
        lines.append(f"Faktor: {factor_text} | Konfidens: {conf_text}")

    reason = str(snapshot.get("reason", "")).strip()
    if reason:
        lines.append(f"Aarsag: {reason}")
    from_reason = str(snapshot.get("from_reason", "")).strip()
    if from_reason and from_reason.lower() != reason.lower():
        lines.append(f"Fra aarsag: {from_reason}")

    global_block = snapshot.get("global", {})
    if isinstance(global_block, dict):
        mode = str(global_block.get("mode", "")).strip()
        if mode:
            boost_txt = "on" if bool(global_block.get("boost", False)) else "off"
            lines.append(f"Global mode: {mode} | Boost: {boost_txt}")

    room_decisions = snapshot.get("room_decisions", [])
    if isinstance(room_decisions, list) and room_decisions:
        lines.append("Rum-overrides:")
        for row in room_decisions[:8]:
            if not isinstance(row, dict):
                continue
            room_name = str(row.get("name", "Rum")).strip() or "Rum"
            target = row.get("target_temperature")
            mode = str(row.get("mode", "")).strip()
            reason = str(row.get("reason", "")).strip()
            target_txt = f"{target}C" if isinstance(target, (int, float)) else "-"
            mode_txt = mode or "-"
            line = f"- {room_name}: target {target_txt}, mode {mode_txt}"
            if reason:
                line += f" ({reason})"
            lines.append(line)

    return _dedupe_lines(lines)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        AiVarmeFactorSensor(data["coordinator"], entry),
        AiVarmeConfidenceSensor(data["coordinator"], entry),
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


class AiVarmeFactorSensor(AiVarmeBaseEntity, SensorEntity):
    """Current AI factor as a dedicated sensor."""

    _attr_name = "AI faktor"
    _attr_icon = "mdi:tune-variant"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_ai_factor"

    @property
    def native_value(self) -> float:
        data = self.coordinator.data or {}
        value = data.get("ai_factor")
        if value is not None:
            return _num_or_zero(value, 2)
        mqtt_state = self.coordinator.hass.states.get("sensor.ai_varme_openclaw_decision")
        if mqtt_state is not None:
            return _num_or_zero(mqtt_state.state, 2)
        return 0.0


class AiVarmeConfidenceSensor(AiVarmeBaseEntity, SensorEntity):
    """Current AI confidence as a dedicated sensor."""

    _attr_name = "AI konfidens"
    _attr_icon = "mdi:percent"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_ai_confidence_value"

    @property
    def native_value(self) -> float:
        data = self.coordinator.data or {}
        value = data.get("ai_confidence")
        if value is not None:
            return _num_or_zero(value, 1)
        mqtt_state = self.coordinator.hass.states.get("sensor.ai_varme_openclaw_decision")
        if mqtt_state is not None:
            return _num_or_zero(mqtt_state.attributes.get("confidence"), 1)
        return 0.0


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
        deficit = _safe_float(room.get("deficit"), 0.0)
        surplus = _safe_float(room.get("surplus"), 0.0)
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
        comfort_mode_active = bool((self.coordinator.data or {}).get("comfort_mode_enabled", False))
        target_value = room.get("target")
        target_entity = str(room.get("target_number_entity", "") or "").strip()
        if target_entity:
            helper_state = self.hass.states.get(target_entity)
            if helper_state is not None:
                helper_target = _safe_float(helper_state.state)
                if helper_target is not None:
                    target_value = helper_target
        elif bool(room.get("boost_active", False)):
            base_target = _safe_float(room.get("target"))
            boost_delta = _safe_float(room.get("boost_delta_c"))
            if base_target is not None and boost_delta is not None:
                target_value = base_target - boost_delta
        deficit = _safe_float(room.get("deficit"), 0.0) or 0.0
        comfort_gap = _safe_float(room.get("comfort_gap"), 0.0) or 0.0
        comfort_band = str(room.get("comfort_band") or "").strip()
        humidity = _safe_float(room.get("humidity"))
        opening_active = bool(room.get("opening_active"))
        comfort_reason = "Komfortmode er slukket."
        heat_need_source = "temperatur"
        if comfort_mode_active:
            if opening_active:
                comfort_reason = "Komfort ignoreres midlertidigt, fordi rummet er sat på pause pga. åbning."
            elif comfort_gap > deficit + 0.05:
                heat_need_source = "komfort"
                if humidity is not None and comfort_band == "tør":
                    comfort_reason = f"Tør luft ({humidity:.0f}%) løfter det oplevede varmebehov lidt."
                elif humidity is not None and comfort_band == "fugtig":
                    comfort_reason = f"Høj fugt ({humidity:.0f}%) påvirker komforten og holder styringen mere forsigtig."
                else:
                    comfort_reason = "Oplevet komfort vejer lidt tungere end rå temperatur lige nu."
            elif humidity is not None and comfort_band in {"tør", "fugtig"}:
                comfort_reason = f"Fugt ({humidity:.0f}%) overvåges, men ændrer ikke varmebehovet lige nu."
            else:
                comfort_reason = "Komfortmode er aktiv, men rå temperatur er stadig det styrende signal."
        return {
            "temperatur": room.get("temperature"),
            "temperatur_raw": room.get("temperature_raw"),
            "ai_mål": target_value,
            "eco_mål": room.get("eco_target"),
            "komfort_mode_aktiv": comfort_mode_active,
            "komfort_target": room.get("comfort_target"),
            "komfort_offset_c": room.get("comfort_offset_c"),
            "komfort_gap": room.get("comfort_gap"),
            "effektivt_varmebehov": room.get("effective_gap"),
            "komfort_bånd": room.get("comfort_band"),
            "komfort_årsag": comfort_reason,
            "varmebehovskilde": heat_need_source,
            "fugt": room.get("humidity"),
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
        try:
            target_entity = str(room.get("target_number_entity", "") or "").strip()
            if target_entity:
                helper_state = self.hass.states.get(target_entity)
                if helper_state is not None:
                    helper_target = _safe_float(helper_state.state)
                    if helper_target is not None:
                        return float(helper_target)

            target = _safe_float(room.get("target"))
            if target is None:
                return None
            if bool(room.get("boost_active", False)):
                boost_delta = _safe_float(room.get("boost_delta_c"))
                if boost_delta is not None:
                    target -= boost_delta
            return float(target)
        except Exception:
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
            "komfort_mode_aktiv": data.get("comfort_mode_enabled", False),
            "komfort_mode_sidst_skiftet": data.get("comfort_mode_last_changed"),
            "komfort_mode_status": data.get("comfort_mode_status"),
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
            "ai_prev_decision_source": data.get("ai_prev_decision_source"),
            "ai_prev_decision_source_display": data.get("ai_prev_decision_source_display"),
            "ai_decision_transition": data.get("ai_decision_transition"),
            "ai_last_fallback_reason": data.get("ai_last_fallback_reason", ""),
            "ai_last_errors": data.get("ai_last_errors", {}),
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
            "ai_last_fallback_reason": data.get("ai_last_fallback_reason", ""),
            "ai_last_errors": data.get("ai_last_errors", {}),
            "ai_fallback_count": data.get("ai_fallback_count", 0),
            "openclaw_bridge_stats_updated": data.get("openclaw_bridge_stats_updated"),
            "openclaw_ok": bridge_stats.get("openclaw_ok"),
            "openclaw_callback_ok": bridge_stats.get("openclaw_callback_ok"),
            "openclaw_callback_received": bridge_stats.get("openclaw_callback_received"),
            "openclaw_run_id": meta.get("openclaw_run_id"),
            "openclaw_request_id": meta.get("request_id"),
            "openclaw_latency_ms": meta.get("latency_ms"),
            "openclaw_runtime_health": data.get("openclaw_runtime_health"),
            "openclaw_model_requested": data.get("openclaw_model_preferred"),
            "openclaw_model_fallback": data.get("openclaw_model_fallback"),
            "openclaw_model_actual": meta.get("actual_model") or data.get("openclaw_model_preferred"),
            "openclaw_runtime_status": data.get("openclaw_runtime_status", {}),
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
            "ai_last_fallback_reason": data.get("ai_last_fallback_reason", ""),
            "ai_last_errors": data.get("ai_last_errors", {}),
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
            "openclaw_response_summary": meta.get("openclaw_response_summary"),
            "openclaw_runtime_health": data.get("openclaw_runtime_health"),
            "openclaw_runtime_status": data.get("openclaw_runtime_status", {}),
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
        decision_snapshot = _current_decision_snapshot(data)
        decision_lines = _current_decision_lines(decision_snapshot)
        decision_transition = str(decision_snapshot.get("transition", "")).strip()
        if not decision_transition:
            decision_transition = (
                f"{decision_snapshot.get('from_source_display', 'Ukendt')} -> "
                f"{decision_snapshot.get('source_display', 'Ukendt')}"
            )
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
        release_info = _integration_release_info()
        facts = _report_fact_bundle(data)
        return {
            # Keep both legacy Danish keys and canonical short/long keys,
            # so dashboard cards can render regardless of which keyset they use.
            "short": short_text,
            "long": long_text,
            "omhandler": long_text,
            "punkter": clean_points,
            "punkter_raa": bullets,
            "rum_analyse": report.get("room_analyses", []),
            "release_version": release_info.get("version"),
            "release_notes": release_info.get("notes"),
            "release_notes_lines": release_info.get("notes", "").splitlines(),
            "release_title": f"Release {release_info.get('version')}",
            "tid": facts.get("updated_at"),
            "request_id": facts.get("request_id"),
            "run_id": facts.get("run_id"),
            "faktor": facts.get("factor"),
            "konfidens": facts.get("confidence"),
            "aarsag": facts.get("reason"),
            "årsag": facts.get("reason"),
            "samlet_vurdering": facts.get("samlet_vurdering"),
            "override_vurdering": facts.get("override_vurdering"),
            "fokusrum": facts.get("fokusrum"),
            "global_mode": facts.get("mode"),
            "global_boost": _bool_text(facts.get("boost"), unknown="Nej"),
            "udetemperatur": facts.get("outside_temperature"),
            "aktiv_varme": _bool_text(facts.get("heating_active")),
            "billigste_varmekilde": facts.get("cheapest_heat_source"),
            "flow_begraenset": _bool_text(facts.get("flow_limited")),
            "flow_begrænset": _bool_text(facts.get("flow_limited")),
            "sidste_beslutningsalder_sec": facts.get("last_decision_age_sec"),
            "sidste_beslutningsalder": facts.get("last_decision_age_sec"),
            "diagnostik_aktive_rum": _list_text(facts.get("active_heating_rooms")),
            "aktivt_opvarmede_rum": _list_text(facts.get("active_heating_rooms")),
            "diagnostik_taet_paa_maal": _list_text(facts.get("near_target_rooms")),
            "diagnostik_tæt_på_mål": _list_text(facts.get("near_target_rooms")),
            "rum_tæt_på_mål": _list_text(facts.get("near_target_rooms")),
            "diagnostik_over_maal": _list_text(facts.get("overshooting_rooms")),
            "over_målet": _list_text(facts.get("overshooting_rooms")),
            "diagnostik_naer_handling": _list_text(facts.get("action_rooms")),
            "diagnostik_nær_handling": _list_text(facts.get("action_rooms")),
            "rum_nær_handling": _list_text(facts.get("action_rooms")),
            "diagnostik_toerre_rum": _list_text(facts.get("dry_rooms")),
            "diagnostik_tørre_rum": _list_text(facts.get("dry_rooms")),
            "tørre_rum": _list_text(facts.get("dry_rooms")),
            "rum_beslutninger": facts.get("rum_beslutninger") or [],
            "rum_beslutninger_text": "\n".join(facts.get("rum_beslutninger") or []),
            "sidst_opdateret": facts.get("updated_at"),
            "beslutningsmotor": data.get("ai_primary_engine_display"),
            "fallbackmotor": fallback_display,
            "beslutningskilde": data.get("ai_decision_source_display"),
            "kilde": data.get("ai_decision_source_display"),
            "rapportmotor": report_engine_display,
            "rapportmotor_display": report_engine_display,
            "ai_provider": data.get("ai_provider"),
            "ai_primary_engine": data.get("ai_primary_engine"),
            "ai_primary_engine_display": data.get("ai_primary_engine_display"),
            "ai_decision_source": data.get("ai_decision_source"),
            "ai_decision_source_display": data.get("ai_decision_source_display"),
            "ai_prev_decision_source": data.get("ai_prev_decision_source"),
            "ai_prev_decision_source_display": data.get("ai_prev_decision_source_display"),
            "ai_decision_transition": decision_transition,
            "ai_last_fallback_reason": data.get("ai_last_fallback_reason", ""),
            "ai_last_errors": data.get("ai_last_errors", {}),
            "ai_openclaw_meta": meta,
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
            "ai_prev_factor": data.get("ai_prev_factor"),
            "ai_prev_confidence": data.get("ai_prev_confidence"),
            "ai_prev_reason": data.get("ai_prev_reason"),
            "aktiv_beslutning": decision_snapshot,
            "aktive_beslutninger_nu": decision_lines,
            "aktive_rum_beslutninger": decision_snapshot.get("room_decisions", []),
            "aktive_rum_beslutninger_antal": decision_snapshot.get("room_decisions_count", 0),
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
