"""Coordinator and AI motor for AI Varme Styring."""

from __future__ import annotations

import asyncio
import copy
import contextlib
from dataclasses import dataclass, field
from pathlib import Path
from datetime import timedelta
import json
import logging
import os
import re
import traceback
import uuid
from typing import Any

from homeassistant.components.climate.const import HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .ai_client import AiProviderClient
from .const import (
    AI_PRIMARY_ENGINE_OPENCLAW,
    AI_PRIMARY_ENGINE_PROVIDER,
    AI_PRIMARY_ENGINE_OPTIONS,
    AI_ENGINE_NONE,
    AI_PROVIDER_GEMINI,
    AI_PROVIDER_OLLAMA,
    CONF_AI_FALLBACK_ENGINE,
    CONF_AI_DECISION_INTERVAL_MIN,
    CONF_AI_PRIMARY_ENGINE,
    CONF_AI_MODEL_FAST,
    CONF_AI_MODEL_REPORT,
    CONF_AI_PROVIDER,
    CONF_AI_REPORT_ENGINE,
    CONF_CONFIDENCE_THRESHOLD,
    CONF_DECIMALS,
    CONF_DISTRICT_HEAT_CONSUMPTION_SENSOR,
    CONF_DISTRICT_HEAT_PRICE_SENSOR,
    CONF_ELECTRICITY_PRICE_SENSOR,
    CONF_ENABLE_PID_LAYER,
    CONF_ENABLE_LEARNING,
    CONF_ENABLE_PRESENCE_ECO,
    CONF_ENABLE_PRICE_AWARENESS,
    CONF_FLOW_LIMIT_MARGIN_C,
    CONF_GAS_PRICE_SENSOR,
    CONF_GAS_CONSUMPTION_SENSOR,
    CONF_GEMINI_API_KEY,
    CONF_GEMINI_MODEL_FAST,
    CONF_GEMINI_MODEL_REPORT,
    CONF_HUMIDITY_COMFORT_ENABLED,
    CONF_HUMIDITY_DRY_THRESHOLD,
    CONF_HUMIDITY_HUMID_THRESHOLD,
    CONF_HUMIDITY_MAX_OFFSET_C,
    CONF_HEAT_PUMP_CHEAP_PRIORITY_FACTOR,
    CONF_HEAT_PUMP_CHEAP_FAN_MODE,
    CONF_HEAT_SOURCE_DIRECTION_BIAS,
    CONF_CHEAP_POWER_RADIATOR_SETBACK_EXTRA_C,
    CONF_OLLAMA_HOST,
    CONF_OUTDOOR_TEMP_SENSOR,
    CONF_OPENCLAW_ENABLED,
    CONF_OPENCLAW_BRIDGE_URL,
    CONF_OPENCLAW_MODEL_FALLBACK,
    CONF_OPENCLAW_MODEL_PREFERRED,
    CONF_OPENCLAW_ONLY_MODE,
    CONF_OPENCLAW_PAYLOAD_PROFILE,
    CONF_OPENCLAW_TIMEOUT_SEC,
    CONF_OPENCLAW_TOKEN,
    CONF_OPENCLAW_PASSWORD,
    CONF_OPENCLAW_URL,
    CONF_PROVIDER_PAYLOAD_PROFILE,
    CONF_PID_DEADBAND_C,
    CONF_PID_INTEGRAL_LIMIT,
    CONF_PID_KD,
    CONF_PID_KI,
    CONF_PID_KP,
    CONF_PID_OFFSET_MAX_C,
    CONF_PRESENCE_AWAY_MIN,
    CONF_PRESENCE_RETURN_MIN,
    CONF_PRICE_MARGIN,
    CONF_RADIATOR_BOOST_C,
    CONF_RADIATOR_SETBACK_C,
    CONF_REPORT_INTERVAL_MIN,
    CONF_REVERT_TIMEOUT_MIN,
    CONF_ROOMS,
    CONF_ROOM_ANTI_SHORT_CYCLE_MIN,
    CONF_ROOM_HEAT_PUMP,
    CONF_ROOM_HUMIDITY_SENSOR,
    CONF_ROOM_HEAT_PUMP_POWER_SENSOR,
    CONF_ROOM_LINK_GROUP,
    CONF_ROOM_ADJACENT_ROOMS,
    CONF_ROOM_HEAT_SOURCE_DIRECTION_BIAS,
    CONF_ROOM_CHEAP_POWER_RADIATOR_SETBACK_EXTRA_C,
    CONF_ROOM_MASSIVE_OVERHEAT_C,
    CONF_ROOM_MASSIVE_OVERHEAT_MIN,
    CONF_ROOM_NAME,
    CONF_ROOM_OCCUPANCY_SENSORS,
    CONF_ROOM_ENABLE_PRESENCE_ECO,
    CONF_ROOM_ENABLE_LEARNING,
    CONF_ROOM_ENABLE_OPENING_PAUSE,
    CONF_ROOM_OPENING_SENSORS,
    CONF_ROOM_PAUSE_AFTER_OPEN_MIN,
    CONF_ROOM_QUICK_START_DEFICIT_C,
    CONF_ROOM_START_DEFICIT_C,
    CONF_ROOM_STOP_SURPLUS_C,
    CONF_ROOM_RADIATORS,
    CONF_ROOM_RESUME_AFTER_CLOSED_MIN,
    CONF_ROOM_SENSOR_BIAS_C,
    CONF_ROOM_TARGET_NUMBER,
    CONF_ROOM_TEMP_SENSOR,
    CONF_START_DEFICIT_C,
    CONF_STOP_SURPLUS_C,
    CONF_UPDATE_SECONDS,
    CONF_VACUUM_ENTITY,
    CONF_WEATHER_ENTITY,
    DEFAULT_AI_DECISION_INTERVAL_MIN,
    DEFAULT_AI_PRIMARY_ENGINE,
    DEFAULT_AI_MODEL_FAST,
    DEFAULT_AI_MODEL_REPORT,
    DEFAULT_AI_FALLBACK_ENGINE,
    DEFAULT_AI_PROVIDER,
    DEFAULT_AI_REPORT_ENGINE,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_DECIMALS,
    DEFAULT_ENABLE_LEARNING,
    DEFAULT_FLOW_LIMIT_MARGIN_C,
    DEFAULT_GARAGE_ROOM_QUICK_START_DEFICIT_C,
    DEFAULT_GARAGE_ROOM_START_DEFICIT_C,
    DEFAULT_HUMIDITY_COMFORT_ENABLED,
    DEFAULT_HUMIDITY_DRY_THRESHOLD,
    DEFAULT_HUMIDITY_HUMID_THRESHOLD,
    DEFAULT_HUMIDITY_MAX_OFFSET_C,
    DEFAULT_HEAT_PUMP_CHEAP_PRIORITY_FACTOR,
    DEFAULT_HEAT_PUMP_CHEAP_FAN_MODE,
    DEFAULT_HEAT_SOURCE_DIRECTION_BIAS,
    DEFAULT_CHEAP_POWER_RADIATOR_SETBACK_EXTRA_C,
    DEFAULT_OPENCLAW_ENABLED,
    DEFAULT_OPENCLAW_BRIDGE_URL,
    DEFAULT_OPENCLAW_MODEL_FALLBACK,
    DEFAULT_OPENCLAW_MODEL_PREFERRED,
    DEFAULT_OPENCLAW_ONLY_MODE,
    DEFAULT_OPENCLAW_PAYLOAD_PROFILE,
    DEFAULT_OPENCLAW_TIMEOUT_SEC,
    DEFAULT_OPENCLAW_URL,
    DEFAULT_PID_DEADBAND_C,
    DEFAULT_PID_INTEGRAL_LIMIT,
    DEFAULT_PID_KD,
    DEFAULT_PID_KI,
    DEFAULT_PID_KP,
    DEFAULT_PID_OFFSET_MAX_C,
    DEFAULT_PRICE_MARGIN,
    DEFAULT_PRESENCE_AWAY_MIN,
    DEFAULT_PRESENCE_RETURN_MIN,
    DEFAULT_PROVIDER_PAYLOAD_PROFILE,
    DEFAULT_RADIATOR_BOOST_C,
    DEFAULT_RADIATOR_SETBACK_C,
    DEFAULT_REPORT_INTERVAL_MIN,
    DEFAULT_REVERT_TIMEOUT_MIN,
    DEFAULT_ROOM_ANTI_SHORT_CYCLE_MIN,
    DEFAULT_ROOM_ENABLE_PRESENCE_ECO,
    DEFAULT_ROOM_ENABLE_LEARNING,
    DEFAULT_ROOM_ENABLE_OPENING_PAUSE,
    DEFAULT_ROOM_LINK_GROUP,
    DEFAULT_ROOM_HEAT_SOURCE_DIRECTION_BIAS,
    DEFAULT_ROOM_CHEAP_POWER_RADIATOR_SETBACK_EXTRA_C,
    DEFAULT_ROOM_MASSIVE_OVERHEAT_C,
    DEFAULT_ROOM_MASSIVE_OVERHEAT_MIN,
    DEFAULT_ROOM_PAUSE_AFTER_OPEN_MIN,
    DEFAULT_ROOM_QUICK_START_DEFICIT_C,
    DEFAULT_ROOM_START_DEFICIT_C,
    DEFAULT_ROOM_STOP_SURPLUS_C,
    DEFAULT_ROOM_RESUME_AFTER_CLOSED_MIN,
    DEFAULT_ROOM_SENSOR_BIAS_C,
    DEFAULT_UPDATE_SECONDS,
    DOMAIN,
    PAYLOAD_PROFILE_HEAVY,
    RUNTIME_AI_DECISION_INTERVAL_MIN,
    RUNTIME_ECO_TARGET,
    RUNTIME_ENABLED,
    RUNTIME_GLOBAL_TARGET,
    RUNTIME_CONFIDENCE_THRESHOLD,
    RUNTIME_LEARNING_ENABLED,
    RUNTIME_COMFORT_MODE_ENABLED,
    RUNTIME_PID_DEADBAND_C,
    RUNTIME_PID_INTEGRAL_LIMIT,
    RUNTIME_PID_KD,
    RUNTIME_PID_KI,
    RUNTIME_PID_KP,
    RUNTIME_PID_OFFSET_MAX_C,
    RUNTIME_PID_LAYER_ENABLED,
    RUNTIME_PRESENCE_AWAY_MIN,
    RUNTIME_PRESENCE_RETURN_MIN,
    RUNTIME_REPORT_INTERVAL_MIN,
    RUNTIME_REVERT_TIMEOUT_MIN,
    RUNTIME_PRESENCE_ECO_ENABLED,
)

LOGGER = logging.getLogger(__name__)
OPENCLAW_RUNTIME_TMP_DIR = Path(
    os.environ.get("OPENCLAW_RUNTIME_TMP_DIR", "/config/custom_components/ai_varme_styring/runtime/tmp")
)
OPENCLAW_COMPLETION_RESULTS_CANDIDATES = [
    OPENCLAW_RUNTIME_TMP_DIR / "openclaw_completion_results.json",
    Path('/config/_tmp_openclaw_completion_results.json'),
]
OPENCLAW_RUNTIME_ERROR_LOG = OPENCLAW_RUNTIME_TMP_DIR / "ai_varme_runtime_error.log"
OPENCLAW_COMPLETION_WORKER_LOG = OPENCLAW_RUNTIME_TMP_DIR / "openclaw_completion_worker.log"
OPENCLAW_BRIDGE_LOG = OPENCLAW_RUNTIME_TMP_DIR / "openclaw_bridge.log"
OPENCLAW_SERVICES_ENSURE_LOG = OPENCLAW_RUNTIME_TMP_DIR / "openclaw_services_ensure.log"

_OPENCLAW_BRIDGE_ENV_FILE = "/config/custom_components/ai_varme_styring/runtime/systemd/openclaw-decision-bridge.env"


def _write_services_ensure_log(stage: str, **payload: object) -> None:
    try:
        row = {"stage": stage, **payload}
        OPENCLAW_SERVICES_ENSURE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with OPENCLAW_SERVICES_ENSURE_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _load_openclaw_bridge_env() -> dict[str, str]:
    """Load KEY=VALUE pairs from the bridge env file when present."""
    data: dict[str, str] = {}
    try:
        with open(_OPENCLAW_BRIDGE_ENV_FILE, "r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                data[key.strip()] = value.strip()
    except FileNotFoundError:
        return {}
    except Exception as err:  # noqa: BLE001
        LOGGER.debug("Could not load OpenClaw bridge env: %s", err)
    return data


def _is_localhost_http_url(value: str, port: int) -> bool:
    candidate = str(value or "").strip().lower()
    return f"127.0.0.1:{port}" in candidate or f"localhost:{port}" in candidate
_STORE_VERSION = 1
_LEGACY_AUTOMATION_IDS = {
    "varmepumpe_prioritet_kontinuerlig_vurdering",
    "varmepumpe_prioritet_stue_massiv_overvarme_sluk",
    "varmepumpe_prioritet_kokken_massiv_overvarme_sluk",
    "varmepumpe_prioritet_garage_massiv_overvarme_sluk",
    "garage_varmepumpe_prioritet_setpoint_stabil",
    "varmepumpe_ollama_generate_report",
    "varmepumpe_ollama_manual_trigger",
    "varmepumpe_ai_setpoint_change_trigger_run",
    "varmepumpe_ollama_daily_report",
    "varmepumpe_ollama_sync_helpers",
    "varmepumpe_ollama_sync_live_tuning_json",
    "varmepumpe_ollama_auto_tuning_apply",
    "varmepumpe_ai_varme_sync_prioritet_to_ollama",
    "varmepumpe_ai_varme_sync_ollama_to_prioritet",
    "varmepumpe_ollama_health_check",
    "varmepumpe_sensor_validation",
    "varmepumpe_prioritet_evaluering_watchdog",
    "varmepumpe_ollama_handler_styre_temp",
    "varmepumpe_ollama_confidence_extraction",
    "varmepumpe_ollama_learning_feedback_loop",
    "varmepumpe_ollama_handler_revert_logic",
    "varmepumpe_ai_setpoint_snapshot_init",
    "varmepumpe_ai_setpoint_snapshot_update_from_user",
    "varmepumpe_ai_setpoint_restore_authoritative",
    "garage_ai_presence_eco_enter",
    "garage_ai_presence_eco_exit_on_presence",
    "garage_ai_presence_eco_exit_when_ai_off",
    "garage_ai_presence_eco_hard_floor_guard",
    "garage_ai_presence_eco_user_override_release",
    "garage_ai_presence_eco_heat_failsafe",
    "garage_radiator_sync_under_ai_priority",
    "varmepumpe_pid_layer_garage_update",
    "varmepumpe_pid_layer_garage_reset",
    "varmepumpe_ai_handler_watchdog",
    "varmepumpe_ollama_analysis_15min",
}


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, "unknown", "unavailable", "none", "None", ""):
            return None
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _is_on(state: str | None) -> bool:
    return str(state).lower() in {"on", "home", "true", "open", "detected"}


def _minutes_since(ts: float | int | None, now_ts: float) -> float:
    if ts is None:
        return 10_000.0
    return max(0.0, (now_ts - float(ts)) / 60.0)


def _fmt_ts(ts: float | int | None) -> str | None:
    if ts is None:
        return None
    return dt_util.as_local(dt_util.utc_from_timestamp(float(ts))).strftime("%Y-%m-%d %H:%M:%S")


def _runtime_file_status(path: Path, now_ts: float) -> dict[str, Any]:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return {
            "path": str(path),
            "exists": False,
            "size_bytes": None,
            "updated_at": None,
            "age_seconds": None,
        }
    except Exception:
        return {
            "path": str(path),
            "exists": False,
            "size_bytes": None,
            "updated_at": None,
            "age_seconds": None,
        }
    updated_ts = float(stat.st_mtime)
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": int(stat.st_size),
        "updated_at": _fmt_ts(updated_ts),
        "age_seconds": round(max(0.0, now_ts - updated_ts), 1),
    }


def _openclaw_runtime_health(runtime_status: dict[str, Any]) -> str:
    if not isinstance(runtime_status, dict):
        return "unknown"
    results = runtime_status.get("results_file") if isinstance(runtime_status.get("results_file"), dict) else {}
    worker = runtime_status.get("completion_worker_log") if isinstance(runtime_status.get("completion_worker_log"), dict) else {}
    bridge = runtime_status.get("bridge_log") if isinstance(runtime_status.get("bridge_log"), dict) else {}
    if not results.get("exists") or not worker.get("exists") or not bridge.get("exists"):
        return "missing"
    ages = [
        results.get("age_seconds"),
        worker.get("age_seconds"),
        bridge.get("age_seconds"),
    ]
    numeric_ages = [float(age) for age in ages if isinstance(age, (int, float))]
    if not numeric_ages:
        return "unknown"
    max_age = max(numeric_ages)
    if max_age > 3600:
        return "stale"
    if max_age > 600:
        return "aging"
    return "fresh"


def _slug_text(value: str) -> str:
    normalized = value.lower()
    normalized = normalized.replace("æ", "ae").replace("ø", "oe").replace("å", "aa")
    out = []
    for ch in normalized:
        if ("a" <= ch <= "z") or ("0" <= ch <= "9"):
            out.append(ch)
        else:
            out.append("_")
    return "".join(out).strip("_")


def _ai_provider_display(provider: str) -> str:
    if provider == AI_ENGINE_NONE:
        return "Ingen"
    if provider == AI_PRIMARY_ENGINE_OPENCLAW:
        return "OpenClaw"
    if provider == AI_PROVIDER_GEMINI:
        return "Gemini"
    if provider == AI_PROVIDER_OLLAMA:
        return "Ollama"
    return str(provider or "Ukendt")


def _normalize_primary_engine(engine: str, provider: str) -> str:
    engine_norm = str(engine or "").strip().lower()
    provider_norm = str(provider or "").strip().lower()
    if engine_norm == AI_PRIMARY_ENGINE_OPENCLAW:
        return AI_PRIMARY_ENGINE_OPENCLAW
    if engine_norm in {AI_PRIMARY_ENGINE_PROVIDER, AI_PROVIDER_OLLAMA, AI_PROVIDER_GEMINI}:
        return provider_norm if provider_norm in {AI_PROVIDER_OLLAMA, AI_PROVIDER_GEMINI} else AI_PROVIDER_OLLAMA
    return DEFAULT_AI_PRIMARY_ENGINE


def _ai_decision_source_display(source: str) -> str:
    src = str(source or "").strip().lower()
    if src.startswith("openclaw_bridge:openclaw_callback"):
        return "OpenClaw callback"
    if src.startswith("openclaw_bridge:openclaw"):
        return "OpenClaw bridge"
    if src.startswith("openclaw_bridge:"):
        return "OpenClaw bridge"
    if src.startswith("openclaw"):
        return "OpenClaw"
    if "ollama_fallback" in src:
        return "Ollama fallback"
    if src == AI_PROVIDER_OLLAMA:
        return "Ollama"
    if src == AI_PROVIDER_GEMINI:
        return "Gemini"
    if src == "last_good":
        return "Sidste gyldige AI"
    if src == "safe_default":
        return "Sikker standard"
    if src == "safe_default_openclaw_only":
        return "Sikker standard (OpenClaw only)"
    if src == "safe_default_ollama_cooldown":
        return "Sikker standard (Ollama cooldown)"
    return source or "Ukendt"


def _summarize_ai_errors(errors: Any) -> dict[str, str]:
    if not isinstance(errors, dict):
        return {}
    summary: dict[str, str] = {}
    for key, value in errors.items():
        engine = str(key or "").strip().lower()
        message = str(value or "").strip()
        if not engine or not message:
            continue
        compact = " ".join(message.split())
        summary[engine] = compact[:240]
    return summary


def _fallback_reason_from_decision(
    source: str,
    structured: dict[str, Any] | None,
) -> str:
    source_norm = str(source or "").strip().lower()
    errors = _summarize_ai_errors(
        structured.get("_errors") if isinstance(structured, dict) else {}
    )
    if source_norm == "last_good":
        if errors:
            return "Sidste gyldige AI blev brugt, fordi nyere beslutning fejlede."
        return "Sidste gyldige AI blev genbrugt."
    if source_norm == "safe_default":
        if errors:
            return "Sikker standard blev brugt, fordi alle AI-motorer fejlede."
        return "Sikker standard blev brugt."
    if source_norm == "openclaw_callback":
        return "Sen OpenClaw-callback blev adopteret efter timeout/fallback."
    if source_norm == "openclaw_mqtt_sensor":
        return "Frisk OpenClaw-beslutning blev adopteret fra MQTT."
    if "ollama_fallback" in source_norm:
        return "Ollama blev brugt som fallback-beslutningsmotor."
    if source_norm.startswith("openclaw_queue:"):
        return "OpenClaw queue-path blev brugt."
    if source_norm.startswith("openclaw_bridge:"):
        return "OpenClaw bridge-path blev brugt."
    if source_norm.startswith("openclaw"):
        return "OpenClaw blev brugt som beslutningsmotor."
    return ""


def _resolve_room_humidity_sensor_entity(hass: HomeAssistant, room_name: str, temp_entity: str | None) -> str | None:
    if temp_entity:
        candidate = str(temp_entity).replace("_temperature", "_humidity")
        if candidate != temp_entity and hass.states.get(candidate):
            return candidate
        candidate = str(temp_entity).replace("_temp", "_humidity")
        if candidate != temp_entity and hass.states.get(candidate):
            return candidate
    slug = _slug_text(room_name)
    preferred = [
        f"sensor.temp_fugtighed_{slug}_humidity",
        f"sensor.{slug}_humidity",
    ]
    for entity_id in preferred:
        if hass.states.get(entity_id):
            return entity_id
    return None


def _humidity_comfort_offset_c(
    humidity: float | None,
    *,
    enabled: bool,
    dry_threshold: float,
    humid_threshold: float,
    max_offset_c: float,
) -> float:
    if humidity is None:
        return 0.0
    if not enabled:
        return 0.0
    h = float(humidity)
    if h < max(dry_threshold - 5.0, 0.0):
        return max_offset_c
    if h < dry_threshold:
        return max_offset_c * 0.67
    if h > humid_threshold + 10.0:
        return -max_offset_c
    if h > humid_threshold:
        return -(max_offset_c * 0.67)
    return 0.0


def _comfort_band_from_humidity(
    humidity: float | None,
    *,
    enabled: bool,
    dry_threshold: float,
    humid_threshold: float,
) -> str:
    if humidity is None:
        return "ukendt"
    if not enabled:
        return "deaktiveret"
    h = float(humidity)
    if h < dry_threshold:
        return "tør"
    if h > humid_threshold:
        return "fugtig"
    return "komfort"


def _compact_payload_dict(payload: dict[str, Any], *, keep_empty_keys: set[str] | None = None) -> dict[str, Any]:
    """Remove empty optional values while preserving booleans and real zeros."""
    keep_empty = keep_empty_keys or set()
    compact: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            nested = _compact_payload_dict(value, keep_empty_keys=keep_empty_keys)
            if nested or key in keep_empty:
                compact[key] = nested
            continue
        if isinstance(value, list):
            items: list[Any] = []
            for item in value:
                if isinstance(item, dict):
                    nested = _compact_payload_dict(item, keep_empty_keys=keep_empty_keys)
                    if nested:
                        items.append(nested)
                elif item not in (None, ""):
                    items.append(item)
            if items or key in keep_empty:
                compact[key] = items
            continue
        if value is None or value == "":
            continue
        compact[key] = value
    return compact


def _build_provider_decision_payload(openclaw_payload: dict[str, Any]) -> dict[str, Any]:
    """Compact decision payload for provider/Ollama calls."""
    runtime = openclaw_payload.get("runtime", {})
    prices = openclaw_payload.get("prices", {})
    engine_context = openclaw_payload.get("engine_context", {})
    rooms = openclaw_payload.get("rooms", [])
    compact_rooms: list[dict[str, Any]] = []
    if isinstance(rooms, list):
        for room in rooms:
            if not isinstance(room, dict):
                continue
            compact_rooms.append(
                _compact_payload_dict(
                    {
                        "name": room.get("name"),
                        "temp": room.get("temp"),
                        "target": room.get("target"),
                        "deficit": room.get("deficit"),
                        "surplus": room.get("surplus"),
                        "humidity": room.get("humidity"),
                        "comfort_band": room.get("comfort_band"),
                        "comfort_gap": room.get("comfort_gap"),
                        "opening_active": room.get("opening_active"),
                        "room_enabled": room.get("room_enabled"),
                        "boost_active": room.get("boost_active"),
                        "heat_pump_state": room.get("heat_pump_state"),
                        "heat_pump_power_w": room.get("heat_pump_power_w"),
                        "active_heat_summary": room.get("active_heat_summary"),
                        "is_heating_now": room.get("is_heating_now"),
                    }
                )
            )
    return _compact_payload_dict(
        {
            "timestamp_utc": openclaw_payload.get("timestamp_utc"),
            "engine_context": {
                "ai_provider": engine_context.get("ai_provider"),
                "ai_primary_engine": engine_context.get("ai_primary_engine"),
                "decision_interval_min": engine_context.get("decision_interval_min"),
            },
            "runtime": {
                "enabled": runtime.get("enabled"),
                "presence_eco_active": runtime.get("presence_eco_active"),
                "flow_limited": runtime.get("flow_limited"),
                "thermostat_handover": runtime.get("thermostat_handover"),
                "provider_ready": runtime.get("provider_ready"),
            },
            "prices": {
                "electricity": prices.get("electricity"),
                "gas": prices.get("gas"),
                "district_heat": prices.get("district_heat"),
                "effective_heat_pump_price": prices.get("effective_heat_pump_price"),
                "cheapest_alt_name": prices.get("cheapest_alt_name"),
                "cheapest_alt_price": prices.get("cheapest_alt_price"),
                "heat_pump_cheaper": prices.get("heat_pump_cheaper"),
                "estimated_savings_per_kwh": prices.get("estimated_savings_per_kwh"),
            },
            "max_deficit": openclaw_payload.get("max_deficit"),
            "max_surplus": openclaw_payload.get("max_surplus"),
            "outdoor_temp": openclaw_payload.get("outdoor_temp"),
            "sensor_error": openclaw_payload.get("sensor_error"),
            "rooms": compact_rooms,
        },
        keep_empty_keys={"rooms"},
    )


def _build_openclaw_heating_payload(
    hass: HomeAssistant,
    source_payload: dict[str, Any],
    *,
    now_ts: float,
    room_runtime: dict[str, dict[str, Any]],
    weather_forecast_next_2h: dict[str, float] | None = None,
    supply_temp: float | None = None,
    return_temp: float | None = None,
    heating_curve_offset: float | None = None,
    last_decision_factor: float | None = None,
    last_decision_mode: str | None = None,
    last_decision_age_sec: int = 0,
) -> dict[str, Any]:
    """Build the strict OpenClaw heating contract from live integration data."""

    rooms = source_payload.get("rooms", [])
    request_id = str(source_payload.get("request_id") or uuid.uuid4())
    timestamp_utc = str(source_payload.get("timestamp_utc") or dt_util.utcnow().isoformat())

    mode = "normal"
    house_mode_state = str(
        (hass.states.get("input_select.house_mode").state if hass.states.get("input_select.house_mode") else "")
    ).strip().lower()
    alarm_state = str(
        (
            hass.states.get("alarm_control_panel.verisure_alarm").state
            if hass.states.get("alarm_control_panel.verisure_alarm")
            else ""
        )
    ).strip().lower()
    follow_alarm_away = _is_on(
        hass.states.get("input_boolean.house_mode_follow_alarm_away").state
        if hass.states.get("input_boolean.house_mode_follow_alarm_away")
        else None
    )
    if house_mode_state in {"ude", "away"}:
        mode = "away"
    elif house_mode_state in {"nat", "night"}:
        mode = "night"
    elif house_mode_state in {"ferie", "holiday"}:
        mode = "away"
    elif follow_alarm_away and alarm_state == "armed_away":
        mode = "away"
    if any(isinstance(room, dict) and bool(room.get("boost_active")) for room in rooms if isinstance(rooms, list)):
        mode = "boost"

    normalized_rooms: list[dict[str, Any]] = []
    if isinstance(rooms, list):
        for room in rooms:
            if not isinstance(room, dict):
                continue
            current_temperature = _safe_float(room.get("temp"))
            target_temperature = _safe_float(room.get("target"))
            if current_temperature is None or target_temperature is None:
                continue
            room_name = str(room.get("name") or "Rum")
            room_rt = room_runtime.get(room_name, {}) if isinstance(room_runtime, dict) else {}
            heat_state = str(room.get("heat_pump_state") or "").strip().lower()
            hvac_action = "idle"
            if bool(room.get("opening_active")):
                hvac_action = "off"
            elif bool(room.get("is_heating_now")):
                hvac_action = "heating"
            elif heat_state == "off":
                hvac_action = "off"

            last_switch = room_rt.get("last_switch") if isinstance(room_rt, dict) else None
            last_heating_change_minutes: int | None = None
            if last_switch is not None:
                last_heating_change_minutes = int(max(0, round(_minutes_since(last_switch, now_ts), 0)))

            room_priority = "medium"
            if not bool(room.get("room_enabled", True)):
                room_priority = "low"

            normalized_rooms.append(
                _compact_payload_dict(
                    {
                        "name": room_name,
                        "entity_id": str(room.get("target_number_entity") or room.get("entity_id") or "").strip() or None,
                        "current_temperature": current_temperature,
                        "target_temperature": target_temperature,
                        "hvac_action": hvac_action,
                        "humidity": _safe_float(room.get("humidity")),
                        "window_open": bool(room.get("opening_active")),
                        "last_heating_change_minutes": last_heating_change_minutes,
                        "valve_open_percent": 100.0 if bool(room.get("is_heating_now")) else 0.0,
                        "room_priority": room_priority,
                    }
                )
            )

    forecast_payload = _compact_payload_dict(
        {
            "temp_min": _safe_float((weather_forecast_next_2h or {}).get("temp_min")),
            "temp_max": _safe_float((weather_forecast_next_2h or {}).get("temp_max")),
            "wind_ms": _safe_float((weather_forecast_next_2h or {}).get("wind_ms")),
        }
    )

    return _compact_payload_dict(
        {
            "type": "heating_decision",
            "request_id": request_id,
            "reply_transport": "mqtt",
            "reply_topic": "homeassistant/ai_varme/openclaw/decision",
            "timestamp_utc": timestamp_utc,
            "mode": mode,
            "boost": mode == "boost",
            "heating_active": any(bool(room.get("is_heating_now")) for room in rooms if isinstance(room, dict))
            if isinstance(rooms, list)
            else False,
            "outside_temperature": _safe_float(source_payload.get("outdoor_temp")),
            "weather_forecast_next_2h": forecast_payload if forecast_payload else None,
            "rooms": normalized_rooms,
            "last_decision": _compact_payload_dict(
                {
                    "factor": _safe_float(last_decision_factor),
                    "global_mode": str(last_decision_mode or "").strip() or None,
                }
            ),
            "last_decision_age_sec": int(max(0, last_decision_age_sec)) if last_decision_age_sec is not None else None,
            "supply_temp": _safe_float(supply_temp),
            "return_temp": _safe_float(return_temp),
            "heating_curve_offset": _safe_float(heating_curve_offset),
        },
        keep_empty_keys={"rooms"},
    )


def _legacy_automation_conflicts(hass: HomeAssistant) -> list[str]:
    conflicts: list[str] = []
    for st in hass.states.async_all("automation"):
        if st.state != "on":
            continue
        aid = st.attributes.get("id")
        if isinstance(aid, str) and aid in _LEGACY_AUTOMATION_IDS:
            conflicts.append(aid)
    conflicts.sort()
    return conflicts


def _resolve_room_target_number_entity(
    hass: HomeAssistant, room_name: str, configured_entity: str | None
) -> str | None:
    """Resolve a usable input_number target helper for a room.

    Prefers configured entity when available; otherwise tries common naming patterns
    and finally scans input_number entities for a room/target match.
    """

    def _state_ok(entity_id: str | None) -> bool:
        if not entity_id:
            return False
        st = hass.states.get(entity_id)
        if st is None:
            return False
        return str(st.state).lower() not in {"unknown", "unavailable", "none", ""}

    base_slug = _slug_text(room_name)
    slug_variants: set[str] = {base_slug}
    slug_variants.add(base_slug.replace("oe", "o").replace("ae", "a").replace("aa", "a"))
    if not base_slug.endswith("n"):
        slug_variants.add(f"{base_slug}n")

    candidates: list[str] = []
    if configured_entity:
        candidates.append(str(configured_entity))
    for slug in sorted(slug_variants):
        candidates.extend(
            [
                f"input_number.thermostat_{slug}_target",
                f"input_number.{slug}_temperature_target",
                f"input_number.ai_varme_target_{slug}",
                f"input_number.{slug}",
            ]
        )

    for st in hass.states.async_all("input_number"):
        eid = st.entity_id
        eid_l = eid.lower()
        if ("target" not in eid_l) and ("temperature_target" not in eid_l):
            continue
        if any(slug in eid_l for slug in slug_variants):
            candidates.append(eid)

    seen: set[str] = set()
    dedup: list[str] = []
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        dedup.append(c)

    for c in dedup:
        if _state_ok(c):
            return c
    return dedup[0] if dedup else None


def _normalize_ai_input_number_target(value: float | None) -> float | None:
    """Normalize AI/helper targets to 0.5C increments."""
    if value is None:
        return None
    try:
        target = float(value)
    except (TypeError, ValueError):
        return None
    target = max(7.0, min(25.0, target))
    return round(target * 2.0) / 2.0


def _resolve_room_temp_sensor_entity(
    hass: HomeAssistant, room_name: str, configured_entity: str | None
) -> str | None:
    """Resolve temperature sensor with safe preference rules.

    For Garage we prefer the base sensor without trailing `_2` when both exist.
    """

    def _state_ok(entity_id: str | None) -> bool:
        if not entity_id:
            return False
        st = hass.states.get(entity_id)
        if st is None:
            return False
        return _safe_float(st.state) is not None

    base_slug = _slug_text(room_name)
    slug_variants: set[str] = {base_slug}
    slug_variants.add(base_slug.replace("oe", "o").replace("ae", "a").replace("aa", "a"))
    if not base_slug.endswith("en"):
        slug_variants.add(f"{base_slug}en")
    if not base_slug.endswith("n"):
        slug_variants.add(f"{base_slug}n")

    candidates: list[str] = []
    configured = str(configured_entity or "").strip()
    if configured:
        room_l = room_name.lower()
        if "garage" in room_l and configured.endswith("_2"):
            base = configured[:-2]
            # user-preferred garage sensor should win if available
            candidates.append(base)
        candidates.append(configured)

    for slug in sorted(slug_variants):
        candidates.extend(
            [
                f"sensor.temp_fugtighed_{slug}_temperature",
                f"sensor.{slug}_temperature",
                f"sensor.{slug}_temperatur",
                f"sensor.weathersense_feels_like_temperature_{slug}",
            ]
        )

    for st in hass.states.async_all("sensor"):
        eid = st.entity_id
        eid_l = eid.lower()
        if not any(slug in eid_l for slug in slug_variants):
            continue
        if not any(token in eid_l for token in ("temperature", "temperatur")):
            continue
        candidates.append(eid)

    seen: set[str] = set()
    dedup: list[str] = []
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        dedup.append(c)

    for c in dedup:
        if _state_ok(c):
            return c
    return dedup[0] if dedup else None


def _resolve_room_heat_pump_power_sensor_entity(
    hass: HomeAssistant,
    room_name: str,
    room_cfg: dict[str, Any],
) -> str | None:
    """Resolve optional heat pump power sensor for a room."""

    def _looks_like_non_heat_pump_power(entity_id: str) -> bool:
        st = hass.states.get(entity_id)
        label_parts = [entity_id.lower()]
        if st:
            label_parts.append(str((st.attributes or {}).get("friendly_name", "")).lower())
        label = " ".join(label_parts)
        return any(token in label for token in (" pc", "pc ", "computer", "server", "desktop", "laptop"))

    def _state_ok(entity_id: str) -> bool:
        st = hass.states.get(entity_id)
        if not st:
            return False
        if _looks_like_non_heat_pump_power(entity_id):
            return False
        return _safe_float(st.state) is not None

    explicit = str(room_cfg.get(CONF_ROOM_HEAT_PUMP_POWER_SENSOR) or "").strip()
    if explicit:
        if _state_ok(explicit):
            return explicit
        return explicit

    hp_entity = str(room_cfg.get(CONF_ROOM_HEAT_PUMP) or "").strip()
    hp_obj = hp_entity.split(".", 1)[-1] if hp_entity.startswith("climate.") else hp_entity
    room_slug = _slug_text(room_name)
    candidates: list[str] = []
    if hp_obj:
        for suf in ("power", "active_power", "electric_power", "watt", "forbrug"):
            candidates.append(f"sensor.{hp_obj}_{suf}")
    if room_slug:
        for pref in (room_slug, f"qlima_{room_slug}", f"ac_{room_slug}", f"varmepumpe_{room_slug}"):
            for suf in ("power", "active_power", "electric_power", "watt", "forbrug"):
                candidates.append(f"sensor.{pref}_{suf}")

    for st in hass.states.async_all("sensor"):
        eid = st.entity_id
        low = eid.lower()
        if hp_obj and hp_obj.lower() in low and any(t in low for t in ("power", "watt", "forbrug", "consumption")):
            candidates.append(eid)
        elif (
            room_slug
            and room_slug in low
            and any(t in low for t in ("power", "watt", "forbrug", "consumption"))
            and any(t in low for t in ("qlima", "ac_", "varmepumpe", "heat_pump", "hvac", "aircondition"))
        ):
            candidates.append(eid)

    seen: set[str] = set()
    dedup: list[str] = []
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        dedup.append(c)

    for c in dedup:
        if _state_ok(c):
            return c
    return dedup[0] if dedup else None


def _power_sensor_to_watts(state_obj) -> float | None:
    """Convert power sensor value to watts when possible."""
    if not state_obj:
        return None
    raw = _safe_float(state_obj.state)
    if raw is None:
        return None
    unit = str((state_obj.attributes or {}).get("unit_of_measurement", "")).strip().lower()
    if unit in {"kw", "kilowatt", "kilowatts"}:
        return float(raw) * 1000.0
    return float(raw)


@dataclass
class RoomSnapshot:
    """Room state used by AI motor."""

    name: str
    sensor_entity: str
    humidity_sensor_entity: str | None
    humidity: float | None
    raw_temperature: float
    temperature: float
    target: float
    comfort_target: float
    comfort_offset_c: float
    comfort_gap: float
    comfort_band: str
    deficit: float
    surplus: float
    opening_active: bool
    occupancy_active: bool
    presence_eco_enabled: bool
    learning_enabled: bool
    opening_pause_enabled: bool
    room_enabled: bool
    eco_target: float
    presence_away_min: float
    presence_return_min: float
    boost_active: bool
    boost_delta_c: float
    boost_until_ts: float | None
    boost_duration_min: float
    target_number_entity: str | None
    heat_pump: str | None
    heat_pump_power_sensor: str | None
    heat_pump_power_w: float | None
    radiators: list[str]
    link_group: str
    adjacent_rooms: list[str]
    room_heat_source_direction_bias: float
    room_cheap_power_radiator_setback_extra_c: float
    anti_short_cycle_min: float
    quick_start_deficit_c: float
    start_deficit_c: float
    stop_surplus_c: float
    pause_after_open_min: float
    resume_after_closed_min: float
    massive_overheat_c: float
    massive_overheat_min: float
    active_heat_entities: list[str] = field(default_factory=list)
    active_heat_names: list[str] = field(default_factory=list)
    active_heat_summary: str = "Ingen aktiv varmekilde"
    is_heating_now: bool = False


class AiVarmeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """AI engine and state coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.ai_client = AiProviderClient(hass)
        self._room_runtime: dict[str, dict[str, Any]] = {}
        self._ai_factor: float = 1.0
        self._ai_reason: str = "AI standard"
        self._ai_confidence: float = 75.0
        self._ai_decision_source: str = "safe_default"
        self._ai_structured_decision: dict[str, Any] = {}
        self._ai_prev_factor: float | None = None
        self._ai_prev_reason: str = ""
        self._ai_prev_confidence: float | None = None
        self._ai_prev_decision_source: str = ""
        self._last_ai_decision_payload: dict[str, Any] = {}
        self._last_ai_decision_payload_openclaw: dict[str, Any] = {}
        self._last_ai_decision_payload_provider: dict[str, Any] = {}
        self._last_ai_report_payload: dict[str, Any] = {}
        self._ai_fallback_count: int = 0
        self._last_ai_errors: dict[str, str] = {}
        self._last_ai_fallback_reason: str = ""
        self._last_ai_update = None
        self._last_report_update = None
        self._ai_report_text: str = ""
        self._last_report_model_used: str = ""
        self._manual_full_report_requested: bool = False
        self._bridge_stats: dict[str, Any] = {}
        self._last_bridge_stats_update: float | None = None
        self._last_room_helper_selfheal_ts: float | None = None
        self._analytics_samples: list[dict[str, Any]] = []
        self._manual_baseline: dict[str, dict[str, Any]] = {}
        self._last_valid_prices: dict[str, float] = {}
        self._cycle_temperature_commands: dict[str, float] = {}
        self._cycle_hvac_commands: dict[str, str] = {}
        self._cycle_fan_commands: dict[str, str] = {}
        self._recent_temperature_commands: dict[str, tuple[float, float]] = {}
        self._recent_hvac_commands: dict[str, tuple[str, float]] = {}
        self._recent_fan_commands: dict[str, tuple[str, float]] = {}
        self._runtime_events: dict[str, float | None] = {
            "enabled_last_changed": None,
            "presence_eco_last_changed": None,
            "pid_last_changed": None,
            "learning_last_changed": None,
            "manual_ai_last_trigger": None,
            "manual_report_last_trigger": None,
            "last_control_activity": None,
        }
        self._store = Store(hass, _STORE_VERSION, f"{DOMAIN}_{entry.entry_id}_runtime")
        self._runtime_loaded = False
        super().__init__(
            hass,
            logger=LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(
                seconds=int(({**entry.data, **entry.options}).get(CONF_UPDATE_SECONDS, DEFAULT_UPDATE_SECONDS))
            ),
        )

    async def _async_load_runtime(self) -> None:
        if self._runtime_loaded:
            return
        self._runtime_loaded = True
        data = await self._store.async_load()
        if not isinstance(data, dict):
            return
        rr = data.get("room_runtime")
        if isinstance(rr, dict):
            self._room_runtime = rr
        migrated_runtime = False
        baseline = data.get("manual_baseline")
        if isinstance(baseline, dict):
            self._manual_baseline = baseline
        price_memory = data.get("last_valid_prices")
        if isinstance(price_memory, dict):
            cleaned_prices: dict[str, float] = {}
            for key, val in price_memory.items():
                num = _safe_float(val)
                if num is not None:
                    cleaned_prices[str(key)] = float(num)
            self._last_valid_prices = cleaned_prices
        events = data.get("runtime_events")
        if isinstance(events, dict):
            for key in self._runtime_events:
                val = events.get(key)
                if isinstance(val, (int, float)):
                    self._runtime_events[key] = float(val)
        factor = data.get("ai_factor")
        reason = data.get("ai_reason")
        conf = data.get("ai_confidence")
        last_ai = data.get("last_ai_update_ts")
        last_report = data.get("last_report_update_ts")
        report_text = data.get("ai_report_text")
        report_model_used = data.get("last_report_model_used")
        decision_source = data.get("ai_decision_source")
        structured_decision = data.get("ai_structured_decision")
        fallback_count = data.get("ai_fallback_count")
        analytics_samples = data.get("analytics_samples")
        bridge_stats = data.get("bridge_stats")
        bridge_stats_ts = data.get("bridge_stats_last_update_ts")
        if isinstance(factor, (int, float)):
            self._ai_factor = float(factor)
        if isinstance(reason, str):
            self._ai_reason = reason
        if isinstance(conf, (int, float)):
            self._ai_confidence = float(conf)
        if isinstance(last_ai, (int, float)):
            self._last_ai_update = float(last_ai)
        if isinstance(last_report, (int, float)):
            self._last_report_update = float(last_report)
        if isinstance(report_text, str):
            self._ai_report_text = report_text
        if isinstance(report_model_used, str):
            self._last_report_model_used = report_model_used
        if isinstance(decision_source, str):
            self._ai_decision_source = decision_source
        if isinstance(structured_decision, dict):
            self._ai_structured_decision = structured_decision
        if isinstance(fallback_count, (int, float)):
            self._ai_fallback_count = int(fallback_count)
        self._last_ai_errors = _summarize_ai_errors(
            self._ai_structured_decision.get("_errors")
            if isinstance(self._ai_structured_decision, dict)
            else {}
        )
        self._last_ai_fallback_reason = _fallback_reason_from_decision(
            self._ai_decision_source,
            self._ai_structured_decision if isinstance(self._ai_structured_decision, dict) else {},
        )
        if isinstance(analytics_samples, list):
            cleaned: list[dict[str, Any]] = []
            for row in analytics_samples:
                if not isinstance(row, dict):
                    continue
                ts = row.get("ts")
                if not isinstance(ts, (int, float)):
                    continue
                cleaned.append(
                    {
                        "ts": float(ts),
                        "mode": str(row.get("mode", "Klar")),
                        "el_price": _safe_float(row.get("el_price")),
                        "gas_price": _safe_float(row.get("gas_price")),
                        "district_heat_price": _safe_float(row.get("district_heat_price")),
                        "gas_consumption": _safe_float(row.get("gas_consumption")),
                        "district_heat_consumption": _safe_float(row.get("district_heat_consumption")),
                    }
                )
            self._analytics_samples = cleaned
        if isinstance(bridge_stats, dict):
            self._bridge_stats = bridge_stats
        if isinstance(bridge_stats_ts, (int, float)):
            self._last_bridge_stats_update = float(bridge_stats_ts)

        # One-time runtime migration: if a room is already in eco-active state after restart,
        # but target_override/lock still points to old comfort target, reconcile to eco target.
        # This prevents heat pumps from continuing toward comfort targets during active eco.
        for room_name, room_rt in list(self._room_runtime.items()):
            if not isinstance(room_rt, dict):
                continue
            if room_name.startswith("__target_lock__") or room_name.startswith("__"):
                continue
            if not bool(room_rt.get("eco_active", False)):
                continue
            eco_target = _safe_float(room_rt.get("eco_target_override"))
            if eco_target is None:
                continue
            eco_target = max(7.0, min(25.0, float(eco_target)))
            cur_target = _safe_float(room_rt.get("target_override"))
            lock_key = f"__target_lock__{room_name}"
            lock_rt = self._room_runtime.setdefault(lock_key, {})
            lock_target = _safe_float(lock_rt.get("locked_target")) if isinstance(lock_rt, dict) else None
            if cur_target is None or abs(cur_target - eco_target) > 0.01 or lock_target is None or abs(lock_target - eco_target) > 0.01:
                room_rt["target_override"] = eco_target
                lock_rt["locked_target"] = eco_target
                lock_rt["last_seen_target"] = eco_target
                migrated_runtime = True

        if migrated_runtime:
            await self._async_save_runtime()

    async def _async_selfheal_room_target_helpers(
        self, rooms_cfg: list[dict[str, Any]], now_ts: float
    ) -> list[dict[str, Any]]:
        """Ensure each room has a valid target helper entity linked."""
        if _minutes_since(self._last_room_helper_selfheal_ts, now_ts) < 5.0:
            return rooms_cfg
        self._last_room_helper_selfheal_ts = now_ts

        changed = False
        updated_rooms: list[dict[str, Any]] = []

        for room_cfg in rooms_cfg:
            if not isinstance(room_cfg, dict):
                continue

            room_copy = dict(room_cfg)
            room_name = str(room_copy.get(CONF_ROOM_NAME, "") or "").strip()
            if not room_name:
                updated_rooms.append(room_copy)
                continue

            configured_target = str(room_copy.get(CONF_ROOM_TARGET_NUMBER, "") or "").strip()
            resolved_target = _resolve_room_target_number_entity(self.hass, room_name, configured_target)

            if (not resolved_target) and self.hass.services.has_service("input_number", "create"):
                try:
                    await self.hass.services.async_call(
                        "input_number",
                        "create",
                        {
                            "name": f"AI Varme {room_name} target",
                            "min": 10.0,
                            "max": 30.0,
                            "step": 0.5,
                            "mode": "box",
                            "icon": "mdi:target",
                        },
                        blocking=True,
                    )
                except Exception as err:  # noqa: BLE001
                    _write_services_ensure_log(
                        "room_helper_create_failed",
                        entry_id=self.entry.entry_id,
                        room=room_name,
                        error=str(err),
                    )
                resolved_target = _resolve_room_target_number_entity(self.hass, room_name, configured_target)

            if resolved_target and resolved_target != configured_target:
                room_copy[CONF_ROOM_TARGET_NUMBER] = resolved_target
                changed = True
                _write_services_ensure_log(
                    "room_helper_linked",
                    entry_id=self.entry.entry_id,
                    room=room_name,
                    helper=resolved_target,
                    previous=configured_target or None,
                )
            elif not resolved_target:
                _write_services_ensure_log(
                    "room_helper_missing",
                    entry_id=self.entry.entry_id,
                    room=room_name,
                )

            updated_rooms.append(room_copy)

        if changed:
            new_options = dict(self.entry.options)
            new_options[CONF_ROOMS] = updated_rooms
            self.hass.config_entries.async_update_entry(self.entry, options=new_options)
            _write_services_ensure_log(
                "room_helpers_options_updated",
                entry_id=self.entry.entry_id,
                room_count=len(updated_rooms),
            )
            return updated_rooms

        return rooms_cfg

    async def _async_save_runtime(self) -> None:
        await self._store.async_save(
            {
                "room_runtime": self._room_runtime,
                "manual_baseline": self._manual_baseline,
                "last_valid_prices": self._last_valid_prices,
                "runtime_events": self._runtime_events,
                "ai_factor": self._ai_factor,
                "ai_reason": self._ai_reason,
                "ai_confidence": self._ai_confidence,
                "ai_decision_source": self._ai_decision_source,
                "ai_structured_decision": self._ai_structured_decision,
                "ai_fallback_count": self._ai_fallback_count,
                "last_ai_errors": self._last_ai_errors,
                "last_ai_fallback_reason": self._last_ai_fallback_reason,
                "last_ai_update_ts": self._last_ai_update,
                "last_report_update_ts": self._last_report_update,
                "ai_report_text": self._ai_report_text,
                "last_report_model_used": self._last_report_model_used,
                "analytics_samples": self._analytics_samples,
                "bridge_stats": self._bridge_stats,
                "bridge_stats_last_update_ts": self._last_bridge_stats_update,
            }
        )

    def _optimistically_patch_room_state(
        self,
        room_name: str,
        *,
        target: float | None = None,
        eco_target: float | None = None,
        boost_active: bool | None = None,
        boost_delta_c: float | None = None,
        boost_duration_min: float | None = None,
        boost_until_ts: float | None = None,
    ) -> None:
        """Patch current room data immediately so UI feedback is not delayed."""
        current = self.data
        if not isinstance(current, dict):
            return
        rooms = current.get("rooms")
        if not isinstance(rooms, list):
            return

        patched = copy.deepcopy(current)
        patched_rooms = patched.get("rooms")
        if not isinstance(patched_rooms, list):
            return

        room_found = False
        for room in patched_rooms:
            if not isinstance(room, dict):
                continue
            if str(room.get("name", "")).strip().lower() != room_name.strip().lower():
                continue
            room_found = True
            decimals = 1 if float(room.get("target", 0) or 0).as_integer_ratio()[1] != 1 else 1
            temp = _safe_float(room.get("temperature"))
            if target is not None:
                room["target"] = round(float(target), decimals)
                if temp is not None:
                    room["deficit"] = round(max(float(target) - temp, 0.0), decimals)
                    room["surplus"] = round(max(temp - float(target), 0.0), decimals)
            if eco_target is not None:
                room["eco_target"] = round(float(eco_target), decimals)
            if boost_active is not None:
                room["boost_active"] = bool(boost_active)
            if boost_delta_c is not None:
                room["boost_delta_c"] = round(float(boost_delta_c), decimals)
            if boost_duration_min is not None:
                room["boost_duration_min"] = round(float(boost_duration_min), 1)
            if boost_until_ts is not None:
                room["boost_until"] = _fmt_ts(boost_until_ts)
            elif boost_active is False:
                room["boost_until"] = None
            break

        if room_found:
            self.async_set_updated_data(patched)

    async def _async_fetch_bridge_stats(self, bridge_url: str) -> None:
        base = str(bridge_url).strip()
        if not base:
            return
        if base.endswith("/heating/decision"):
            stats_url = base[: -len("/heating/decision")] + "/stats"
        elif base.endswith("/decision"):
            stats_url = base[: -len("/decision")] + "/stats"
        else:
            stats_url = base.rstrip("/") + "/stats"
        session = async_get_clientsession(self.hass)
        async with session.get(stats_url, timeout=6) as resp:
            resp.raise_for_status()
            data = await resp.json()
            if isinstance(data, dict):
                self._bridge_stats = data
                self._last_bridge_stats_update = dt_util.utcnow().timestamp()

    async def _async_apply_structured_ai_decision(
        self,
        rooms: list[RoomSnapshot],
        decision: dict[str, Any],
        now_ts: float,
        decimals: int,
        actions: list[str],
    ) -> None:
        """Apply optional room-level overrides from a structured AI decision."""
        if not isinstance(decision, dict):
            return
        room_directives = decision.get("rooms")
        if not isinstance(room_directives, list):
            return

        room_by_slug = {_slug_text(room.name): room for room in rooms}
        room_by_entity: dict[str, RoomSnapshot] = {}
        for room in rooms:
            if room.heat_pump:
                room_by_entity[room.heat_pump] = room
            if room.target_number_entity:
                room_by_entity[room.target_number_entity] = room
            for rad in room.radiators:
                room_by_entity[rad] = room

        for directive in room_directives:
            if not isinstance(directive, dict):
                continue
            if directive.get("should_change") is False:
                continue

            room: RoomSnapshot | None = None
            entity_id = str(directive.get("entity_id", "")).strip()
            room_name = str(directive.get("name", "")).strip()
            if entity_id:
                room = room_by_entity.get(entity_id)
            if room is None and room_name:
                room = room_by_slug.get(_slug_text(room_name))
            if room is None:
                continue

            target_temp = _safe_float(directive.get("target_temperature"))
            mode = str(directive.get("mode", "")).strip().lower()
            reason = str(directive.get("reason", "")).strip()
            room_rt = self._room_runtime.setdefault(room.name, {})

            if target_temp is not None:
                target_temp = _normalize_ai_input_number_target(target_temp)
                if target_temp is None:
                    continue
                room_rt["target_override"] = target_temp
                room_rt["room_target_last_changed"] = now_ts
                room.target = target_temp
                room.deficit = max(target_temp - room.temperature, 0.0)
                room.surplus = max(room.temperature - target_temp, 0.0)
                if reason:
                    actions.append(
                        f"{room.name}: OpenClaw driftsoverstyring -> {target_temp}°C ({reason})"
                    )
                else:
                    actions.append(f"{room.name}: OpenClaw driftsoverstyring -> {target_temp}°C")

            if mode in {"off", "heat", "auto", "eco"}:
                room_rt["openclaw_mode_override"] = mode
                room_rt["openclaw_mode_override_ts"] = now_ts
                if mode == "off":
                    actions.append(f"{room.name}: OpenClaw bad om varmepumpe OFF")

    async def async_set_enabled(self, enabled: bool) -> None:
        runtime = self.hass.data[DOMAIN][self.entry.entry_id]
        prev = bool(runtime.get(RUNTIME_ENABLED, True))
        runtime[RUNTIME_ENABLED] = bool(enabled)
        if prev and not enabled:
            await self._async_restore_manual_baseline()
        self._runtime_events["enabled_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()

    async def async_set_presence_eco_enabled(self, enabled: bool) -> None:
        runtime = self.hass.data[DOMAIN][self.entry.entry_id]
        runtime[RUNTIME_PRESENCE_ECO_ENABLED] = bool(enabled)
        self._runtime_events["presence_eco_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()

    async def async_set_pid_enabled(self, enabled: bool) -> None:
        runtime = self.hass.data[DOMAIN][self.entry.entry_id]
        runtime[RUNTIME_PID_LAYER_ENABLED] = bool(enabled)
        self._runtime_events["pid_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()

    async def async_set_learning_enabled(self, enabled: bool) -> None:
        runtime = self.hass.data[DOMAIN][self.entry.entry_id]
        runtime[RUNTIME_LEARNING_ENABLED] = bool(enabled)
        self._runtime_events["learning_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()

    async def async_set_comfort_mode_enabled(self, enabled: bool) -> None:
        runtime = self.hass.data[DOMAIN][self.entry.entry_id]
        runtime[RUNTIME_COMFORT_MODE_ENABLED] = bool(enabled)
        self._runtime_events["comfort_mode_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()

    async def async_set_room_presence_eco_enabled(self, room_name: str, enabled: bool) -> None:
        rt = self._room_runtime.setdefault(room_name, {})
        rt["presence_eco_enabled_override"] = bool(enabled)
        rt["room_presence_eco_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()

    async def async_set_room_opening_pause_enabled(self, room_name: str, enabled: bool) -> None:
        rt = self._room_runtime.setdefault(room_name, {})
        rt["opening_pause_enabled_override"] = bool(enabled)
        rt["room_opening_pause_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()

    async def async_set_room_pause_after_open_min(self, room_name: str, minutes: float) -> None:
        rt = self._room_runtime.setdefault(room_name, {})
        rt["pause_after_open_min_override"] = float(minutes)
        rt["room_pause_after_open_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()

    async def async_set_room_resume_after_closed_min(self, room_name: str, minutes: float) -> None:
        rt = self._room_runtime.setdefault(room_name, {})
        rt["resume_after_closed_min_override"] = float(minutes)
        rt["room_resume_after_closed_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()

    async def async_set_room_sensor_bias(self, room_name: str, bias_c: float) -> None:
        rt = self._room_runtime.setdefault(room_name, {})
        rt["sensor_bias_override"] = float(bias_c)
        rt["room_sensor_bias_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()

    async def async_set_room_target_lock(self, room_name: str, target: float) -> None:
        lock_rt = self._room_runtime.setdefault(
            f"__target_lock__{room_name}",
            {"locked_target": float(target), "last_seen_target": float(target)},
        )
        lock_rt["locked_target"] = float(target)
        lock_rt["last_seen_target"] = float(target)
        await self._async_save_runtime()

    async def async_set_room_target_override(self, room_name: str, target: float) -> None:
        rt = self._room_runtime.setdefault(room_name, {})
        rt["target_override"] = float(target)
        rt["room_target_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()
        self._optimistically_patch_room_state(room_name, target=float(target))
        await self.async_request_refresh()

    async def async_set_room_eco_target(self, room_name: str, target: float) -> None:
        rt = self._room_runtime.setdefault(room_name, {})
        rt["eco_target_override"] = float(target)
        rt["room_eco_target_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()
        self._optimistically_patch_room_state(room_name, eco_target=float(target))

    async def async_set_room_presence_away_min(self, room_name: str, minutes: float) -> None:
        rt = self._room_runtime.setdefault(room_name, {})
        rt["presence_away_min_override"] = float(minutes)
        rt["room_presence_away_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()

    async def async_set_room_presence_return_min(self, room_name: str, minutes: float) -> None:
        rt = self._room_runtime.setdefault(room_name, {})
        rt["presence_return_min_override"] = float(minutes)
        rt["room_presence_return_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()

    async def async_set_room_enabled(self, room_name: str, enabled: bool) -> None:
        rt = self._room_runtime.setdefault(room_name, {})
        rt["room_enabled_override"] = bool(enabled)
        rt["room_enabled_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()

    async def async_set_all_rooms_enabled(self, enabled: bool) -> None:
        cfg = {**self.entry.data, **self.entry.options}
        now_ts = dt_util.utcnow().timestamp()
        for room_cfg in cfg.get(CONF_ROOMS, []):
            room_name = str(room_cfg.get(CONF_ROOM_NAME, "")).strip()
            if not room_name:
                continue
            rt = self._room_runtime.setdefault(room_name, {})
            rt["room_enabled_override"] = bool(enabled)
            rt["room_enabled_last_changed"] = now_ts
        self._runtime_events["all_rooms_enabled_last_changed"] = now_ts
        await self._async_save_runtime()

    async def async_trigger_room_boost(
        self,
        room_name: str,
        *,
        delta_c: float = 1.0,
        duration_min: float = 60.0,
    ) -> None:
        rt = self._room_runtime.setdefault(room_name, {})
        rt["boost_delta_c"] = float(delta_c)
        boost_until_ts = dt_util.utcnow().timestamp() + (float(duration_min) * 60.0)
        rt["boost_until_ts"] = boost_until_ts
        rt["room_boost_last_trigger"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()
        self._optimistically_patch_room_state(
            room_name,
            boost_active=True,
            boost_delta_c=float(delta_c),
            boost_duration_min=float(duration_min),
            boost_until_ts=boost_until_ts,
        )
        await self.async_request_refresh()

    async def async_set_room_boost_delta(self, room_name: str, delta_c: float) -> None:
        rt = self._room_runtime.setdefault(room_name, {})
        rt["boost_delta_c"] = float(delta_c)
        rt["room_boost_delta_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()

    async def async_set_room_boost_duration(self, room_name: str, duration_min: float) -> None:
        rt = self._room_runtime.setdefault(room_name, {})
        rt["boost_duration_min"] = float(duration_min)
        rt["room_boost_duration_last_changed"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()

    def _reconcile_ai_decision_with_payload(
        self,
        payload: dict[str, Any],
        factor: float,
        reason: str,
        confidence: float,
        source: str,
        structured: dict[str, Any],
    ) -> tuple[float, str, float, str, dict[str, Any]]:
        rooms = payload.get("rooms") if isinstance(payload, dict) else None
        if not isinstance(rooms, list):
            return factor, reason, confidence, source, structured

        deficit_rooms = []
        cold_without_heat = []
        for room in rooms:
            if not isinstance(room, dict):
                continue
            deficit = _safe_float(room.get("deficit")) or 0.0
            if deficit > 0.05:
                deficit_rooms.append((str(room.get("name") or "Rum"), deficit, bool(room.get("is_heating_now"))))
                if deficit >= 0.15 and not bool(room.get("is_heating_now")):
                    cold_without_heat.append((str(room.get("name") or "Rum"), deficit))

        if not deficit_rooms:
            return factor, reason, confidence, source, structured

        reason_l = str(reason or "").strip().lower()
        misleading_phrases = [
            'alle rum er ved eller over',
            'alle rum er på eller over',
            'alle rum er over',
            'alle rum er enten ved eller over',
            'alle rum er tæt på eller over',
            'alle rum er tæt på deres måltemperatur',
            'ingen ændring nødvendig',
            'ingen ændringer nødvendige',
            'ingen justering nødvendig',
            'ingen justeringer nødvendige',
            'ingen konkrete ændringer',
            'ingen rum kræver ændring',
            'ingen akut regulering nødvendig',
        ]
        reason_mentions_deficit = any(word in reason_l for word in [
            'under mål',
            'under target',
            'underskud',
            'lidt under',
        ])
        inaccurate_claim = any(phrase in reason_l for phrase in misleading_phrases) and not reason_mentions_deficit
        if not inaccurate_claim:
            return factor, reason, confidence, source, structured

        deficit_names = ', '.join(name for name, _, _ in deficit_rooms[:3])
        if cold_without_heat:
            cold_names = ', '.join(name for name, _ in cold_without_heat[:3])
            new_reason = f'Nogle rum er lidt under mål; {cold_names} er under mål uden aktiv varme.'
            confidence = min(float(confidence), 82.0)
        else:
            new_reason = f'Nogle rum er lidt under mål ({deficit_names}), men afvigelserne er små.'
            confidence = min(float(confidence), 88.0)

        updated = dict(structured or {})
        updated['reason'] = new_reason
        updated['confidence'] = confidence
        meta = updated.get('_openclaw_meta') if isinstance(updated.get('_openclaw_meta'), dict) else {}
        updated['_openclaw_meta'] = {**meta, 'reason_reconciled': True}
        return factor, new_reason, confidence, source, updated

    async def async_trigger_ai_decision(self) -> None:
        self._last_ai_update = None
        self._runtime_events["manual_ai_last_trigger"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()
        await self.async_request_refresh()

    def _read_openclaw_delivered_result(self, request_id: str) -> dict[str, Any] | None:
        for candidate in OPENCLAW_COMPLETION_RESULTS_CANDIDATES:
            try:
                if not candidate.exists():
                    continue
                data = json.loads(candidate.read_text(encoding='utf-8'))
            except Exception:  # noqa: BLE001
                continue
            if not isinstance(data, dict):
                continue
            row = data.get(request_id)
            if not isinstance(row, dict):
                continue
            decision = row.get('decision')
            if not isinstance(decision, dict):
                continue
            if not all(k in decision for k in ('factor', 'confidence', 'reason')):
                continue
            meta = {
                'request_id': request_id,
                'results_file': str(candidate),
                'forwarded_url': row.get('forwarded_url'),
                'delivery_status': row.get('status'),
                'delivery_response_body': row.get('response_body'),
                'delivered_ts': row.get('delivered_ts'),
            }
            return {
                'decision': decision,
                'meta': meta,
            }
        return None

    def _adopt_openclaw_delivered_result_if_available(self) -> bool:
        structured = self._ai_structured_decision if isinstance(self._ai_structured_decision, dict) else {}
        errors = structured.get('_errors') if isinstance(structured.get('_errors'), dict) else {}
        openclaw_error = str(errors.get('openclaw', '')).strip()
        if 'OpenClaw session result timeout for ' not in openclaw_error:
            return False
        match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', openclaw_error, re.I)
        if not match:
            return False
        request_id = match.group(1)
        delivered = self._read_openclaw_delivered_result(request_id)
        if not isinstance(delivered, dict):
            return False
        decision = delivered.get('decision') or {}
        meta = delivered.get('meta') or {}
        try:
            self._ai_factor = max(0.6, min(1.4, float(decision.get('factor', self._ai_factor))))
            self._ai_confidence = max(0.0, min(100.0, float(decision.get('confidence', self._ai_confidence))))
        except Exception:  # noqa: BLE001
            return False
        reason = str(decision.get('reason', self._ai_reason)).strip()
        self._ai_reason = reason or self._ai_reason
        adopted = dict(decision)
        adopted['_openclaw_meta'] = meta
        self._ai_structured_decision = adopted
        self._ai_decision_source = 'openclaw_callback'
        self._last_ai_update = dt_util.utcnow().timestamp()
        return True

    def _adopt_mqtt_sensor_decision_if_available(self) -> bool:
        try:
            mqtt_decision = self.ai_client._mqtt_sensor_decision()
        except Exception:  # noqa: BLE001
            return False
        if not isinstance(mqtt_decision, dict):
            return False
        meta = mqtt_decision.get('_openclaw_meta') if isinstance(mqtt_decision.get('_openclaw_meta'), dict) else {}
        request_id = str(meta.get('request_id') or '').strip()
        age_sec = meta.get('age_sec')
        if not request_id:
            return False
        if isinstance(age_sec, (int, float)) and float(age_sec) > 300:
            return False
        try:
            self._ai_factor = max(0.6, min(1.4, float(mqtt_decision.get('factor', self._ai_factor))))
            self._ai_confidence = max(0.0, min(100.0, float(mqtt_decision.get('confidence', self._ai_confidence))))
        except Exception:  # noqa: BLE001
            return False
        self._ai_reason = str(mqtt_decision.get('reason', self._ai_reason)).strip() or self._ai_reason
        adopted = dict(mqtt_decision)
        adopted['_openclaw_meta'] = meta
        self._ai_structured_decision = adopted
        self._ai_decision_source = 'openclaw_mqtt_sensor'
        self._last_ai_update = dt_util.utcnow().timestamp()
        return True

    async def async_trigger_ai_report(self) -> None:
        self._last_report_update = None
        self._manual_full_report_requested = True
        self._runtime_events["manual_report_last_trigger"] = dt_util.utcnow().timestamp()
        await self._async_save_runtime()
        await self.async_request_refresh()

    def _remember_manual_baseline(self, climate_entity: str) -> None:
        if climate_entity in self._manual_baseline:
            return
        state = self.hass.states.get(climate_entity)
        if not state:
            return
        self._manual_baseline[climate_entity] = {
            "hvac_mode": state.state,
            "temperature": _safe_float(state.attributes.get("temperature")),
        }

    async def _async_restore_manual_baseline(self) -> None:
        for entity_id, baseline in list(self._manual_baseline.items()):
            mode = str(baseline.get("hvac_mode", ""))
            temperature = _safe_float(baseline.get("temperature"))
            if mode in {"off", "heat", "cool", "auto", "dry", "fan_only", "heat_cool"}:
                await self.hass.services.async_call(
                    "climate",
                    "set_hvac_mode",
                    {"entity_id": entity_id, "hvac_mode": mode},
                    blocking=False,
                )
            if temperature is not None:
                await self.hass.services.async_call(
                    "climate",
                    "set_temperature",
                    {"entity_id": entity_id, "temperature": temperature},
                    blocking=False,
                )
        self._manual_baseline = {}

    async def _async_set_input_number_if_needed(
        self,
        entity_id: str | None,
        target: float | None,
        actions: list[str],
    ) -> None:
        """Set an input_number only when the target actually changed."""
        if not entity_id or target is None:
            return
        state = self.hass.states.get(entity_id)
        current = _safe_float(state.state if state else None)
        target_norm = _normalize_ai_input_number_target(target)
        if target_norm is None:
            return
        target_f = float(target_norm)
        if current is not None and abs(current - target_f) < 0.01:
            return
        await self.hass.services.async_call(
            "input_number",
            "set_value",
            {"entity_id": entity_id, "value": target_f},
            blocking=False,
        )
        actions.append(f"{entity_id}: mål justeret til {target_f:.1f}")

    async def _async_set_temperature_if_needed(
        self,
        entity_id: str | None,
        target: float | None,
        actions: list[str],
    ) -> None:
        """Set climate temperature only when needed."""
        if not entity_id or target is None:
            return
        target_f = float(target)
        is_qlima_heat_pump = entity_id.startswith("climate.qlima_")
        if is_qlima_heat_pump:
            target_f = float(round(target_f))
        pending = self._cycle_temperature_commands.get(entity_id)
        compare_margin = 0.49 if is_qlima_heat_pump else 0.05
        if pending is not None and abs(pending - target_f) < compare_margin:
            return
        recent = self._recent_temperature_commands.get(entity_id)
        now_ts = dt_util.utcnow().timestamp()
        recent_retry_cooldown_s = 90.0
        if (
            recent
            and abs(recent[0] - target_f) < compare_margin
            and (now_ts - float(recent[1])) < recent_retry_cooldown_s
        ):
            return
        state = self.hass.states.get(entity_id)
        attrs = state.attributes if state else {}
        current = _safe_float(attrs.get("temperature"))
        if current is not None and abs(current - target_f) < compare_margin:
            self._cycle_temperature_commands[entity_id] = target_f
            return
        await self.hass.services.async_call(
            "climate",
            "set_temperature",
            {"entity_id": entity_id, "temperature": target_f},
            blocking=True,
        )
        self._cycle_temperature_commands[entity_id] = target_f
        self._recent_temperature_commands[entity_id] = (target_f, now_ts)
        actions.append(f"{entity_id}: temperatur sat til {target_f:.1f}°C")

    async def _async_set_hvac_mode_if_needed(
        self,
        entity_id: str | None,
        mode: HVACMode | str | None,
        actions: list[str],
    ) -> None:
        """Set climate HVAC mode only when it changed."""
        if not entity_id or mode is None:
            return
        target_mode = str(mode.value if isinstance(mode, HVACMode) else mode).lower()
        pending = self._cycle_hvac_commands.get(entity_id)
        if pending == target_mode:
            return
        recent = self._recent_hvac_commands.get(entity_id)
        now_ts = dt_util.utcnow().timestamp()
        recent_retry_cooldown_s = 90.0
        if (
            recent
            and recent[0] == target_mode
            and (now_ts - float(recent[1])) < recent_retry_cooldown_s
        ):
            return
        state = self.hass.states.get(entity_id)
        current_mode = str(state.state if state else "").lower()
        if current_mode == target_mode:
            self._cycle_hvac_commands[entity_id] = target_mode
            return
        await self.hass.services.async_call(
            "climate",
            "set_hvac_mode",
            {"entity_id": entity_id, "hvac_mode": target_mode},
            blocking=True,
        )
        self._cycle_hvac_commands[entity_id] = target_mode
        self._recent_hvac_commands[entity_id] = (target_mode, now_ts)
        actions.append(f"{entity_id}: hvac mode sat til {target_mode}")

    def _resolve_preferred_fan_mode(
        self,
        entity_id: str,
        preferred: str,
    ) -> str | None:
        state = self.hass.states.get(entity_id)
        if not state:
            return None
        modes_raw = state.attributes.get("fan_modes")
        if not isinstance(modes_raw, list):
            return None
        available = [str(m).lower() for m in modes_raw if str(m).strip()]
        if not available:
            return None

        pref = str(preferred or "").strip().lower()
        if pref == "off":
            return None
        if pref in available:
            return pref

        candidates_map = {
            "auto": ["auto", "medium", "mid", "high", "max", "turbo", "powerful"],
            "medium": ["medium", "mid", "med", "high", "auto", "max", "turbo"],
            "high": ["high", "max", "turbo", "powerful", "medium"],
            "max": ["max", "turbo", "powerful", "high", "medium"],
        }
        for cand in candidates_map.get(pref, []):
            if cand in available:
                return cand
        return None

    async def _async_set_fan_mode_if_needed(
        self,
        entity_id: str | None,
        fan_mode: str | None,
        actions: list[str],
    ) -> None:
        if not entity_id or not fan_mode:
            return
        target = str(fan_mode).lower()
        pending = self._cycle_fan_commands.get(entity_id)
        if pending == target:
            return
        recent = self._recent_fan_commands.get(entity_id)
        now_ts = dt_util.utcnow().timestamp()
        if recent and recent[0] == target and (now_ts - float(recent[1])) < 90.0:
            return

        state = self.hass.states.get(entity_id)
        current = str((state.attributes if state else {}).get("fan_mode", "")).lower()
        if current == target:
            self._cycle_fan_commands[entity_id] = target
            return

        await self.hass.services.async_call(
            "climate",
            "set_fan_mode",
            {"entity_id": entity_id, "fan_mode": target},
            blocking=True,
        )
        self._cycle_fan_commands[entity_id] = target
        self._recent_fan_commands[entity_id] = (target, now_ts)
        actions.append(f"{entity_id}: fan mode sat til {target}")

    def _compute_heating_mode_from_rooms(self, rooms: list[RoomSnapshot]) -> str:
        """Summarize current house heating mode from room activity."""
        hp_active = False
        rad_active = False
        for room in rooms:
            active = set(room.active_heat_entities or [])
            if room.heat_pump and room.heat_pump in active:
                hp_active = True
            if set(room.radiators or []).intersection(active):
                rad_active = True
        if hp_active and rad_active:
            return "Mix"
        if hp_active:
            return "AC"
        if rad_active:
            return "Gas"
        return "Klar"

    def _append_analytics_sample(
        self,
        *,
        now_ts: float,
        mode: str,
        el_price: float | None,
        gas_price: float | None,
        district_heat_price: float | None,
        gas_consumption: float | None,
        district_heat_consumption: float | None,
    ) -> None:
        """Append one analytics sample and keep a rolling 7-day window."""
        self._analytics_samples.append(
            {
                "ts": float(now_ts),
                "mode": str(mode or "Klar"),
                "el_price": _safe_float(el_price),
                "gas_price": _safe_float(gas_price),
                "district_heat_price": _safe_float(district_heat_price),
                "gas_consumption": _safe_float(gas_consumption),
                "district_heat_consumption": _safe_float(district_heat_consumption),
            }
        )
        cutoff = float(now_ts) - (7 * 24 * 60 * 60)
        self._analytics_samples = [
            row for row in self._analytics_samples
            if isinstance(row, dict) and _safe_float(row.get("ts")) is not None and float(row["ts"]) >= cutoff
        ]

    def _build_period_summary(self, start_ts: float, end_ts: float, decimals: int) -> dict[str, Any]:
        """Build a lightweight operating summary for a period."""
        rows = [
            row for row in self._analytics_samples
            if isinstance(row, dict)
            and _safe_float(row.get("ts")) is not None
            and float(start_ts) <= float(row["ts"]) < float(end_ts)
        ]
        mode_hours = {"AC": 0.0, "Gas": 0.0, "Mix": 0.0, "Klar": 0.0}
        if rows:
            span_hours = max(0.0, (float(end_ts) - float(start_ts)) / 3600.0)
            per_sample = span_hours / max(len(rows), 1)
            for row in rows:
                mode = str(row.get("mode", "Klar"))
                if mode not in mode_hours:
                    mode = "Klar"
                mode_hours[mode] += per_sample

        def _avg(key: str) -> float | None:
            values = [_safe_float(row.get(key)) for row in rows]
            clean = [float(v) for v in values if v is not None]
            if not clean:
                return None
            return round(sum(clean) / len(clean), decimals)

        gas_vals = [_safe_float(row.get("gas_consumption")) for row in rows]
        dh_vals = [_safe_float(row.get("district_heat_consumption")) for row in rows]
        gas_total = round(sum(float(v) for v in gas_vals if v is not None), decimals)
        dh_total = round(sum(float(v) for v in dh_vals if v is not None), decimals)
        avg_prices = {
            "el": _avg("el_price"),
            "gas": _avg("gas_price"),
            "fjernvarme": _avg("district_heat_price"),
        }
        cost = {
            "gas": round(gas_total * float(avg_prices["gas"] or 0.0), decimals),
            "fjernvarme": round(dh_total * float(avg_prices["fjernvarme"] or 0.0), decimals),
        }
        return {
            "mode_hours": {k: round(v, 1) for k, v in mode_hours.items()},
            "avg_prices": avg_prices,
            "consumption": {
                "gas": gas_total,
                "fjernvarme": dh_total,
            },
            "cost": cost,
            "sample_count": len(rows),
        }

    def _build_room_state_payload(self, room: RoomSnapshot, decimals: int) -> dict[str, Any]:
        """Serialize room state for sensors, reports, and cards."""
        heat_pump_state = None
        heat_pump_internal_temp = None
        if room.heat_pump:
            hp_state = self.hass.states.get(room.heat_pump)
            if hp_state:
                heat_pump_state = hp_state.state
                heat_pump_internal_temp = _safe_float(
                    hp_state.attributes.get("current_temperature")
                    or hp_state.attributes.get("current_temp")
                    or hp_state.attributes.get("temperature")
                )

        occupancy_last_change = _fmt_ts(self._room_runtime.get(room.name, {}).get("room_occupancy_last_change"))
        boost_until = _fmt_ts(room.boost_until_ts)
        return {
            "name": room.name,
            "sensor_entity": room.sensor_entity,
            "humidity_sensor_entity": room.humidity_sensor_entity,
            "humidity": round(room.humidity, 1) if room.humidity is not None else None,
            "comfort_band": room.comfort_band,
            "comfort_target": round(room.comfort_target, decimals),
            "comfort_offset_c": round(room.comfort_offset_c, 2),
            "comfort_gap": round(room.comfort_gap, decimals),
            "effective_gap": round(max(room.deficit, room.comfort_gap), decimals),
            "temperature": round(room.temperature, decimals),
            "temperature_raw": round(room.raw_temperature, decimals),
            "target": round(room.target, decimals),
            "eco_target": round(room.eco_target, decimals),
            "deficit": round(room.deficit, decimals),
            "surplus": round(room.surplus, decimals),
            "opening_active": bool(room.opening_active),
            "occupancy_active": bool(room.occupancy_active),
            "occupancy_last_change": occupancy_last_change,
            "occupancy_source_fallback": bool(self._room_runtime.get(room.name, {}).get("occupancy_source_fallback", False)),
            "occupancy_unavailable_sensors": list(self._room_runtime.get(room.name, {}).get("occupancy_unavailable_sensors", [])),
            "presence_eco_enabled": bool(room.presence_eco_enabled),
            "learning_enabled": bool(room.learning_enabled),
            "opening_pause_enabled": bool(room.opening_pause_enabled),
            "room_enabled": bool(room.room_enabled),
            "presence_away_min": round(room.presence_away_min, 1),
            "presence_return_min": round(room.presence_return_min, 1),
            "boost_active": bool(room.boost_active),
            "boost_delta_c": round(room.boost_delta_c, decimals),
            "boost_duration_min": round(room.boost_duration_min, 1),
            "boost_until": boost_until,
            "target_number_entity": room.target_number_entity,
            "heat_pump": room.heat_pump,
            "heat_pump_state": heat_pump_state,
            "heat_pump_power_sensor": room.heat_pump_power_sensor,
            "heat_pump_power_w": round(room.heat_pump_power_w, 1) if room.heat_pump_power_w is not None else None,
            "heat_pump_internal_temp": round(heat_pump_internal_temp, decimals) if heat_pump_internal_temp is not None else None,
            "heat_pump_internal_bias_c": None if heat_pump_internal_temp is None else round(room.temperature - heat_pump_internal_temp, decimals),
            "radiators": list(room.radiators),
            "link_group": room.link_group,
            "anti_short_cycle_min": round(room.anti_short_cycle_min, 1),
            "quick_start_deficit_c": round(room.quick_start_deficit_c, decimals),
            "start_deficit_c": round(room.start_deficit_c, decimals),
            "stop_surplus_c": round(room.stop_surplus_c, decimals),
            "pause_after_open_min": round(room.pause_after_open_min, 1),
            "resume_after_closed_min": round(room.resume_after_closed_min, 1),
            "massive_overheat_c": round(room.massive_overheat_c, decimals),
            "massive_overheat_min": round(room.massive_overheat_min, 1),
            "active_heat_entities": list(room.active_heat_entities),
            "active_heat_names": list(room.active_heat_names),
            "active_heat_summary": room.active_heat_summary,
            "is_heating_now": bool(room.is_heating_now),
            "control_entities": [x for x in [room.heat_pump, room.target_number_entity, *room.radiators] if x],
            "eco_active": bool(self._room_runtime.get(room.name, {}).get("eco_active", False)),
        }

    def _build_room_analysis(self, room: RoomSnapshot, decimals: int) -> dict[str, Any]:
        """Create a compact, user-facing room analysis."""
        effective_gap = max(float(room.comfort_gap), float(room.deficit))
        status = "stabil"
        recommendation = "Ingen ændring nødvendig."
        if room.opening_active:
            status = "pause"
            recommendation = "Afvent lukket åbning før yderligere varme."
        elif effective_gap >= max(0.3, room.quick_start_deficit_c) and not room.is_heating_now:
            status = "koldt_uden_varme"
            recommendation = "Bør prioriteres til varme nu."
        elif effective_gap > 0.05 and room.is_heating_now:
            status = "under_maal_men_varmer"
            recommendation = "Lad nuværende varme arbejde færdig."
        elif effective_gap > 0.05:
            status = "under_maal"
            recommendation = "Let varmebehov."
        elif room.surplus > 0.5:
            status = "over_maal"
            recommendation = "Undgå yderligere opvarmning."
        elif room.comfort_band == "tør" and room.surplus > 0.2:
            status = "tor_men_varm"
            recommendation = "Ingen ekstra varme; tør luft bør håndteres uden at hæve temperaturen."
        elif room.comfort_band == "fugtig" and room.surplus <= 0.2:
            status = "fugtig"
            recommendation = "Hold temperaturen rolig; fugtig luft kan få rummet til at føles tungere."
        elif room.comfort_band == "tør" and effective_gap <= 0.05:
            status = "tor_men_stabil"
            recommendation = "Temperaturen er fin, men tør luft kan stadig påvirke komforten."

        humidity_note = "ingen fugtdata"
        if room.humidity is not None:
            humidity_note = f"{room.humidity:.0f}% ({room.comfort_band})"

        if room.deficit > 0.05:
            thermal_note = f"{room.deficit:.{decimals}f}°C under mål"
        elif room.surplus > 0.05:
            thermal_note = f"{room.surplus:.{decimals}f}°C over mål"
        else:
            thermal_note = "tæt på mål"

        comfort_note = ""
        if room.comfort_gap > room.deficit + 0.1:
            comfort_note = f", oplevet komfortgap ca. {room.comfort_gap:.{decimals}f}°C"
        elif room.comfort_band == "tør" and room.surplus > 0.2:
            comfort_note = ", tør luft kan få rummet til at føles mindre behageligt trods varmeoverskud"
        elif room.comfort_band == "fugtig":
            comfort_note = ", høj fugt kan få rummet til at føles tungere end temperaturen antyder"

        summary = (
            f"{room.name}: {thermal_note}, fugt {humidity_note}, varme: {room.active_heat_summary.lower()}{comfort_note}."
        )
        return {
            "name": room.name,
            "status": status,
            "summary": summary,
            "recommendation": recommendation,
            "temperature": round(room.temperature, decimals),
            "target": round(room.target, decimals),
            "deficit": round(room.deficit, decimals),
            "effective_gap": round(effective_gap, decimals),
            "surplus": round(room.surplus, decimals),
            "humidity": round(room.humidity, 1) if room.humidity is not None else None,
            "comfort_band": room.comfort_band,
            "comfort_target": round(room.comfort_target, decimals),
            "comfort_gap": round(room.comfort_gap, decimals),
            "is_heating_now": bool(room.is_heating_now),
            "active_heat_summary": room.active_heat_summary,
        }

    def _build_report(
        self,
        *,
        ai_provider: str,
        ai_primary_engine: str,
        ai_fallback_engine: str,
        ai_report_engine: str,
        ai_decision_source: str,
        ai_model_fast: str,
        ai_model_report: str,
        provider_ready: bool,
        flow_limited: bool,
        heat_pump_cheaper: bool,
        cheapest_alt_name: str,
        estimated_savings_per_kwh: float | None,
        estimated_daily_savings: float | None,
        ai_report_text: str,
        openclaw_model_preferred: str,
        openclaw_model_fallback: str,
        rooms: list[RoomSnapshot],
        actions: list[str],
        decimals: int,
    ) -> dict[str, Any]:
        """Build report text and bullets for cards."""
        bullets: list[str] = []
        room_analyses = [self._build_room_analysis(room, decimals) for room in rooms]
        cold_rooms = [r for r in rooms if max(r.deficit, r.comfort_gap) > 0.05]
        if cold_rooms:
            for room in cold_rooms:
                effective_gap = max(room.deficit, room.comfort_gap)
                if room.deficit > 0.05:
                    line = f"{room.name}: {room.deficit:.{decimals}f}°C under mål"
                else:
                    line = f"{room.name}: tæt på mål men oplevet komfortgap ca. {effective_gap:.{decimals}f}°C"
                if room.humidity is not None:
                    line += f", fugt {room.humidity:.0f}% ({room.comfort_band})"
                    if room.comfort_gap > room.deficit + 0.05:
                        line += f", opleves som ca. {room.comfort_gap:.{decimals}f}°C fra komfortmål"
                if room.is_heating_now:
                    line += ", varme aktiv"
                else:
                    line += ", mangler aktiv varme"
                bullets.append(line)
        else:
            bullets.append("Alle rum er tæt på måltemperatur.")

        for room in rooms:
            if room not in cold_rooms:
                line = f"{room.name}: {room.surplus:.{decimals}f}°C over mål" if room.surplus > 0.05 else f"{room.name}: stabil"
                if room.humidity is not None:
                    line += f", fugt {room.humidity:.0f}% ({room.comfort_band})"
                bullets.append(line)

        bullets.append("Rumvurdering:")
        bullets.extend(
            f"- {analysis['summary']} {analysis['recommendation']}"
            for analysis in room_analyses[:12]
        )

        if flow_limited:
            bullets.append("Flowbegrænsning er aktiv lige nu.")
        if estimated_savings_per_kwh is not None:
            bullets.append(
                f"Estimeret besparelse: {float(estimated_savings_per_kwh):.{min(decimals,3)}f} kr/kWh"
            )
        if estimated_daily_savings is not None:
            bullets.append(f"Estimeret dagsbesparelse: {float(estimated_daily_savings):.{decimals}f} kr")
        if heat_pump_cheaper:
            bullets.append("Billigste varmevalg nu: Varmepumpe")
        elif cheapest_alt_name:
            bullets.append(f"Billigste varmevalg nu: {cheapest_alt_name}")
        if cheapest_alt_name:
            bullets.append(f"Billigste alternativ til varmepumpe: {cheapest_alt_name}")
        bullets.append(
            "Varmepumpe billigst: "
            + ("Ja" if heat_pump_cheaper else "Nej")
        )
        if actions:
            bullets.extend(str(a) for a in actions[-5:])

        short = (
            ai_report_text.strip()
            if str(ai_report_text or "").strip()
            else f"Beslutningsmotor: {_ai_provider_display(ai_primary_engine)} | AI-kilde nu: {_ai_decision_source_display(ai_decision_source)}"
        )
        requested_openclaw_model = openclaw_model_preferred or DEFAULT_OPENCLAW_MODEL_PREFERRED
        fallback_openclaw_model = openclaw_model_fallback or DEFAULT_OPENCLAW_MODEL_FALLBACK
        actual_openclaw_model = ""
        if isinstance(self._ai_structured_decision, dict):
            meta_model = self._ai_structured_decision.get("_openclaw_meta", {}).get("actual_model") if isinstance(self._ai_structured_decision.get("_openclaw_meta", {}), dict) else None
            if isinstance(meta_model, str):
                actual_openclaw_model = meta_model.strip()
        long_lines = [
            f"Beslutningsmotor: {_ai_provider_display(ai_primary_engine)}",
            f"AI-kilde nu: {_ai_decision_source_display(ai_decision_source)}",
            f"Fallback-motor: {_ai_provider_display(ai_fallback_engine)}",
            f"Rapportmotor: {_ai_provider_display(ai_report_engine)}",
            f"Hurtig model: {_ai_provider_display(ai_model_fast) if ai_report_engine == AI_PRIMARY_ENGINE_OPENCLAW else ai_model_fast}",
            f"Rapport model: {_ai_provider_display(ai_model_report) if ai_report_engine == AI_PRIMARY_ENGINE_OPENCLAW else ai_model_report}",
            f"OpenClaw foretrukken model: {requested_openclaw_model}",
            f"OpenClaw fallback-model: {fallback_openclaw_model}",
            f"OpenClaw aktiv model: {actual_openclaw_model or requested_openclaw_model}",
            f"Provider klar: {'Ja' if provider_ready else 'Nej'}",
        ]
        if str(ai_report_text or "").strip():
            long_lines.extend(["", str(ai_report_text).strip()])
        else:
            long_lines.extend(["", "Omhandler:"])
            long_lines.extend(f"- {item}" for item in bullets[:40])
        return {
            "short": short,
            "long": "\n".join(long_lines),
            "bullets": bullets[:40],
            "room_analyses": room_analyses,
            "meta": {
                "provider": ai_provider,
                "primary_engine": ai_primary_engine,
                "fallback_engine": ai_fallback_engine,
                "report_engine": ai_report_engine,
                "decision_source": ai_decision_source,
                "heat_pump_cheaper": bool(heat_pump_cheaper),
            },
        }

    async def _async_update_data(self) -> dict[str, Any]:
        previous_data = dict(self.data) if isinstance(self.data, dict) else {}
        try:
            self._cycle_temperature_commands = {}
            self._cycle_hvac_commands = {}
            self._cycle_fan_commands = {}
            try:
                OPENCLAW_RUNTIME_ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
                with OPENCLAW_RUNTIME_ERROR_LOG.open("a", encoding="utf-8") as fh:
                    row = {"stage": "update_start", "entry_id": self.entry.entry_id, "has_previous_data": bool(previous_data)}
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            except Exception:
                pass
            await self._async_load_runtime()
            cfg = {**self.entry.data, **self.entry.options}
            runtime = self.hass.data[DOMAIN][self.entry.entry_id]
            now = dt_util.utcnow()
            now_ts = now.timestamp()
            startup_refresh = self.data is None
            
            decimals = int(cfg.get(CONF_DECIMALS, DEFAULT_DECIMALS))
            enabled = bool(runtime.get(RUNTIME_ENABLED, True))
            global_target = float(runtime.get(RUNTIME_GLOBAL_TARGET, 22.0))
            eco_target = float(runtime.get(RUNTIME_ECO_TARGET, 20.0))
            presence_eco_enabled = bool(
                runtime.get(
                    RUNTIME_PRESENCE_ECO_ENABLED,
                    cfg.get(CONF_ENABLE_PRESENCE_ECO, False),
                )
            )
            pid_enabled = bool(
                runtime.get(
                    RUNTIME_PID_LAYER_ENABLED,
                    cfg.get(CONF_ENABLE_PID_LAYER, False),
                )
            )
            learning_enabled = bool(
                runtime.get(
                    RUNTIME_LEARNING_ENABLED,
                    cfg.get(CONF_ENABLE_LEARNING, DEFAULT_ENABLE_LEARNING),
                )
            )
            comfort_mode_enabled = bool(runtime.get(RUNTIME_COMFORT_MODE_ENABLED, False))
            decision_interval_min = float(
                runtime.get(
                    RUNTIME_AI_DECISION_INTERVAL_MIN,
                    cfg.get(CONF_AI_DECISION_INTERVAL_MIN, DEFAULT_AI_DECISION_INTERVAL_MIN),
                )
            )
            report_interval_min = float(
                runtime.get(
                    RUNTIME_REPORT_INTERVAL_MIN,
                    cfg.get(CONF_REPORT_INTERVAL_MIN, DEFAULT_REPORT_INTERVAL_MIN),
                )
            )
            pid_kp = float(runtime.get(RUNTIME_PID_KP, cfg.get(CONF_PID_KP, DEFAULT_PID_KP)))
            pid_ki = float(runtime.get(RUNTIME_PID_KI, cfg.get(CONF_PID_KI, DEFAULT_PID_KI)))
            pid_kd = float(runtime.get(RUNTIME_PID_KD, cfg.get(CONF_PID_KD, DEFAULT_PID_KD)))
            pid_deadband_c = float(
                runtime.get(RUNTIME_PID_DEADBAND_C, cfg.get(CONF_PID_DEADBAND_C, DEFAULT_PID_DEADBAND_C))
            )
            pid_integral_limit = float(
                runtime.get(
                    RUNTIME_PID_INTEGRAL_LIMIT,
                    cfg.get(CONF_PID_INTEGRAL_LIMIT, DEFAULT_PID_INTEGRAL_LIMIT),
                )
            )
            pid_offset_max_c = float(
                runtime.get(RUNTIME_PID_OFFSET_MAX_C, cfg.get(CONF_PID_OFFSET_MAX_C, DEFAULT_PID_OFFSET_MAX_C))
            )
            confidence_threshold = float(
                runtime.get(
                    RUNTIME_CONFIDENCE_THRESHOLD,
                    cfg.get(CONF_CONFIDENCE_THRESHOLD, DEFAULT_CONFIDENCE_THRESHOLD),
                )
            )
            revert_timeout_min = float(
                runtime.get(
                    RUNTIME_REVERT_TIMEOUT_MIN,
                    cfg.get(CONF_REVERT_TIMEOUT_MIN, DEFAULT_REVERT_TIMEOUT_MIN),
                )
            )
            
            ai_provider = str(cfg.get(CONF_AI_PROVIDER, DEFAULT_AI_PROVIDER)).strip().lower()
            ai_primary_engine_raw = str(
                cfg.get(CONF_AI_PRIMARY_ENGINE, DEFAULT_AI_PRIMARY_ENGINE)
            )
            ai_fallback_engine = str(
                cfg.get(CONF_AI_FALLBACK_ENGINE, DEFAULT_AI_FALLBACK_ENGINE)
            ).strip().lower()
            ai_report_engine = str(
                cfg.get(CONF_AI_REPORT_ENGINE, DEFAULT_AI_REPORT_ENGINE)
            ).strip().lower()
            ai_primary_engine = _normalize_primary_engine(ai_primary_engine_raw, ai_provider)
            if ai_provider == AI_PROVIDER_GEMINI:
                ai_model_fast = str(cfg.get(CONF_GEMINI_MODEL_FAST, "gemini-2.5-flash"))
                ai_model_report = str(cfg.get(CONF_GEMINI_MODEL_REPORT, "gemini-2.5-pro"))
                provider_endpoint = "gemini"
                provider_api_key = str(cfg.get(CONF_GEMINI_API_KEY, "")).strip()
                provider_ready = bool(provider_api_key)
            else:
                ai_model_fast = str(cfg.get(CONF_AI_MODEL_FAST, DEFAULT_AI_MODEL_FAST))
                ai_model_report = str(cfg.get(CONF_AI_MODEL_REPORT, DEFAULT_AI_MODEL_REPORT))
                provider_endpoint = str(cfg.get(CONF_OLLAMA_HOST, "")).strip()
                provider_api_key = ""
                provider_ready = bool(provider_endpoint)
            openclaw_enabled = bool(cfg.get(CONF_OPENCLAW_ENABLED, DEFAULT_OPENCLAW_ENABLED))
            openclaw_bridge_url = str(cfg.get(CONF_OPENCLAW_BRIDGE_URL, DEFAULT_OPENCLAW_BRIDGE_URL)).strip()
            openclaw_url = str(cfg.get(CONF_OPENCLAW_URL, DEFAULT_OPENCLAW_URL)).strip()
            openclaw_token = str(cfg.get(CONF_OPENCLAW_TOKEN, "")).strip()
            openclaw_password = str(cfg.get(CONF_OPENCLAW_PASSWORD, "")).strip()
            openclaw_timeout_sec = float(
                cfg.get(CONF_OPENCLAW_TIMEOUT_SEC, DEFAULT_OPENCLAW_TIMEOUT_SEC)
            )
            openclaw_model_preferred = str(
                cfg.get(CONF_OPENCLAW_MODEL_PREFERRED, DEFAULT_OPENCLAW_MODEL_PREFERRED)
            ).strip()
            openclaw_model_fallback = str(
                cfg.get(CONF_OPENCLAW_MODEL_FALLBACK, DEFAULT_OPENCLAW_MODEL_FALLBACK)
            ).strip()
            bridge_env = _load_openclaw_bridge_env()
            env_openclaw_url = (
                bridge_env.get("OPENCLAW_URL")
                or os.getenv("OPENCLAW_URL", "")
            ).strip()
            env_openclaw_token = (
                bridge_env.get("OPENCLAW_TOKEN")
                or os.getenv("OPENCLAW_TOKEN", "")
            ).strip()
            env_openclaw_password = (
                bridge_env.get("OPENCLAW_PASSWORD")
                or os.getenv("OPENCLAW_PASSWORD", "")
            ).strip()
            env_openclaw_timeout = (
                bridge_env.get("OPENCLAW_TIMEOUT_SEC")
                or os.getenv("OPENCLAW_TIMEOUT_SEC", "")
            ).strip()
            # Prefer local bridge path when configured or empty.
            # In this runtime, session mounts may be unavailable, while the bridge
            # runs in the same HA context on localhost:18890.
            if not openclaw_bridge_url:
                openclaw_bridge_url = DEFAULT_OPENCLAW_BRIDGE_URL
            if (not openclaw_url) or _is_localhost_http_url(openclaw_url, 18789):
                openclaw_url = env_openclaw_url or "http://homeassistant.local:18789/hooks/agent"
            if not openclaw_token:
                openclaw_token = env_openclaw_token
            if not openclaw_password:
                openclaw_password = env_openclaw_password
            if env_openclaw_timeout:
                with contextlib.suppress(ValueError):
                    openclaw_timeout_sec = max(openclaw_timeout_sec, float(env_openclaw_timeout))
            openclaw_payload_profile = str(
                cfg.get(CONF_OPENCLAW_PAYLOAD_PROFILE, DEFAULT_OPENCLAW_PAYLOAD_PROFILE)
            ).strip().lower()
            provider_payload_profile = str(
                cfg.get(CONF_PROVIDER_PAYLOAD_PROFILE, DEFAULT_PROVIDER_PAYLOAD_PROFILE)
            ).strip().lower()
            if ai_primary_engine == "provider":
                ai_primary_engine = ai_provider
            if ai_fallback_engine == "provider":
                ai_fallback_engine = ai_provider
            if ai_report_engine == "provider":
                ai_report_engine = ai_provider
            use_openclaw_path = bool(
                openclaw_enabled
                or ai_primary_engine == AI_PRIMARY_ENGINE_OPENCLAW
                or ai_fallback_engine == AI_PRIMARY_ENGINE_OPENCLAW
                or ai_report_engine == AI_PRIMARY_ENGINE_OPENCLAW
            )
            openclaw_ready = bool(
                use_openclaw_path and (openclaw_bridge_url or openclaw_url)
            )
            openclaw_only_mode = bool(
                cfg.get(CONF_OPENCLAW_ONLY_MODE, DEFAULT_OPENCLAW_ONLY_MODE)
            )
            decision_engines = [ai_primary_engine]
            if ai_fallback_engine not in {"", AI_ENGINE_NONE} and ai_fallback_engine not in decision_engines:
                decision_engines.append(ai_fallback_engine)
            engine_ready_map = {
                AI_PRIMARY_ENGINE_OPENCLAW: openclaw_ready,
                AI_PROVIDER_OLLAMA: bool(provider_endpoint) if ai_provider == AI_PROVIDER_OLLAMA else bool(
                    str(cfg.get(CONF_OLLAMA_HOST, "")).strip()
                ),
                AI_PROVIDER_GEMINI: bool(str(cfg.get(CONF_GEMINI_API_KEY, "")).strip()),
            }
            report_provider_ready = bool(
                ai_report_engine == AI_PRIMARY_ENGINE_OPENCLAW
                or engine_ready_map.get(ai_report_engine, provider_ready)
            )
            if openclaw_only_mode:
                decision_engines = [AI_PRIMARY_ENGINE_OPENCLAW]
                ai_fallback_engine = AI_ENGINE_NONE
                report_provider_ready = openclaw_ready
            ai_provider_ready = any(bool(engine_ready_map.get(engine, False)) for engine in decision_engines)
            
            if openclaw_bridge_url and _minutes_since(self._last_bridge_stats_update, now_ts) >= 1.0:
                try:
                    await self._async_fetch_bridge_stats(openclaw_bridge_url)
                except Exception as err:  # noqa: BLE001
                    LOGGER.debug("Bridge stats fetch failed: %s", err)
            openclaw_runtime_status = {
                "results_file": _runtime_file_status(OPENCLAW_COMPLETION_RESULTS_CANDIDATES[0], now_ts),
                "completion_worker_log": _runtime_file_status(OPENCLAW_COMPLETION_WORKER_LOG, now_ts),
                "bridge_log": _runtime_file_status(OPENCLAW_BRIDGE_LOG, now_ts),
                "services_ensure_log": _runtime_file_status(OPENCLAW_SERVICES_ENSURE_LOG, now_ts),
            }
            openclaw_runtime_health = _openclaw_runtime_health(openclaw_runtime_status)
            
            vacuum_entity: str | None = cfg.get(CONF_VACUUM_ENTITY)
            vacuum_running = (
                self.hass.states.get(vacuum_entity).state == "cleaning"
                if vacuum_entity and self.hass.states.get(vacuum_entity)
                else False
            )
            
            rooms_cfg: list[dict[str, Any]] = list(cfg.get(CONF_ROOMS, []))
            rooms_cfg = await self._async_selfheal_room_target_helpers(rooms_cfg, now_ts)
            occupancy_global = False
            for room_cfg in rooms_cfg:
                for sensor in room_cfg.get(CONF_ROOM_OCCUPANCY_SENSORS, []):
                    st = self.hass.states.get(sensor)
                    if st and _is_on(st.state):
                        occupancy_global = True
                        break
                if occupancy_global:
                    break
            
            presence_away_min = float(
                runtime.get(
                    RUNTIME_PRESENCE_AWAY_MIN,
                    cfg.get(CONF_PRESENCE_AWAY_MIN, DEFAULT_PRESENCE_AWAY_MIN),
                )
            )
            presence_return_min = float(
                runtime.get(
                    RUNTIME_PRESENCE_RETURN_MIN,
                    cfg.get(CONF_PRESENCE_RETURN_MIN, DEFAULT_PRESENCE_RETURN_MIN),
                )
            )
            presence_state = self._room_runtime.setdefault(
                "__presence__",
                {
                    "eco_forced": False,
                    "empty_since": None,
                    "occupied_since": None,
                    "last_change": None,
                },
            )
            occupied_now = occupancy_global and not vacuum_running
            if occupied_now:
                presence_state["empty_since"] = None
                if presence_state["occupied_since"] is None:
                    presence_state["occupied_since"] = now_ts
                if presence_state.get("eco_forced") and _minutes_since(presence_state["occupied_since"], now_ts) >= presence_return_min:
                    presence_state["eco_forced"] = False
                    presence_state["last_change"] = now_ts
            else:
                presence_state["occupied_since"] = None
                if presence_state["empty_since"] is None:
                    presence_state["empty_since"] = now_ts
                if (not presence_state.get("eco_forced")) and _minutes_since(presence_state["empty_since"], now_ts) >= presence_away_min:
                    presence_state["eco_forced"] = True
                    presence_state["last_change"] = now_ts
            
            presence_eco_active = bool(presence_eco_enabled and presence_state.get("eco_forced"))
            # Keep room control target local to each room. Global presence eco is informational
            # and must not pull all rooms down to eco target.
            target_base = global_target
            
            rooms: list[RoomSnapshot] = []
            unavailable = 0
            for idx, room_cfg in enumerate(rooms_cfg):
                name = str(room_cfg.get(CONF_ROOM_NAME) or f"Rum {idx + 1}")
                room_rt = self._room_runtime.setdefault(name, {})
                temp_entity = _resolve_room_temp_sensor_entity(
                    self.hass, name, room_cfg.get(CONF_ROOM_TEMP_SENSOR)
                )
                if not temp_entity:
                    unavailable += 1
                    continue
                st = self.hass.states.get(temp_entity)
                raw_temp = _safe_float(st.state if st else None)
                if raw_temp is None:
                    unavailable += 1
                    continue
            
                bias = float(
                    room_rt.get(
                        "sensor_bias_override",
                        room_cfg.get(CONF_ROOM_SENSOR_BIAS_C, DEFAULT_ROOM_SENSOR_BIAS_C),
                    )
                )
                adj_temp = raw_temp - bias
            
                target = target_base
                tgt_number = _resolve_room_target_number_entity(
                    self.hass, name, room_cfg.get(CONF_ROOM_TARGET_NUMBER)
                )
                if tgt_number:
                    tgt_state = self.hass.states.get(tgt_number)
                    tgt = _safe_float(tgt_state.state if tgt_state else None)
                    if tgt is not None:
                        lock_rt = self._room_runtime.setdefault(
                            f"__target_lock__{name}",
                            {"locked_target": tgt, "last_seen_target": tgt},
                        )
                        locked_target = _safe_float(lock_rt.get("locked_target"))
                        if locked_target is None:
                            locked_target = tgt
                            lock_rt["locked_target"] = tgt
                        last_seen_target = _safe_float(lock_rt.get("last_seen_target"))
                        changed = last_seen_target is None or abs(tgt - last_seen_target) > 0.01
                        if changed:
                            user_change = bool(tgt_state and tgt_state.context and tgt_state.context.user_id)
                            if user_change:
                                lock_rt["locked_target"] = tgt
                                room_rt["target_override"] = tgt
                                room_rt["room_target_last_changed"] = now_ts
                            elif abs(tgt - float(locked_target)) > 0.01:
                                lock_rt["locked_target"] = tgt
                            lock_rt["last_seen_target"] = tgt
                        target = tgt
                target_override = _safe_float(room_rt.get("target_override"))
                if target_override is not None:
                    target = target_override
            
                opening_active = any(
                    _is_on(self.hass.states.get(s).state if self.hass.states.get(s) else None)
                    for s in room_cfg.get(CONF_ROOM_OPENING_SENSORS, [])
                )
                occupancy_sensor_ids = list(room_cfg.get(CONF_ROOM_OCCUPANCY_SENSORS, []))
                occupancy_values: list[bool] = []
                occupancy_unavailable: list[str] = []
                for occ_entity in occupancy_sensor_ids:
                    occ_state_obj = self.hass.states.get(occ_entity)
                    occ_state_raw = str(occ_state_obj.state).lower() if occ_state_obj else "unavailable"
                    if occ_state_raw in {"unknown", "unavailable", "none", ""}:
                        occupancy_unavailable.append(occ_entity)
                        continue
                    occupancy_values.append(_is_on(occ_state_raw))
            
                if occupancy_values:
                    occupancy_active = any(occupancy_values)
                    prev_occ = room_rt.get("last_occupancy_active")
                    if prev_occ is None or bool(prev_occ) != bool(occupancy_active):
                        room_rt["room_occupancy_last_change"] = now_ts
                    room_rt["last_occupancy_active"] = bool(occupancy_active)
                    room_rt["occupancy_source_fallback"] = False
                elif occupancy_sensor_ids:
                    # If configured occupancy sensors are temporarily unavailable, keep last known state.
                    occupancy_active = bool(room_rt.get("last_occupancy_active", False))
                    room_rt["occupancy_source_fallback"] = True
                    if room_rt.get("room_occupancy_last_change") is None:
                        room_rt["room_occupancy_last_change"] = now_ts
                else:
                    # No occupancy sensors configured for this room. Presence should only affect ECO mode,
                    # so remove stale occupancy state instead of carrying an old value forward.
                    occupancy_active = False
                    room_rt["last_occupancy_active"] = False
                    room_rt["occupancy_source_fallback"] = False
                    room_rt["room_occupancy_last_change"] = None
            
                room_rt["occupancy_unavailable_sensors"] = occupancy_unavailable
                room_enabled = bool(room_rt.get("room_enabled_override", True))
                presence_eco_enabled_room = bool(
                    room_rt.get(
                        "presence_eco_enabled_override",
                        room_cfg.get(CONF_ROOM_ENABLE_PRESENCE_ECO, DEFAULT_ROOM_ENABLE_PRESENCE_ECO),
                    )
                )
                eco_target_room = float(room_rt.get("eco_target_override", eco_target))
                away_min_room = float(room_rt.get("presence_away_min_override", presence_away_min))
                return_min_room = float(room_rt.get("presence_return_min_override", presence_return_min))
                boost_until_ts = room_rt.get("boost_until_ts")
                boost_active = isinstance(boost_until_ts, (int, float)) and float(boost_until_ts) > now_ts
                if not boost_active and "boost_until_ts" in room_rt:
                    room_rt.pop("boost_until_ts", None)
                boost_delta_c = float(room_rt.get("boost_delta_c", 1.0))
                boost_duration_min = float(room_rt.get("boost_duration_min", 60.0))
                if boost_active:
                    target = target + boost_delta_c
                learning_enabled_room = bool(
                    room_cfg.get(CONF_ROOM_ENABLE_LEARNING, DEFAULT_ROOM_ENABLE_LEARNING)
                )
                opening_pause_enabled_room = bool(
                    room_rt.get(
                        "opening_pause_enabled_override",
                        room_cfg.get(CONF_ROOM_ENABLE_OPENING_PAUSE, DEFAULT_ROOM_ENABLE_OPENING_PAUSE),
                    )
                )
                pause_after_open_min_room = float(
                    room_rt.get(
                        "pause_after_open_min_override",
                        room_cfg.get(CONF_ROOM_PAUSE_AFTER_OPEN_MIN, DEFAULT_ROOM_PAUSE_AFTER_OPEN_MIN),
                    )
                )
                resume_after_closed_min_room = float(
                    room_rt.get(
                        "resume_after_closed_min_override",
                        room_cfg.get(CONF_ROOM_RESUME_AFTER_CLOSED_MIN, DEFAULT_ROOM_RESUME_AFTER_CLOSED_MIN),
                    )
                )
                heat_pump_power_sensor = _resolve_room_heat_pump_power_sensor_entity(
                    self.hass, name, room_cfg
                )
                heat_pump_power_w = _power_sensor_to_watts(
                    self.hass.states.get(heat_pump_power_sensor) if heat_pump_power_sensor else None
                )
                humidity_enabled = bool(
                    comfort_mode_enabled
                    and cfg.get(CONF_HUMIDITY_COMFORT_ENABLED, DEFAULT_HUMIDITY_COMFORT_ENABLED)
                )
                humidity_dry_threshold = float(cfg.get(CONF_HUMIDITY_DRY_THRESHOLD, DEFAULT_HUMIDITY_DRY_THRESHOLD))
                humidity_humid_threshold = float(cfg.get(CONF_HUMIDITY_HUMID_THRESHOLD, DEFAULT_HUMIDITY_HUMID_THRESHOLD))
                humidity_max_offset_c = float(cfg.get(CONF_HUMIDITY_MAX_OFFSET_C, DEFAULT_HUMIDITY_MAX_OFFSET_C))
                humidity_entity = str(room_cfg.get(CONF_ROOM_HUMIDITY_SENSOR, "") or "").strip() or _resolve_room_humidity_sensor_entity(self.hass, name, temp_entity)
                humidity_raw = _safe_float(self.hass.states.get(humidity_entity).state if humidity_entity and self.hass.states.get(humidity_entity) else None)
                comfort_offset_c = _humidity_comfort_offset_c(
                    humidity_raw,
                    enabled=humidity_enabled,
                    dry_threshold=humidity_dry_threshold,
                    humid_threshold=humidity_humid_threshold,
                    max_offset_c=humidity_max_offset_c,
                )
                comfort_target = target + comfort_offset_c
                comfort_gap = max(comfort_target - adj_temp, 0.0)
                comfort_band = _comfort_band_from_humidity(
                    humidity_raw,
                    enabled=humidity_enabled,
                    dry_threshold=humidity_dry_threshold,
                    humid_threshold=humidity_humid_threshold,
                )
                active_heat_entities: list[str] = []
                active_heat_names: list[str] = []
            
                def _add_active_heat(entity_id: str) -> None:
                    st = self.hass.states.get(entity_id)
                    if not st:
                        return
                    hvac_action = str(st.attributes.get("hvac_action", "")).lower()
                    state = str(st.state).lower()
                    is_active = hvac_action in {"heating", "preheating"} or (state == "heat" and hvac_action == "")
                    if not is_active:
                        return
                    active_heat_entities.append(entity_id)
                    active_heat_names.append(str(st.attributes.get("friendly_name") or entity_id))
            
                heat_pump_entity = room_cfg.get(CONF_ROOM_HEAT_PUMP)
                if heat_pump_entity:
                    _add_active_heat(heat_pump_entity)
                radiator_entities = list(room_cfg.get(CONF_ROOM_RADIATORS, []))
                for rad_entity in radiator_entities:
                    _add_active_heat(rad_entity)
                active_heat_summary = (
                    ", ".join(active_heat_names) if active_heat_names else "Ingen aktiv varmekilde"
                )
            
                room_name_l = str(name or "").strip().lower()
                garage_room = "garage" in room_name_l or "garagen" in room_name_l
                configured_quick_start = room_cfg.get(CONF_ROOM_QUICK_START_DEFICIT_C)
                if garage_room and configured_quick_start is not None and float(configured_quick_start) == DEFAULT_ROOM_QUICK_START_DEFICIT_C:
                    quick_start_deficit_c = DEFAULT_GARAGE_ROOM_QUICK_START_DEFICIT_C
                else:
                    quick_start_deficit_c = float(
                        configured_quick_start
                        if configured_quick_start is not None
                        else (DEFAULT_GARAGE_ROOM_QUICK_START_DEFICIT_C if garage_room else DEFAULT_ROOM_QUICK_START_DEFICIT_C)
                    )

                configured_start_deficit = room_cfg.get(CONF_ROOM_START_DEFICIT_C)
                base_start_deficit = cfg.get(CONF_START_DEFICIT_C, DEFAULT_ROOM_START_DEFICIT_C)
                if garage_room and configured_start_deficit is not None and float(configured_start_deficit) == DEFAULT_ROOM_START_DEFICIT_C:
                    start_deficit_c = DEFAULT_GARAGE_ROOM_START_DEFICIT_C
                else:
                    start_deficit_c = float(
                        configured_start_deficit
                        if configured_start_deficit is not None
                        else (DEFAULT_GARAGE_ROOM_START_DEFICIT_C if garage_room else base_start_deficit)
                    )

                adjacent_rooms_cfg = room_cfg.get(CONF_ROOM_ADJACENT_ROOMS, [])
                if not isinstance(adjacent_rooms_cfg, list):
                    adjacent_rooms_cfg = []
                adjacent_rooms = [
                    str(x).strip() for x in adjacent_rooms_cfg if str(x).strip() and str(x).strip() != name
                ]
                room_direction_bias = float(
                    room_cfg.get(
                        CONF_ROOM_HEAT_SOURCE_DIRECTION_BIAS,
                        cfg.get(
                            CONF_HEAT_SOURCE_DIRECTION_BIAS,
                            DEFAULT_ROOM_HEAT_SOURCE_DIRECTION_BIAS,
                        ),
                    )
                )
                room_direction_bias = max(-2.0, min(2.0, room_direction_bias))
                room_setback_extra = float(
                    room_cfg.get(
                        CONF_ROOM_CHEAP_POWER_RADIATOR_SETBACK_EXTRA_C,
                        cfg.get(
                            CONF_CHEAP_POWER_RADIATOR_SETBACK_EXTRA_C,
                            DEFAULT_ROOM_CHEAP_POWER_RADIATOR_SETBACK_EXTRA_C,
                        ),
                    )
                )
                room_setback_extra = max(0.0, min(4.0, room_setback_extra))

                rooms.append(
                    RoomSnapshot(
                        name=name,
                        sensor_entity=temp_entity,
                        humidity_sensor_entity=humidity_entity,
                        raw_temperature=raw_temp,
                        humidity=humidity_raw,
                        temperature=adj_temp,
                        target=target,
                        comfort_target=comfort_target,
                        comfort_offset_c=comfort_offset_c,
                        comfort_gap=comfort_gap,
                        comfort_band=comfort_band,
                        deficit=max(target - adj_temp, 0.0),
                        surplus=max(adj_temp - target, 0.0),
                        opening_active=opening_active,
                        occupancy_active=occupancy_active,
                        presence_eco_enabled=presence_eco_enabled_room,
                        learning_enabled=learning_enabled_room,
                        opening_pause_enabled=opening_pause_enabled_room,
                        room_enabled=room_enabled,
                        eco_target=eco_target_room,
                        presence_away_min=away_min_room,
                        presence_return_min=return_min_room,
                        boost_active=bool(boost_active),
                        boost_delta_c=boost_delta_c,
                        boost_until_ts=float(boost_until_ts) if isinstance(boost_until_ts, (int, float)) else None,
                        boost_duration_min=boost_duration_min,
                        target_number_entity=tgt_number,
                        heat_pump=heat_pump_entity,
                        heat_pump_power_sensor=heat_pump_power_sensor,
                        heat_pump_power_w=heat_pump_power_w,
                        radiators=radiator_entities,
                        link_group=str(room_cfg.get(CONF_ROOM_LINK_GROUP, DEFAULT_ROOM_LINK_GROUP)).strip().lower(),
                        adjacent_rooms=adjacent_rooms,
                        room_heat_source_direction_bias=room_direction_bias,
                        room_cheap_power_radiator_setback_extra_c=room_setback_extra,
                        anti_short_cycle_min=float(
                            room_cfg.get(CONF_ROOM_ANTI_SHORT_CYCLE_MIN, DEFAULT_ROOM_ANTI_SHORT_CYCLE_MIN)
                        ),
                        quick_start_deficit_c=quick_start_deficit_c,
                        start_deficit_c=start_deficit_c,
                        stop_surplus_c=float(
                            room_cfg.get(
                                CONF_ROOM_STOP_SURPLUS_C,
                                cfg.get(CONF_STOP_SURPLUS_C, DEFAULT_ROOM_STOP_SURPLUS_C),
                            )
                        ),
                        pause_after_open_min=float(
                            pause_after_open_min_room
                        ),
                        resume_after_closed_min=float(
                            resume_after_closed_min_room
                        ),
                        massive_overheat_c=float(
                            room_cfg.get(CONF_ROOM_MASSIVE_OVERHEAT_C, DEFAULT_ROOM_MASSIVE_OVERHEAT_C)
                        ),
                        massive_overheat_min=float(
                            room_cfg.get(CONF_ROOM_MASSIVE_OVERHEAT_MIN, DEFAULT_ROOM_MASSIVE_OVERHEAT_MIN)
                        ),
                        active_heat_entities=active_heat_entities,
                        active_heat_names=active_heat_names,
                        active_heat_summary=active_heat_summary,
                        is_heating_now=bool(active_heat_entities),
                    )
                )

            if (
                startup_refresh
                and rooms_cfg
                and unavailable >= len(rooms_cfg)
                and not rooms
                and not getattr(self, "_startup_sensor_retry_in_progress", False)
            ):
                self._startup_sensor_retry_in_progress = True
                try:
                    await asyncio.sleep(5)
                    return await self._async_update_data()
                finally:
                    self._startup_sensor_retry_in_progress = False
            
            room_slug_map: dict[str, RoomSnapshot] = {}
            for r in rooms:
                room_slug_map[_slug_text(r.name)] = r
            
            max_deficit = max((r.deficit for r in rooms), default=0.0)
            max_surplus = max((r.surplus for r in rooms), default=0.0)
            cold_rooms = [r for r in rooms if r.deficit > 0.5]
            cold_rooms_sorted = sorted(cold_rooms, key=lambda r: r.deficit, reverse=True)
            focus_room = cold_rooms_sorted[0].name if cold_rooms_sorted else "Ingen"
            focus_room_delta = round(cold_rooms_sorted[0].deficit, decimals) if cold_rooms_sorted else 0.0
            extra_room = cold_rooms_sorted[1].name if len(cold_rooms_sorted) > 1 else "Ingen"
            if max_deficit >= 1.0:
                house_level = "Komforttab"
            elif max_deficit >= 0.4:
                house_level = "Let underskud"
            elif max_surplus >= 1.0:
                house_level = "Overophedning"
            else:
                house_level = "Stabil"
            radiator_help_count = 0
            for r in rooms:
                heating = False
                for rad in r.radiators:
                    st = self.hass.states.get(rad)
                    if st and str(st.attributes.get("hvac_action", "")).lower() == "heating":
                        heating = True
                        break
                if heating:
                    radiator_help_count += 1
            
            def _sticky_price(sensor_key: str, memory_key: str) -> float | None:
                sensor_entity = cfg.get(sensor_key, "")
                current = _safe_float(
                    self.hass.states.get(sensor_entity).state
                    if sensor_entity and self.hass.states.get(sensor_entity)
                    else None
                )
                if current is not None:
                    self._last_valid_prices[memory_key] = float(current)
                    return float(current)
                return _safe_float(self._last_valid_prices.get(memory_key))
            
            el_price = _sticky_price(CONF_ELECTRICITY_PRICE_SENSOR, "el_price")
            gas_price = _sticky_price(CONF_GAS_PRICE_SENSOR, "gas_price")
            district_heat_price = _sticky_price(CONF_DISTRICT_HEAT_PRICE_SENSOR, "district_heat_price")
            district_heat_consumption = _safe_float(
                self.hass.states.get(cfg.get(CONF_DISTRICT_HEAT_CONSUMPTION_SENSOR, "")).state
                if cfg.get(CONF_DISTRICT_HEAT_CONSUMPTION_SENSOR)
                and self.hass.states.get(cfg.get(CONF_DISTRICT_HEAT_CONSUMPTION_SENSOR))
                else None
            )
            gas_consumption = _safe_float(
                self.hass.states.get(cfg.get(CONF_GAS_CONSUMPTION_SENSOR, "")).state
                if cfg.get(CONF_GAS_CONSUMPTION_SENSOR)
                and self.hass.states.get(cfg.get(CONF_GAS_CONSUMPTION_SENSOR))
                else None
            )
            outdoor_for_validation = None
            if cfg.get(CONF_OUTDOOR_TEMP_SENSOR):
                st = self.hass.states.get(cfg.get(CONF_OUTDOOR_TEMP_SENSOR))
                outdoor_for_validation = _safe_float(st.state if st else None)
            if outdoor_for_validation is None and cfg.get(CONF_WEATHER_ENTITY):
                w = self.hass.states.get(cfg.get(CONF_WEATHER_ENTITY))
                outdoor_for_validation = _safe_float((w.attributes if w else {}).get("temperature"))
            
            sensor_error = False
            if el_price is not None and not (0 <= el_price < 20):
                sensor_error = True
            if gas_price is not None and not (0 <= gas_price < 20):
                sensor_error = True
            if district_heat_price is not None and not (0 <= district_heat_price < 20):
                sensor_error = True
            if outdoor_for_validation is not None and not (-40 <= outdoor_for_validation <= 50):
                sensor_error = True
            legacy_conflicts = _legacy_automation_conflicts(self.hass)
            price_margin = float(cfg.get(CONF_PRICE_MARGIN, DEFAULT_PRICE_MARGIN))
            price_awareness = bool(cfg.get(CONF_ENABLE_PRICE_AWARENESS, True))
            heat_pump_cheap_priority_factor = float(
                cfg.get(
                    CONF_HEAT_PUMP_CHEAP_PRIORITY_FACTOR,
                    DEFAULT_HEAT_PUMP_CHEAP_PRIORITY_FACTOR,
                )
            )
            heat_pump_cheap_priority_factor = max(0.5, min(2.5, heat_pump_cheap_priority_factor))
            heat_pump_cheap_fan_mode = str(
                cfg.get(
                    CONF_HEAT_PUMP_CHEAP_FAN_MODE,
                    DEFAULT_HEAT_PUMP_CHEAP_FAN_MODE,
                )
            ).strip().lower()
            heat_source_direction_bias = float(
                cfg.get(
                    CONF_HEAT_SOURCE_DIRECTION_BIAS,
                    DEFAULT_HEAT_SOURCE_DIRECTION_BIAS,
                )
            )
            heat_source_direction_bias = max(-2.0, min(2.0, heat_source_direction_bias))
            cheap_power_radiator_setback_extra_c = float(
                cfg.get(
                    CONF_CHEAP_POWER_RADIATOR_SETBACK_EXTRA_C,
                    DEFAULT_CHEAP_POWER_RADIATOR_SETBACK_EXTRA_C,
                )
            )
            cheap_power_radiator_setback_extra_c = max(0.0, min(4.0, cheap_power_radiator_setback_extra_c))
            # Prefer legacy heat-price sensors when present (COP + boiler-efficiency aware):
            # - sensor.varmepris_varmepumpe
            # - sensor.varmepris_gasfyr
            # Fall back to integration-native inputs when those are not available.
            legacy_hp_price = _safe_float(
                self.hass.states.get("sensor.varmepris_varmepumpe").state
                if self.hass.states.get("sensor.varmepris_varmepumpe")
                else None
            )
            legacy_gas_heat_price = _safe_float(
                self.hass.states.get("sensor.varmepris_gasfyr").state
                if self.hass.states.get("sensor.varmepris_gasfyr")
                else None
            )
            # Fallback for setups without legacy templates.
            assumed_hp_cop = 3.0
            fallback_hp_price = None
            if el_price is not None:
                fallback_hp_price = el_price / max(1.0, assumed_hp_cop)
            effective_hp_price = legacy_hp_price if legacy_hp_price is not None else fallback_hp_price
            cheapest_alt_price = None
            cheapest_alt_name = None
            gas_compare_price = legacy_gas_heat_price if legacy_gas_heat_price is not None else gas_price
            for name, price in (("Gas", gas_compare_price), ("Fjernvarme", district_heat_price)):
                if price is None:
                    continue
                if cheapest_alt_price is None or price < cheapest_alt_price:
                    cheapest_alt_price = price
                    cheapest_alt_name = name
            heat_pump_cheaper = (
                effective_hp_price is not None
                and cheapest_alt_price is not None
                and (cheapest_alt_price - effective_hp_price) >= price_margin
            )
            estimated_savings_per_kwh = None
            if effective_hp_price is not None and cheapest_alt_price is not None:
                estimated_savings_per_kwh = round(max(cheapest_alt_price - effective_hp_price, 0.0), decimals)
            estimated_daily_savings = None
            savings_consumption_base = None
            if district_heat_consumption is not None:
                savings_consumption_base = district_heat_consumption
            elif gas_consumption is not None:
                savings_consumption_base = gas_consumption
            if estimated_savings_per_kwh is not None and savings_consumption_base is not None:
                estimated_daily_savings = round(estimated_savings_per_kwh * savings_consumption_base, decimals)
            estimated_monthly_savings = None
            if estimated_daily_savings is not None:
                estimated_monthly_savings = round(estimated_daily_savings * 30.0, decimals)
            cheapest_heat_source = None
            if heat_pump_cheaper:
                cheapest_heat_source = "Varmepumpe"
            elif cheapest_alt_name:
                cheapest_heat_source = cheapest_alt_name
            
            flow_limit_margin = float(cfg.get(CONF_FLOW_LIMIT_MARGIN_C, DEFAULT_FLOW_LIMIT_MARGIN_C))
            radiator_boost = float(cfg.get(CONF_RADIATOR_BOOST_C, DEFAULT_RADIATOR_BOOST_C))
            radiator_setback = float(cfg.get(CONF_RADIATOR_SETBACK_C, DEFAULT_RADIATOR_SETBACK_C))
            actions: list[str] = []
            opening_active_any = any(r.opening_active for r in rooms)
            flow_limited = any(r.temperature >= (r.target + flow_limit_margin) for r in rooms)
            thermostat_handover = False
            pid_rows: list[dict[str, Any]] = []
            
            decision_due = _minutes_since(self._last_ai_update, now_ts) >= decision_interval_min
            manual_ai_requested = bool(
                self._runtime_events.get("manual_ai_last_trigger")
                and (
                    self._last_ai_update is None
                    or float(self._runtime_events.get("manual_ai_last_trigger") or 0.0) > float(self._last_ai_update or 0.0)
                )
            )
            if (
                ai_provider_ready
                and (decision_due or manual_ai_requested)
                and ((not startup_refresh) or manual_ai_requested)
            ):
                try:
                    outdoor_for_ai = None
                    if cfg.get(CONF_OUTDOOR_TEMP_SENSOR):
                        s = self.hass.states.get(cfg.get(CONF_OUTDOOR_TEMP_SENSOR))
                        outdoor_for_ai = _safe_float(s.state if s else None)
                    if outdoor_for_ai is None and cfg.get(CONF_WEATHER_ENTITY):
                        w = self.hass.states.get(cfg.get(CONF_WEATHER_ENTITY))
                        outdoor_for_ai = _safe_float((w.attributes if w else {}).get("temperature"))
                    weather_forecast_next_2h = {
                        "temp_min": 0.0,
                        "temp_max": 0.0,
                        "wind_ms": 0.0,
                    }
                    if cfg.get(CONF_WEATHER_ENTITY):
                        weather_state = self.hass.states.get(cfg.get(CONF_WEATHER_ENTITY))
                        forecast_rows = []
                        if weather_state is not None:
                            raw_forecast = weather_state.attributes.get("forecast")
                            if isinstance(raw_forecast, list):
                                forecast_rows = [row for row in raw_forecast if isinstance(row, dict)]
                        if forecast_rows:
                            window = forecast_rows[:2]
                            temps = [
                                _safe_float(row.get("temperature"))
                                for row in window
                                if _safe_float(row.get("temperature")) is not None
                            ]
                            winds = [
                                _safe_float(row.get("wind_speed"))
                                for row in window
                                if _safe_float(row.get("wind_speed")) is not None
                            ]
                            if temps:
                                weather_forecast_next_2h["temp_min"] = float(min(temps))
                                weather_forecast_next_2h["temp_max"] = float(max(temps))
                            if winds:
                                weather_forecast_next_2h["wind_ms"] = float(winds[0])
                    ai_payload = {
                        "request_id": str(uuid.uuid4()),
                        "timestamp_utc": now.isoformat(),
                        "engine_context": {
                            "ai_provider": ai_provider,
                            "ai_primary_engine": ai_primary_engine,
                            "ai_primary_engine_display": _ai_provider_display(ai_primary_engine),
                            "openclaw_enabled": openclaw_enabled,
                            "openclaw_bridge_url": openclaw_bridge_url if use_openclaw_path else "",
                            "decision_interval_min": round(decision_interval_min, 2),
                        },
                        "runtime": {
                            "enabled": enabled,
                            "presence_eco_enabled": presence_eco_enabled,
                            "presence_eco_active": presence_eco_active,
                            "pid_enabled": pid_enabled,
                            "learning_enabled": learning_enabled,
                            "confidence_threshold": round(confidence_threshold, 2),
                            "current_ai_factor": round(self._ai_factor, 3),
                            "current_ai_confidence": round(self._ai_confidence, 2),
                            "current_ai_reason": self._ai_reason,
                            "fallback_count": self._ai_fallback_count,
                            "last_control_activity": _fmt_ts(self._runtime_events.get("last_control_activity")),
                            "provider_ready": ai_provider_ready,
                            "flow_limited": flow_limited,
                            "thermostat_handover": thermostat_handover,
                        },
                        "prices": {
                            "electricity": el_price,
                            "gas": gas_price,
                            "district_heat": district_heat_price,
                            "legacy_heat_pump_price": legacy_hp_price,
                            "legacy_gas_heat_price": legacy_gas_heat_price,
                            "effective_heat_pump_price": effective_hp_price,
                            "cheapest_heat_source": cheapest_heat_source,
                            "cheapest_alt_name": cheapest_alt_name,
                            "cheapest_alt_price": cheapest_alt_price,
                            "heat_pump_cheaper": heat_pump_cheaper,
                            "estimated_savings_per_kwh": estimated_savings_per_kwh,
                            "estimated_daily_savings": estimated_daily_savings,
                            "estimated_monthly_savings": estimated_monthly_savings,
                            "price_awareness": price_awareness,
                            "heat_pump_cheap_priority_factor": round(heat_pump_cheap_priority_factor, 2),
                            "heat_pump_cheap_fan_mode": heat_pump_cheap_fan_mode,
                "heat_source_direction_bias": round(heat_source_direction_bias, 2),
                "cheap_power_radiator_setback_extra_c": round(cheap_power_radiator_setback_extra_c, 2),
                            "heat_source_direction_bias": round(heat_source_direction_bias, 2),
                            "cheap_power_radiator_setback_extra_c": round(cheap_power_radiator_setback_extra_c, 2),
                        },
                        "max_deficit": round(max_deficit, 2),
                        "max_surplus": round(max_surplus, 2),
                        "outdoor_temp": outdoor_for_ai,
                        "sensor_error": sensor_error,
                        "legacy_conflicts": legacy_conflicts,
                        "bridge_stats": self._bridge_stats,
                        "rooms": [
                            {
                                "name": r.name,
                                "entity_id": (
                                    r.target_number_entity
                                    or r.heat_pump
                                    or (r.radiators[0] if r.radiators else "")
                                ),
                                "sensor_entity": r.sensor_entity,
                                "raw_temp": round(r.raw_temperature, 2),
                                "temp": round(r.temperature, 2),
                                "target": round(r.target, 2),
                                "humidity": round(r.humidity, 1) if r.humidity is not None else None,
                                "humidity_sensor": r.humidity_sensor_entity,
                                "comfort_band": r.comfort_band,
                                "comfort_offset_c": round(r.comfort_offset_c, 2),
                                "comfort_target": round(r.comfort_target, 2),
                                "comfort_gap": round(r.comfort_gap, 2),
                                "effective_gap": round(max(r.deficit, r.comfort_gap), 2),
                                "deficit": round(r.deficit, 2),
                                "surplus": round(r.surplus, 2),
                                "opening_active": bool(r.opening_active),
                                "room_enabled": bool(r.room_enabled),
                                "presence_eco_enabled": bool(r.presence_eco_enabled),
                                "learning_enabled": bool(r.learning_enabled),
                                "opening_pause_enabled": bool(r.opening_pause_enabled),
                                "eco_target": round(r.eco_target, 2),
                                "boost_active": bool(r.boost_active),
                                "boost_delta_c": round(r.boost_delta_c, 2),
                                "boost_duration_min": round(r.boost_duration_min, 1),
                                "boost_until_ts": r.boost_until_ts,
                                "target_number_entity": r.target_number_entity,
                                "heat_pump": r.heat_pump,
                                "heat_pump_state": (
                                    self.hass.states.get(r.heat_pump).state
                                    if r.heat_pump and self.hass.states.get(r.heat_pump)
                                    else None
                                ),
                                "heat_pump_power_sensor": r.heat_pump_power_sensor,
                                "heat_pump_power_w": round(r.heat_pump_power_w, 1)
                                if r.heat_pump_power_w is not None
                                else None,
                                "radiators": r.radiators,
                                "active_heat_entities": r.active_heat_entities,
                                "active_heat_names": r.active_heat_names,
                                "active_heat_summary": r.active_heat_summary,
                                "is_heating_now": bool(r.is_heating_now),
                                "radiator_states": {
                                    rad: (
                                        self.hass.states.get(rad).state
                                        if self.hass.states.get(rad)
                                        else None
                                    )
                                    for rad in r.radiators
                                },
                                "link_group": r.link_group,
                                "anti_short_cycle_min": round(r.anti_short_cycle_min, 2),
                                "quick_start_deficit_c": round(r.quick_start_deficit_c, 2),
                                "start_deficit_c": round(r.start_deficit_c, 2),
                                "stop_surplus_c": round(r.stop_surplus_c, 2),
                                "pause_after_open_min": round(r.pause_after_open_min, 2),
                                "resume_after_closed_min": round(r.resume_after_closed_min, 2),
                                "massive_overheat_c": round(r.massive_overheat_c, 2),
                                "massive_overheat_min": round(r.massive_overheat_min, 2),
                            }
                            for r in rooms
                        ],
                    }
                    provider_ai_payload = _build_provider_decision_payload(ai_payload)
                    last_decision_mode = (
                        self._ai_structured_decision.get("global", {}).get("mode")
                        if isinstance(self._ai_structured_decision, dict)
                        and isinstance(self._ai_structured_decision.get("global"), dict)
                        else None
                    )
                    last_decision_age_sec = int(round(_minutes_since(self._last_ai_update, now_ts) * 60.0, 0))
                    openclaw_decision_payload = _build_openclaw_heating_payload(
                        self.hass,
                        ai_payload,
                        now_ts=now_ts,
                        room_runtime=self._room_runtime,
                        weather_forecast_next_2h=weather_forecast_next_2h,
                        supply_temp=None,
                        return_temp=None,
                        heating_curve_offset=None,
                        last_decision_factor=self._ai_factor,
                        last_decision_mode=str(last_decision_mode or "normal"),
                        last_decision_age_sec=last_decision_age_sec,
                    )
                    provider_decision_payload = (
                        ai_payload if provider_payload_profile == PAYLOAD_PROFILE_HEAVY else provider_ai_payload
                    )
                    self._last_ai_decision_payload_openclaw = openclaw_decision_payload
                    self._last_ai_decision_payload_provider = provider_decision_payload
                    self._last_ai_decision_payload = (
                        openclaw_decision_payload
                        if ai_primary_engine == AI_PRIMARY_ENGINE_OPENCLAW
                        else provider_decision_payload
                    )
                    self._ai_prev_factor = self._ai_factor
                    self._ai_prev_reason = self._ai_reason
                    self._ai_prev_confidence = self._ai_confidence
                    self._ai_prev_decision_source = self._ai_decision_source
                    previous_decision = (self._ai_factor, self._ai_reason, self._ai_confidence)
                    (
                        self._ai_factor,
                        self._ai_reason,
                        self._ai_confidence,
                        self._ai_decision_source,
                        self._ai_structured_decision,
                    ) = await self.ai_client.async_decision_factor(
                        openclaw_enabled=use_openclaw_path and openclaw_enabled,
                        openclaw_bridge_url=openclaw_bridge_url if use_openclaw_path else "",
                        openclaw_url=openclaw_url,
                        openclaw_token=openclaw_token,
                        openclaw_password=openclaw_password,
                        openclaw_timeout_sec=openclaw_timeout_sec,
                        openclaw_model_preferred=openclaw_model_preferred,
                        openclaw_model_fallback=openclaw_model_fallback,
                        primary_engine=ai_primary_engine,
                        fallback_engine=ai_fallback_engine,
                        last_good=previous_decision,
                        ollama_endpoint=str(cfg.get(CONF_OLLAMA_HOST, "")).strip(),
                        ollama_model=str(cfg.get(CONF_AI_MODEL_FAST, DEFAULT_AI_MODEL_FAST)),
                        gemini_api_key=str(cfg.get(CONF_GEMINI_API_KEY, "")).strip(),
                        gemini_model=str(cfg.get(CONF_GEMINI_MODEL_FAST, "gemini-2.5-flash")),
                        payload_openclaw=openclaw_decision_payload,
                        payload_provider=provider_decision_payload,
                    )
                    (
                        self._ai_factor,
                        self._ai_reason,
                        self._ai_confidence,
                        self._ai_decision_source,
                        self._ai_structured_decision,
                    ) = self._reconcile_ai_decision_with_payload(
                        openclaw_decision_payload if ai_primary_engine == AI_PRIMARY_ENGINE_OPENCLAW else provider_decision_payload,
                        self._ai_factor,
                        self._ai_reason,
                        self._ai_confidence,
                        self._ai_decision_source,
                        self._ai_structured_decision if isinstance(self._ai_structured_decision, dict) else {},
                    )
                    self._last_ai_errors = _summarize_ai_errors(
                        self._ai_structured_decision.get("_errors")
                        if isinstance(self._ai_structured_decision, dict)
                        else {}
                    )
                    self._last_ai_fallback_reason = _fallback_reason_from_decision(
                        self._ai_decision_source,
                        self._ai_structured_decision if isinstance(self._ai_structured_decision, dict) else {},
                    )
                    adopted_openclaw_result = False
                    if self._ai_decision_source == 'last_good':
                        adopted_openclaw_result = self._adopt_openclaw_delivered_result_if_available()
                        if adopted_openclaw_result:
                            self._last_ai_fallback_reason = _fallback_reason_from_decision(
                                self._ai_decision_source,
                                self._ai_structured_decision if isinstance(self._ai_structured_decision, dict) else {},
                            )
                    adopted_mqtt_result = False
                    if self._ai_decision_source in {'last_good', 'safe_default', 'safe_default_openclaw_only'}:
                        adopted_mqtt_result = self._adopt_mqtt_sensor_decision_if_available()
                        if adopted_mqtt_result:
                            self._last_ai_fallback_reason = _fallback_reason_from_decision(
                                self._ai_decision_source,
                                self._ai_structured_decision if isinstance(self._ai_structured_decision, dict) else {},
                            )
                    if (
                        self._ai_decision_source in {"last_good", "safe_default"}
                        or "ollama_fallback" in self._ai_decision_source
                    ) and not adopted_openclaw_result and not adopted_mqtt_result:
                        self._ai_fallback_count += 1
                    self._last_ai_update = now_ts
                except Exception as err:  # noqa: BLE001
                    LOGGER.exception("AI decision cycle failed softly: %s", err)
                    actions.append("AI beslutning fejlede - fortsætter med sidste gyldige beslutning")
            
            manual_report_requested = bool(
                self._runtime_events.get("manual_report_last_trigger")
                and (
                    self._last_report_update is None
                    or float(self._runtime_events.get("manual_report_last_trigger") or 0.0) > float(self._last_report_update or 0.0)
                )
            )
            if report_provider_ready and (
                ((not startup_refresh) and _minutes_since(self._last_report_update, now_ts) >= report_interval_min)
                or manual_report_requested
            ):
                try:
                    use_full_report_model = self._manual_full_report_requested
                    report_model_to_use = ai_model_report if use_full_report_model else ai_model_fast
                    report_payload = {
                        "timestamp_utc": now.isoformat(),
                        "decision_engine": {
                            "primary_engine": ai_primary_engine,
                            "primary_engine_display": _ai_provider_display(ai_primary_engine),
                            "fallback_engine": ai_fallback_engine,
                            "fallback_engine_display": _ai_provider_display(ai_fallback_engine),
                            "report_engine": ai_report_engine,
                            "report_engine_display": _ai_provider_display(ai_report_engine),
                            "openclaw_only_mode": openclaw_only_mode,
                            "available_decision_paths": ["openclaw", "ollama", "gemini"],
                            "decision_source": self._ai_decision_source,
                            "decision_source_display": _ai_decision_source_display(self._ai_decision_source),
                            "provider": ai_provider,
                            "provider_display": _ai_provider_display(ai_provider),
                        },
                        "decision": {
                            "factor": round(self._ai_factor, 3),
                            "confidence": round(self._ai_confidence, 1),
                            "reason": self._ai_reason,
                            "structured": self._ai_structured_decision,
                            "openclaw_meta": (
                                self._ai_structured_decision.get("_openclaw_meta", {})
                                if isinstance(self._ai_structured_decision, dict)
                                else {}
                            ),
                        },
                        "decision_payload_profiles": {
                            "active_engine": (
                                "openclaw" if ai_primary_engine == AI_PRIMARY_ENGINE_OPENCLAW else "provider"
                            ),
                            "openclaw_payload_profile": openclaw_payload_profile,
                            "provider_payload_profile": provider_payload_profile,
                            "active_payload": self._last_ai_decision_payload,
                            "openclaw_payload": self._last_ai_decision_payload_openclaw,
                            "provider_payload": self._last_ai_decision_payload_provider,
                        },
                        "runtime": {
                            "enabled": enabled,
                            "provider_ready": ai_provider_ready,
                            "presence_eco_enabled": presence_eco_enabled,
                            "presence_eco_active": presence_eco_active,
                            "pid_enabled": pid_enabled,
                            "learning_enabled": learning_enabled,
                            "flow_limited": flow_limited,
                            "thermostat_handover": thermostat_handover,
                            "fallback_count": self._ai_fallback_count,
                        },
                        "target_base": round(target_base, decimals),
                        "heat_pump_cheaper": heat_pump_cheaper,
                        "el_price": el_price,
                        "gas_price": gas_price,
                        "district_heat_price": district_heat_price,
                        "estimated_savings_per_kwh": estimated_savings_per_kwh,
                        "estimated_daily_savings": estimated_daily_savings,
                        "estimated_monthly_savings": estimated_monthly_savings,
                        "openclaw_bridge_stats": self._bridge_stats,
                        "actions": actions[-10:],
                        "rooms": [
                            {
                                "name": r.name,
                                "temp": round(r.temperature, decimals),
                                "target": round(r.target, decimals),
                                "deficit": round(r.deficit, decimals),
                                "surplus": round(r.surplus, decimals),
                                "opening_active": bool(r.opening_active),
                                "heat_pump": r.heat_pump,
                                "heat_pump_state": (
                                    self.hass.states.get(r.heat_pump).state
                                    if r.heat_pump and self.hass.states.get(r.heat_pump)
                                    else None
                                ),
                                "active_heat_summary": r.active_heat_summary,
                                "is_heating_now": bool(r.is_heating_now),
                            }
                            for r in rooms
                        ],
                    }
                    report_payload["openclaw_requested_model"] = openclaw_model_preferred
                    report_payload["openclaw_fallback_model"] = openclaw_model_fallback
                    report_payload["openclaw_actual_model"] = (
                        self._ai_structured_decision.get("_openclaw_meta", {}).get("actual_model")
                        if isinstance(self._ai_structured_decision, dict)
                        and isinstance(self._ai_structured_decision.get("_openclaw_meta", {}), dict)
                        else None
                    )
                    self._last_ai_report_payload = report_payload
                    ai_report = ""
                    if ai_report_engine == AI_PROVIDER_OLLAMA:
                        ai_report = await self.ai_client.async_generate_report(
                            provider=AI_PROVIDER_OLLAMA,
                            endpoint=str(cfg.get(CONF_OLLAMA_HOST, "")).strip(),
                            api_key="",
                            model=str(cfg.get(CONF_AI_MODEL_REPORT, DEFAULT_AI_MODEL_REPORT)),
                            payload=report_payload,
                        )
                        self._last_report_model_used = str(cfg.get(CONF_AI_MODEL_REPORT, DEFAULT_AI_MODEL_REPORT))
                    elif ai_report_engine == AI_PROVIDER_GEMINI:
                        ai_report = await self.ai_client.async_generate_report(
                            provider=AI_PROVIDER_GEMINI,
                            endpoint="gemini",
                            api_key=str(cfg.get(CONF_GEMINI_API_KEY, "")).strip(),
                            model=str(cfg.get(CONF_GEMINI_MODEL_REPORT, "gemini-2.5-pro")),
                            payload=report_payload,
                        )
                        self._last_report_model_used = str(cfg.get(CONF_GEMINI_MODEL_REPORT, "gemini-2.5-pro"))
                    else:
                        self._last_report_model_used = "OpenClaw"
                        self._ai_report_text = ""
                    if ai_report.strip():
                        self._ai_report_text = ai_report.strip()
                    self._manual_full_report_requested = False
                    self._last_report_update = now_ts
                except Exception as err:  # noqa: BLE001
                    LOGGER.exception("AI report generation failed softly: %s", err)
                    actions.append("AI rapport fejlede - bevarer sidste gyldige rapport")
            
            try:
                await self._async_apply_structured_ai_decision(
                    rooms,
                    self._ai_structured_decision,
                    now_ts,
                    decimals,
                    actions,
                )
            except Exception as err:  # noqa: BLE001
                LOGGER.exception("Structured AI decision apply failed softly: %s", err)
                actions.append("AI rum-overrides fejlede - fortsætter uden structured overrides")
            flow_limited = any(r.temperature >= (r.target + flow_limit_margin) for r in rooms)
            provider_error_state = bool(ai_provider_ready and self._ai_confidence <= 0.1)
            if sensor_error:
                actions.append("Sensorvalidering: outlier fundet")
            if enabled and ai_provider_ready:
                try:
                    allow_heat_pumps = (not price_awareness) or heat_pump_cheaper
                    thermostat_handover = bool(price_awareness and not allow_heat_pumps)
                    cheap_hp_bias_active = bool(price_awareness and heat_pump_cheaper)
                    low_confidence = self._ai_confidence < confidence_threshold
                    if low_confidence:
                        actions.append(
                            f"Lav AI-konfidens ({round(self._ai_confidence,1)}% < {round(confidence_threshold,1)}%)"
                        )
                    adjacent_to_heat_pump: set[str] = set()
                    for hp_room in rooms:
                        if not hp_room.heat_pump:
                            continue
                        for nm in hp_room.adjacent_rooms:
                            adjacent_to_heat_pump.add(str(nm).strip().lower())

                    for room in rooms:
                        if not room.room_enabled:
                            actions.append(f"{room.name}: AI rumstyring er slået fra")
                            continue
                        room_rt_defaults = {
                            "open_since": None,
                            "closed_since": None,
                            "paused_by_open": False,
                            "last_hvac_mode": "heat",
                            "last_switch": None,
                            "overheat_since": None,
                            "pid_integral": 0.0,
                            "pid_last_error": None,
                            "pid_last_ts": None,
                            "learn_hot_hits": 0,
                            "learn_cold_hits": 0,
                            "learn_start_offset": 0.0,
                            "learn_stop_offset": 0.0,
                            "room_empty_since": None,
                            "room_occupied_since": None,
                            "eco_active": False,
                            "eco_comfort_target": None,
                            "eco_prev_radiator_target": None,
                            "eco_last_change": None,
                            "heat_hold_until": None,
                            "stop_candidate_since": None,
                        }
                        rt = self._room_runtime.setdefault(room.name, dict(room_rt_defaults))
                        for key, value in room_rt_defaults.items():
                            rt.setdefault(key, value)
            
                        eco_room_enabled = bool(presence_eco_enabled and room.presence_eco_enabled)
                        room_occupied_now = bool(room.occupancy_active and not vacuum_running)
                        # Track room occupancy continuously, even when eco is disabled, so enabling
                        # eco while a room has already been empty can use the real empty-since time.
                        if room_occupied_now:
                            rt["room_empty_since"] = None
                            if rt["room_occupied_since"] is None:
                                rt["room_occupied_since"] = now_ts
                        else:
                            rt["room_occupied_since"] = None
                            if rt["room_empty_since"] is None:
                                rt["room_empty_since"] = now_ts
            
                        if eco_room_enabled:
                            # Reconcile eco target every cycle while eco is active.
                            # This guarantees correct behavior after restart/migration where
                            # previous runtime could still hold an old comfort target override.
                            if rt.get("eco_active", False):
                                eco_target_for_ai = round(max(7.0, min(25.0, room.eco_target)), decimals)
                                cur_override = _safe_float(rt.get("target_override"))
                                lock_rt = self._room_runtime.setdefault(
                                    f"__target_lock__{room.name}",
                                    {"locked_target": eco_target_for_ai, "last_seen_target": eco_target_for_ai},
                                )
                                lock_target = _safe_float(lock_rt.get("locked_target"))
                                needs_reconcile = (
                                    cur_override is None
                                    or abs(float(cur_override) - eco_target_for_ai) > 0.01
                                    or lock_target is None
                                    or abs(float(lock_target) - eco_target_for_ai) > 0.01
                                )
                                if needs_reconcile:
                                    rt["target_override"] = eco_target_for_ai
                                    rt["room_target_last_changed"] = now_ts
                                    actions.append(
                                        f"{room.name}: eco driftmål -> {eco_target_for_ai}°C"
                                    )
            
                            if (
                                enabled
                                and not rt.get("eco_active", False)
                                and not room_occupied_now
                                and _minutes_since(rt.get("room_empty_since"), now_ts) >= room.presence_away_min
                            ):
                                rt["eco_active"] = True
                                rt["eco_last_change"] = now_ts
                                rt["eco_comfort_target"] = room.target
                                eco_target_for_ai = round(max(7.0, min(25.0, room.eco_target)), decimals)
                                rt["target_override"] = eco_target_for_ai
                                rt["room_target_last_changed"] = now_ts
                                lock_rt = self._room_runtime.setdefault(
                                    f"__target_lock__{room.name}",
                                    {"locked_target": eco_target_for_ai, "last_seen_target": eco_target_for_ai},
                                )
                                actions.append(
                                    f"{room.name}: eco aktiv via manglende presence (driftmål -> {eco_target_for_ai}°C)"
                                )
                                if room.radiators:
                                    rad_state = self.hass.states.get(room.radiators[0])
                                    rt["eco_prev_radiator_target"] = _safe_float(
                                        rad_state.attributes.get("temperature") if rad_state else None
                                    )
            
                            if (
                                rt.get("eco_active", False)
                                and (
                                    (room_occupied_now and _minutes_since(rt.get("room_occupied_since"), now_ts) >= room.presence_return_min)
                                    or not enabled
                                    or not presence_eco_enabled
                                )
                            ):
                                restore_rad = _safe_float(rt.get("eco_prev_radiator_target"))
                                if restore_rad is not None and room.radiators:
                                    await self._async_set_temperature_if_needed(room.radiators[0], restore_rad, actions)
                                restore_target = _safe_float(rt.get("eco_comfort_target"))
                                if restore_target is not None:
                                    restore_target = round(max(7.0, min(25.0, restore_target)), decimals)
                                    rt["target_override"] = restore_target
                                    rt["room_target_last_changed"] = now_ts
                                rt["eco_active"] = False
                                rt["eco_last_change"] = now_ts
                                actions.append(f"{room.name}: eco afsluttet (hovedmål bevaret)")
                        elif rt.get("eco_active", False):
                            # If eco is active and the room/global eco toggle is turned off,
                            # clear eco state immediately for predictable behavior.
                            restore_rad = _safe_float(rt.get("eco_prev_radiator_target"))
                            if restore_rad is not None and room.radiators:
                                await self._async_set_temperature_if_needed(room.radiators[0], restore_rad, actions)
                            restore_target = _safe_float(rt.get("eco_comfort_target"))
                            if restore_target is not None:
                                restore_target = round(max(7.0, min(25.0, restore_target)), decimals)
                                rt["target_override"] = restore_target
                                rt["room_target_last_changed"] = now_ts
                            rt["eco_active"] = False
                            rt["eco_last_change"] = now_ts
                            actions.append(f"{room.name}: eco slået fra")
            
                        if room.opening_active and room.opening_pause_enabled:
                            rt["closed_since"] = None
                            if rt["open_since"] is None:
                                rt["open_since"] = now_ts
                            if (
                                room.heat_pump
                                and not rt["paused_by_open"]
                                and _minutes_since(rt["open_since"], now_ts) >= room.pause_after_open_min
                            ):
                                hp_state = self.hass.states.get(room.heat_pump)
                                if hp_state and hp_state.state not in ("off", "unknown", "unavailable"):
                                    rt["last_hvac_mode"] = hp_state.state
                                    await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode.OFF, actions)
                                    rt["paused_by_open"] = True
                                    rt["last_switch"] = now_ts
                            continue
            
                        rt["open_since"] = None
                        if rt["closed_since"] is None:
                            rt["closed_since"] = now_ts
            
                        if room.heat_pump and rt["paused_by_open"] and not room.opening_pause_enabled:
                            restore = str(rt.get("last_hvac_mode", "heat"))
                            if restore not in {"heat", "cool", "auto", "dry", "fan_only", "heat_cool"}:
                                restore = "heat"
                            await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode(restore), actions)
                            rt["paused_by_open"] = False
                            rt["last_switch"] = now_ts
            
                        if room.heat_pump and rt["paused_by_open"]:
                            if _minutes_since(rt["closed_since"], now_ts) >= room.resume_after_closed_min:
                                restore = str(rt.get("last_hvac_mode", "heat"))
                                if restore not in {"heat", "cool", "auto", "dry", "fan_only", "heat_cool"}:
                                    restore = "heat"
                                await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode(restore), actions)
                                rt["paused_by_open"] = False
                                rt["last_switch"] = now_ts
                            continue
            
                        # Room Eco fallback: if no target number is configured, keep legacy direct control.
                        if eco_room_enabled and rt.get("eco_active", False) and not room.target_number_entity:
                            eco_setpoint = round(max(7.0, min(25.0, room.eco_target)), decimals)
                            if room.heat_pump:
                                # Deadband around eco target to avoid toggling noise.
                                if room.temperature >= (room.eco_target + 0.1):
                                    await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode.HEAT, actions)
                                    await self._async_set_temperature_if_needed(room.heat_pump, eco_setpoint, actions)
                                    actions.append(f"{room.name}: eco coast aktiv ved lavt setpoint")
                                elif room.temperature <= (room.eco_target - 0.3):
                                    await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode.HEAT, actions)
                                    await self._async_set_temperature_if_needed(room.heat_pump, eco_setpoint, actions)
                                else:
                                    await self._async_set_temperature_if_needed(room.heat_pump, eco_setpoint, actions)
                            for rad in room.radiators:
                                await self._async_set_temperature_if_needed(rad, eco_setpoint, actions)
                            continue
            
                        linked_hot = False
                        if room.link_group:
                            peers = [r for r in rooms if r.link_group and r.link_group == room.link_group]
                            linked_hot = any((p.temperature >= (p.target + flow_limit_margin)) for p in peers)
            
                        if room.surplus >= room.massive_overheat_c:
                            if rt["overheat_since"] is None:
                                rt["overheat_since"] = now_ts
                        else:
                            rt["overheat_since"] = None
            
                        massive_overheat_active = (
                            rt["overheat_since"] is not None
                            and _minutes_since(rt["overheat_since"], now_ts) >= room.massive_overheat_min
                        )
            
                        error = room.target - room.temperature
                        effective_deficit = room.deficit
                        shared_demand_rooms: list[RoomSnapshot] = []
                        if room.link_group:
                            shared_demand_rooms.extend(
                                [r for r in rooms if r.name != room.name and r.link_group == room.link_group]
                            )
                        if room.heat_pump:
                            hp_slug = _slug_text(str(room.heat_pump).split(".", 1)[-1])
                            for slug, r in room_slug_map.items():
                                if r.name == room.name:
                                    continue
                                if slug and slug in hp_slug and r not in shared_demand_rooms:
                                    shared_demand_rooms.append(r)
                        if shared_demand_rooms:
                            effective_deficit = max([room.deficit] + [r.deficit for r in shared_demand_rooms])
                        comfort_effective_gap = max(float(room.deficit), float(room.comfort_gap))
                        comfort_gap_extra = max(0.0, float(room.comfort_gap) - float(room.deficit))
                        comfort_bias_active = bool(
                            comfort_mode_enabled
                            and room.room_enabled
                            and not room.opening_active
                            and comfort_gap_extra >= 0.05
                        )
                        if comfort_bias_active:
                            effective_deficit = max(effective_deficit, comfort_effective_gap)
                        learn_start_offset = float(rt.get("learn_start_offset", 0.0))
                        learn_stop_offset = float(rt.get("learn_stop_offset", 0.0))
                        effective_room_direction_bias = (
                            room.room_heat_source_direction_bias if cheap_hp_bias_active else 0.0
                        )
                        room_hp_priority_factor = (
                            max(
                                0.5,
                                min(
                                    2.5,
                                    heat_pump_cheap_priority_factor
                                    + (effective_room_direction_bias * 0.4),
                                ),
                            )
                            if room.heat_pump
                            else 1.0
                        )
                        start_threshold = max(
                            0.0,
                            (room.start_deficit_c + learn_start_offset) / max(0.5, room_hp_priority_factor),
                        )
                        stop_threshold = max(
                            0.0,
                            (room.stop_surplus_c + learn_stop_offset)
                            * max(0.5, 1.0 + 0.4 * (room_hp_priority_factor - 1.0)),
                        )
                        quick_start_threshold = max(
                            0.05,
                            room.quick_start_deficit_c / max(0.5, room_hp_priority_factor),
                        )
                        prolonged_deficit_min = 20.0
                        comfort_deficit_threshold = 0.1
                        effective_start_threshold = start_threshold
                        if comfort_bias_active and room.comfort_band == "tør":
                            effective_start_threshold = max(
                                0.0,
                                start_threshold - min(0.1, comfort_gap_extra),
                            )
                        min_hold_minutes = 60.0
                        hold_surplus_release_c = 1.0
                        stop_temp_surplus_c = 1.0
            
                        hp_room_offset = 0.0
                        if effective_deficit >= 1.2:
                            hp_room_offset = 3.0
                        elif effective_deficit >= 0.5:
                            hp_room_offset = 2.0
                        elif effective_deficit >= 0.1:
                            hp_room_offset = 1.0
                        elif room.surplus >= stop_threshold:
                            hp_room_offset = -1.0
                        elif room.surplus > 0.0:
                            hp_room_offset = -1.0
            
                        pid_output = 0.0
                        if pid_enabled:
                            last_pid_ts = rt.get("pid_last_ts")
                            dt_min = min(max(_minutes_since(last_pid_ts, now_ts), 0.1), 10.0)
                            integral = float(rt.get("pid_integral", 0.0)) + (error * dt_min)
                            integral = max(-pid_integral_limit, min(pid_integral_limit, integral))
                            last_error = rt.get("pid_last_error")
                            derivative = 0.0
                            if isinstance(last_error, (int, float)):
                                derivative = (error - float(last_error)) / dt_min
                            if abs(error) <= pid_deadband_c:
                                pid_output = 0.0
                                integral = integral * 0.5
                            else:
                                pid_output = (pid_kp * error) + (pid_ki * integral) + (pid_kd * derivative)
                                pid_output = max(-pid_offset_max_c, min(pid_offset_max_c, pid_output))
                            rt["pid_integral"] = integral
                            rt["pid_last_error"] = error
                            rt["pid_last_ts"] = now_ts
            
                        hp_target = round(max(16.0, min(30.0, room.target + hp_room_offset)), decimals)
                        hp_state = self.hass.states.get(room.heat_pump) if room.heat_pump else None
                        hp_internal_temp = _safe_float((hp_state.attributes if hp_state else {}).get("current_temperature"))
                        hp_internal_bias = None
                        if hp_internal_temp is not None:
                            hp_internal_bias = hp_internal_temp - room.temperature
            
                        if effective_deficit >= effective_start_threshold:
                            if rt.get("deficit_since") is None:
                                rt["deficit_since"] = now_ts
                        else:
                            rt["deficit_since"] = None
                        prolonged_deficit_active = (
                            rt.get("deficit_since") is not None
                            and _minutes_since(rt.get("deficit_since"), now_ts) >= prolonged_deficit_min
                        )
            
                        if linked_hot or room.surplus >= stop_threshold:
                            hp_target = round(room.target, decimals)
            
                        allow_start = (
                            effective_deficit >= effective_start_threshold
                            and allow_heat_pumps
                            and not massive_overheat_active
                        )
                        openclaw_mode_override = str(rt.get("openclaw_mode_override", "")).strip().lower()
                        force_off_by_ai = openclaw_mode_override == "off"
                        room_hybrid_takeover_heat = bool(
                            thermostat_handover
                            and room.heat_pump
                            and effective_deficit >= effective_start_threshold
                            and not massive_overheat_active
                        )
                        if room_hybrid_takeover_heat:
                            allow_start = True
                        if force_off_by_ai:
                            allow_start = False
                        if low_confidence:
                            # Fail soft: keep deterministic heating control active.
                            # We only reduce AI aggressiveness, never block basic heat demand.
                            hp_room_offset = max(hp_room_offset, 0.0)
                        last_switch = rt.get("last_switch")
                        if allow_start:
                            if _minutes_since(last_switch, now_ts) < room.anti_short_cycle_min and effective_deficit < quick_start_threshold:
                                allow_start = False
            
                        if room.heat_pump:
                            if force_off_by_ai:
                                hp_was_running = bool(hp_state and hp_state.state != "off")
                                await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode.OFF, actions)
                                rt["heat_hold_until"] = None
                                rt["stop_candidate_since"] = None
                                if hp_was_running:
                                    rt["last_switch"] = now_ts
                            elif allow_start:
                                rt["stop_candidate_since"] = None
                                hp_prev_state = str(hp_state.state).lower() if hp_state and hp_state.state is not None else "unknown"
                                hp_was_not_heat = hp_prev_state != "heat"
                                if pid_enabled:
                                    hp_target = round(
                                        max(16.0, min(30.0, room.target + hp_room_offset + pid_output)),
                                        decimals,
                                    )
                                hp_power_w = room.heat_pump_power_w
                                if hp_power_w is not None:
                                    if effective_deficit >= 0.4 and hp_power_w < 180.0:
                                        hp_target = round(max(16.0, min(30.0, max(hp_target, room.target + 1.5))), decimals)
                                        actions.append(
                                            f"{room.name}: lavt HP-forbrug ({round(hp_power_w)}W) ved underskud -> løftet setpoint"
                                        )
                                    elif effective_deficit >= 0.2 and hp_power_w < 120.0:
                                        hp_target = round(max(16.0, min(30.0, max(hp_target, room.target + 1.0))), decimals)
                                        actions.append(
                                            f"{room.name}: meget lavt HP-forbrug ({round(hp_power_w)}W) -> mild setpoint boost"
                                        )
                                await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode.HEAT, actions)
                                await self._async_set_temperature_if_needed(room.heat_pump, hp_target, actions)
                                if hp_was_not_heat:
                                    rt["last_switch"] = now_ts
                                    rt["heat_hold_until"] = now_ts + (min_hold_minutes * 60.0)
                                actions.append(f"{room.name}: varmepumpe hold aktiv i {int(min_hold_minutes)} min")
                                if comfort_bias_active and room.comfort_band == "tør":
                                    actions.append(
                                        f"{room.name}: komfortmode prioriterede tør luft ({room.humidity:.0f}%) og oplevet komfort"
                                    )
                            else:
                                stop_temp_threshold = max(stop_threshold, stop_temp_surplus_c)
                                stop_due_to_temp = room.surplus >= stop_temp_threshold
                                stop_due_to_price = bool(
                                    price_awareness and not allow_heat_pumps and not room_hybrid_takeover_heat
                                )
                                stop_request = bool(
                                    stop_due_to_temp or stop_due_to_price
                                )
                                stop_delay_min = 12.0
                                if stop_request:
                                    if rt.get("stop_candidate_since") is None:
                                        rt["stop_candidate_since"] = now_ts
                                else:
                                    rt["stop_candidate_since"] = None
                                stop_stable = bool(
                                    stop_request
                                    and _minutes_since(rt.get("stop_candidate_since"), now_ts) >= stop_delay_min
                                )
                                hold_until = _safe_float(rt.get("heat_hold_until"))
                                hold_active = bool(hold_until is not None and hold_until > now_ts)
                                hold_break_surplus = max(stop_temp_threshold + hold_surplus_release_c, 1.6)
                                high_surplus_now = room.surplus >= hold_break_surplus
                                coast_offset = 1.0 if room.surplus < (stop_temp_threshold + 1.5) else 2.0
                                coast_target = round(max(16.0, min(30.0, room.target - coast_offset)), decimals)
                                modulate_when_cheap = bool(
                                    stop_due_to_temp
                                    and not stop_due_to_price
                                    and allow_heat_pumps
                                    and not massive_overheat_active
                                )
                                if modulate_when_cheap:
                                    rt["stop_candidate_since"] = None
                                    await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode.HEAT, actions)
                                    await self._async_set_temperature_if_needed(room.heat_pump, coast_target, actions)
                                    actions.append(
                                        f"{room.name}: billig AC -> modulerer (coast {coast_target}°C) i stedet for OFF"
                                    )
                                elif massive_overheat_active:
                                    hp_was_running = bool(hp_state and hp_state.state != "off")
                                    await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode.OFF, actions)
                                    rt["heat_hold_until"] = None
                                    rt["stop_candidate_since"] = None
                                    if hp_was_running:
                                        rt["last_switch"] = now_ts
                                elif stop_stable and (not hold_active or high_surplus_now):
                                    await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode.HEAT, actions)
                                    await self._async_set_temperature_if_needed(room.heat_pump, coast_target, actions)
                                    rt["stop_candidate_since"] = None
                                    actions.append(
                                        f"{room.name}: stabilt stopbehov -> coast {coast_target}°C i stedet for OFF"
                                    )
                                elif stop_request and hold_active:
                                    await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode.HEAT, actions)
                                    await self._async_set_temperature_if_needed(
                                        room.heat_pump, round(room.target, decimals), actions
                                    )
                                    actions.append(f"{room.name}: hold holder varmepumpe aktiv nær mål")
                                elif stop_request and not stop_stable:
                                    await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode.HEAT, actions)
                                    await self._async_set_temperature_if_needed(
                                        room.heat_pump, round(room.target, decimals), actions
                                    )
                                    actions.append(f"{room.name}: stop afventer stabilitet ({int(stop_delay_min)} min)")
                            if low_confidence and _minutes_since(rt.get("last_switch"), now_ts) >= revert_timeout_min:
                                await self._async_set_temperature_if_needed(room.heat_pump, round(room.target, decimals), actions)
            
                            if eco_room_enabled and rt.get("eco_active", False):
                                hp_state = self.hass.states.get(room.heat_pump)
                                hp_off = bool(hp_state and hp_state.state == "off")
                                if (
                                    hp_off
                                    and not room.occupancy_active
                                    and not vacuum_running
                                    and _minutes_since(rt.get("last_switch"), now_ts) >= 3
                                    and room.temperature < (room.eco_target - 0.2)
                                ):
                                    await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode.HEAT, actions)
                                    actions.append(f"{room.name}: eco failsafe tændte varmepumpe")
            
                            if learning_enabled and room.learning_enabled:
                                hp_state = self.hass.states.get(room.heat_pump)
                                hp_is_heat = bool(hp_state and hp_state.state == "heat")
                                if room.surplus >= 1.2 and hp_is_heat:
                                    rt["learn_hot_hits"] = int(rt.get("learn_hot_hits", 0)) + 1
                                elif room.deficit >= 1.0 and not hp_is_heat:
                                    rt["learn_cold_hits"] = int(rt.get("learn_cold_hits", 0)) + 1
                                else:
                                    rt["learn_hot_hits"] = max(0, int(rt.get("learn_hot_hits", 0)) - 1)
                                    rt["learn_cold_hits"] = max(0, int(rt.get("learn_cold_hits", 0)) - 1)
            
                                if int(rt.get("learn_hot_hits", 0)) >= 3:
                                    rt["learn_start_offset"] = min(0.6, float(rt.get("learn_start_offset", 0.0)) + 0.1)
                                    rt["learn_stop_offset"] = max(-0.5, float(rt.get("learn_stop_offset", 0.0)) - 0.1)
                                    rt["learn_hot_hits"] = 0
                                if int(rt.get("learn_cold_hits", 0)) >= 3:
                                    rt["learn_start_offset"] = max(-0.5, float(rt.get("learn_start_offset", 0.0)) - 0.1)
                                    rt["learn_stop_offset"] = min(0.6, float(rt.get("learn_stop_offset", 0.0)) + 0.1)
                                    rt["learn_cold_hits"] = 0

                        if thermostat_handover:
                            if room.heat_pump and not room_hybrid_takeover_heat:
                                takeover_coast_target = round(max(16.0, min(30.0, room.target - 2.0)), decimals)
                                await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode.HEAT, actions)
                                await self._async_set_temperature_if_needed(
                                    room.heat_pump, takeover_coast_target, actions
                                )
                            if room_hybrid_takeover_heat:
                                actions.append(
                                    f"{room.name}: hybrid takeover (AC prioriteret pga. aktuelt underskud)"
                                )
                                if shared_demand_rooms:
                                    demand_names = ", ".join(r.name for r in shared_demand_rooms if r.deficit > 0)
                                    if demand_names:
                                        actions.append(f"{room.name}: delt varmebehov fra {demand_names}")
                            else:
                                actions.append(
                                    f"{room.name}: thermostat takeover (AC dyrere end alternativ, coast beholdt)"
                                )
            
                        if room.heat_pump:
                            room_radiator_setback = radiator_setback
                            if cheap_hp_bias_active:
                                direction_bonus = max(0.0, room.room_heat_source_direction_bias) * 0.8
                                direction_penalty = max(0.0, -room.room_heat_source_direction_bias) * 0.8
                                room_radiator_setback = max(
                                    0.0,
                                    radiator_setback
                                    + room.room_cheap_power_radiator_setback_extra_c
                                    + (room_hp_priority_factor - 1.0) * 1.5
                                    + direction_bonus
                                    - direction_penalty,
                                )
                            rad_target = round(
                                max(
                                    7.0,
                                    min(
                                        25.0,
                                        (room.target - room_radiator_setback)
                                        + (radiator_boost if (room.deficit > 0 and linked_hot) else 0),
                                    ),
                                ),
                                decimals,
                            )
                        else:
                            # Rooms without heat pump should maintain room target directly.
                            rad_target = round(max(7.0, min(25.0, room.target)), decimals)
                            if cheap_hp_bias_active and str(room.name).strip().lower() in adjacent_to_heat_pump:
                                adjacency_setback = (
                                    max(0.0, room.room_cheap_power_radiator_setback_extra_c * 0.6)
                                    + max(0.0, room.room_heat_source_direction_bias) * 0.5
                                )
                                if room.deficit <= 0.3 and adjacency_setback > 0.0:
                                    rad_target = round(max(7.0, min(25.0, room.target - adjacency_setback)), decimals)
                                    actions.append(
                                        f"{room.name}: nabo-til-varmepumpe, radiator saenket ({rad_target}C)"
                                    )
                        if thermostat_handover:
                            if room.heat_pump:
                                # Gas/thermostat takeover: raise radiator to room target for stable comfort.
                                rad_target = round(max(7.0, min(25.0, room.target)), decimals)
                                actions.append(
                                    f"{room.name}: radiator mål sat til AI-mål ({rad_target}°C) ved thermostat takeover"
                                )
                            else:
                                # Rooms without heat pump: radiator follows AI target directly.
                                rad_target = round(max(7.0, min(25.0, room.target)), decimals)
                                actions.append(f"{room.name}: radiator mål sat til AI-mål ({rad_target}°C)")
                        elif room.heat_pump and (
                            prolonged_deficit_active
                            or (comfort_bias_active and effective_deficit >= comfort_deficit_threshold)
                        ) and not (eco_room_enabled and rt.get("eco_active", False)):
                            # If AC room remains in deficit for longer time, lift radiator to target as assist.
                            assist_target = round(max(7.0, min(25.0, room.target)), decimals)
                            if assist_target > rad_target:
                                rad_target = assist_target
                                if prolonged_deficit_active:
                                    actions.append(
                                        f"{room.name}: langvarigt underskud -> radiator assist til AI-mål ({rad_target}°C)"
                                    )
                                else:
                                    actions.append(
                                        f"{room.name}: komfortmode -> radiator assist til AI-mål ({rad_target}°C)"
                                    )
                        if eco_room_enabled and rt.get("eco_active", False):
                            hard_floor = room.eco_target - 1.2
                            if room.temperature < hard_floor:
                                guard_target = round(min(hard_floor + 0.5, 21.0), decimals)
                                if guard_target > rad_target:
                                    rad_target = guard_target
                                    actions.append(f"{room.name}: eco hard-floor løftede radiator-target")
                        for rad in room.radiators:
                            await self._async_set_temperature_if_needed(rad, rad_target, actions)
            
                        pid_rows.append(
                            {
                                "rum": room.name,
                                "error": round(error, decimals),
                                "integral": round(float(rt.get("pid_integral", 0.0)), decimals),
                                "output": round(pid_output, decimals),
                                "setpunkt": hp_target if room.heat_pump else None,
                                "learn_start_offset": round(float(rt.get("learn_start_offset", 0.0)), decimals),
                                "learn_stop_offset": round(float(rt.get("learn_stop_offset", 0.0)), decimals),
                            }
                        )
                except Exception as err:  # noqa: BLE001
                    LOGGER.exception("AI room control cycle failed: %s", err)
                    actions.append(f"AI styringsfejl: {err}")
            elif enabled and not ai_provider_ready:
                actions.append("AI provider ikke klar - styring pauset")
            
            if not enabled:
                # Global AI-styring er slået fra:
                # - AC/varmepumper styres ikke.
                # - Radiator-termostater (fx Better Thermostat) følger fortsat AI-rummål.
                for room in rooms:
                    if room.target is None:
                        continue
                    rad_target = round(max(7.0, min(25.0, room.target)), decimals)
                    for rad in room.radiators:
                        await self._async_set_temperature_if_needed(rad, rad_target, actions)
                if actions:
                    actions.append("AI OFF: radiatorer følger AI-mål, AC styres manuelt")
            
            if enabled and ai_provider_ready and _minutes_since(self._runtime_events.get("last_control_activity"), now_ts) >= 30:
                coldest = next((r for r in sorted(rooms, key=lambda x: x.deficit, reverse=True) if r.heat_pump), None)
                if coldest and coldest.deficit > 0.3:
                    await self._async_set_hvac_mode_if_needed(coldest.heat_pump, HVACMode.HEAT, actions)
                    actions.append(f"Watchdog: genaktiverede varme i {coldest.name}")
            
            if actions:
                self._runtime_events["last_control_activity"] = now_ts
            
            outdoor_temp = None
            if cfg.get(CONF_OUTDOOR_TEMP_SENSOR):
                st = self.hass.states.get(cfg[CONF_OUTDOOR_TEMP_SENSOR])
                outdoor_temp = _safe_float(st.state if st else None)
            if outdoor_temp is None and cfg.get(CONF_WEATHER_ENTITY):
                weather_state = self.hass.states.get(cfg[CONF_WEATHER_ENTITY])
                outdoor_temp = _safe_float((weather_state.attributes if weather_state else {}).get("temperature"))
            
            current_mode = self._compute_heating_mode_from_rooms(rooms)
            self._append_analytics_sample(
                now_ts=now_ts,
                mode=current_mode,
                el_price=el_price,
                gas_price=gas_price,
                district_heat_price=district_heat_price,
                gas_consumption=gas_consumption,
                district_heat_consumption=district_heat_consumption,
            )
            local_now = dt_util.as_local(now)
            today_start_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_start_local = today_start_local - timedelta(days=1)
            week_start_ts = now_ts - (7 * 24 * 60 * 60)
            yesterday_summary = self._build_period_summary(
                yesterday_start_local.timestamp(), today_start_local.timestamp(), decimals
            )
            week_summary = self._build_period_summary(week_start_ts, now_ts, decimals)
            
            report = self._build_report(
                ai_provider=ai_provider,
                ai_primary_engine=ai_primary_engine,
                ai_fallback_engine=ai_fallback_engine,
                ai_report_engine=ai_report_engine,
                ai_decision_source=self._ai_decision_source,
                ai_model_fast=ai_model_fast,
                ai_model_report=ai_model_report,
                provider_ready=ai_provider_ready,
                flow_limited=flow_limited,
                heat_pump_cheaper=heat_pump_cheaper,
                cheapest_alt_name=cheapest_alt_name,
                estimated_savings_per_kwh=estimated_savings_per_kwh,
                estimated_daily_savings=estimated_daily_savings,
                ai_report_text=self._ai_report_text,
                openclaw_model_preferred=openclaw_model_preferred,
                openclaw_model_fallback=openclaw_model_fallback,
                rooms=rooms,
                actions=actions,
                decimals=decimals,
            )
            
            await self._async_save_runtime()
            
            rooms_payload = [self._build_room_state_payload(r, decimals) for r in rooms]
            actions_payload = actions[-25:]
            report_payload = report
            unavailable_payload = unavailable
            cold_start_cache_used = False
            if (
                startup_refresh
                and unavailable >= len(rooms_cfg)
                and not rooms
                and isinstance(previous_data.get("rooms"), list)
                and previous_data.get("rooms")
            ):
                cold_start_cache_used = True
                rooms_payload = list(previous_data.get("rooms", []))
                actions_payload = list(previous_data.get("actions", []))
                previous_report = previous_data.get("report")
                if isinstance(previous_report, dict) and previous_report:
                    report_payload = previous_report
                unavailable_payload = int(previous_data.get("unavailable_sensors", unavailable))

            return {
                "updated_at": dt_util.now().strftime("%Y-%m-%d %H:%M:%S"),
                "enabled": enabled,
                "ai_provider": ai_provider,
                "ai_primary_engine": ai_primary_engine,
                "ai_primary_engine_display": (
                    _ai_provider_display(ai_primary_engine)
                ),
                "ai_fallback_engine": ai_fallback_engine,
                "ai_fallback_engine_display": _ai_provider_display(ai_fallback_engine),
                "ai_report_engine": ai_report_engine,
                "ai_report_engine_display": _ai_provider_display(ai_report_engine),
                "ai_available_providers": ["openclaw", "ollama", "gemini"],
                "openclaw_payload_profile": openclaw_payload_profile,
                "provider_payload_profile": provider_payload_profile,
                "ai_model_fast": ai_model_fast,
                "ai_model_report": ai_model_report,
                "last_report_model_used": self._last_report_model_used or ai_model_fast,
                "ai_provider_ready": ai_provider_ready,
                "openclaw_only_mode": openclaw_only_mode,
                "ai_provider_endpoint": provider_endpoint,
                "openclaw_url": openclaw_url if openclaw_enabled else "",
                "openclaw_bridge_url": openclaw_bridge_url,
                "openclaw_model_preferred": openclaw_model_preferred,
                "openclaw_model_fallback": openclaw_model_fallback,
                "ai_decision_interval_min": round(decision_interval_min, 1),
                "ai_report_interval_min": round(report_interval_min, 1),
                "ai_factor": self._ai_factor,
                "ai_reason": self._ai_reason,
                "ai_confidence": round(self._ai_confidence, 1),
                "ai_prev_factor": (
                    round(self._ai_prev_factor, 3)
                    if isinstance(self._ai_prev_factor, (int, float))
                    else None
                ),
                "ai_prev_reason": self._ai_prev_reason,
                "ai_prev_confidence": (
                    round(self._ai_prev_confidence, 1)
                    if isinstance(self._ai_prev_confidence, (int, float))
                    else None
                ),
                "ai_decision_source": self._ai_decision_source,
                "ai_decision_source_display": _ai_decision_source_display(self._ai_decision_source),
                "ai_prev_decision_source": self._ai_prev_decision_source,
                "ai_prev_decision_source_display": _ai_decision_source_display(self._ai_prev_decision_source),
                "ai_decision_transition": (
                    f"{_ai_decision_source_display(self._ai_prev_decision_source)} -> "
                    f"{_ai_decision_source_display(self._ai_decision_source)}"
                ),
                "ai_last_errors": self._last_ai_errors,
                "ai_last_fallback_reason": self._last_ai_fallback_reason,
                "ai_structured_decision": self._ai_structured_decision,
                "ai_openclaw_meta": (
                    self._ai_structured_decision.get("_openclaw_meta", {})
                    if isinstance(self._ai_structured_decision, dict)
                    else {}
                ),
                "ai_decision_payload": self._last_ai_decision_payload,
                "ai_decision_payload_openclaw": self._last_ai_decision_payload_openclaw,
                "ai_decision_payload_provider": self._last_ai_decision_payload_provider,
                "ai_report_payload": self._last_ai_report_payload,
                "ai_fallback_count": self._ai_fallback_count,
                "openclaw_enabled": openclaw_enabled,
                "openclaw_bridge_stats": self._bridge_stats,
                "openclaw_bridge_stats_updated": _fmt_ts(self._last_bridge_stats_update),
                "openclaw_runtime_status": openclaw_runtime_status,
                "openclaw_runtime_health": openclaw_runtime_health,
                "confidence_threshold": confidence_threshold,
                "revert_timeout_min": revert_timeout_min,
                "presence_away_min": presence_away_min,
                "presence_return_min": presence_return_min,
                "provider_error_state": provider_error_state,
                "last_control_activity": _fmt_ts(self._runtime_events.get("last_control_activity")),
                "enabled_last_changed": _fmt_ts(self._runtime_events.get("enabled_last_changed")),
                "all_rooms_enabled_last_changed": _fmt_ts(
                    self._runtime_events.get("all_rooms_enabled_last_changed")
                ),
                "presence_eco_enabled": presence_eco_enabled,
                "presence_eco_active": presence_eco_active,
                "presence_eco_last_changed": _fmt_ts(
                    self._runtime_events.get("presence_eco_last_changed")
                    or self._room_runtime.get("__presence__", {}).get("last_change")
                ),
                "comfort_mode_enabled": comfort_mode_enabled,
                "comfort_mode_last_changed": _fmt_ts(
                    self._runtime_events.get("comfort_mode_last_changed")
                ),
                "comfort_mode_status": "Aktiv" if comfort_mode_enabled else "Inaktiv",
                "pid_enabled": pid_enabled,
                "pid_last_changed": _fmt_ts(self._runtime_events.get("pid_last_changed")),
                "pid_status": "Aktiv" if pid_enabled else "Inaktiv",
                "pid_rooms": pid_rows,
                "pid_kp": pid_kp,
                "pid_ki": pid_ki,
                "pid_kd": pid_kd,
                "pid_deadband_c": pid_deadband_c,
                "pid_integral_limit": pid_integral_limit,
                "pid_offset_max_c": pid_offset_max_c,
                "learning_enabled": learning_enabled,
                "learning_last_changed": _fmt_ts(self._runtime_events.get("learning_last_changed")),
                "manual_ai_last_trigger": _fmt_ts(self._runtime_events.get("manual_ai_last_trigger")),
                "manual_report_last_trigger": _fmt_ts(self._runtime_events.get("manual_report_last_trigger")),
                "last_report_generated": _fmt_ts(self._last_report_update),
                "learning_status": "Aktiv" if learning_enabled else "Inaktiv",
                "vacuum_running": vacuum_running,
                "target_base": round(target_base, decimals),
                "outdoor_temp": outdoor_temp,
                "el_price": el_price,
                "gas_price": gas_price,
                "district_heat_price": district_heat_price,
                "district_heat_consumption": district_heat_consumption,
                "gas_consumption": gas_consumption,
                "heat_pump_cheaper": heat_pump_cheaper,
                "cheapest_heat_source": cheapest_heat_source,
                "cheapest_alt_name": cheapest_alt_name,
                "estimated_savings_per_kwh": estimated_savings_per_kwh,
                "estimated_daily_savings": estimated_daily_savings,
                "estimated_monthly_savings": estimated_monthly_savings,
                "price_awareness": price_awareness,
                "heat_pump_cheap_priority_factor": round(heat_pump_cheap_priority_factor, 2),
                "thermostat_handover": thermostat_handover,
                "sensor_error": sensor_error,
                "legacy_conflicts": legacy_conflicts,
                "flow_limited": flow_limited,
                "opening_active": opening_active_any,
                "cold_rooms_count": len(cold_rooms),
                "radiator_help_count": radiator_help_count,
                "focus_room": focus_room,
                "focus_room_delta": focus_room_delta,
                "extra_room": extra_room,
                "house_level": house_level,
                "heating_mode": current_mode,
                "summary_yesterday": yesterday_summary,
                "summary_week": week_summary,
                "max_deficit": round(max_deficit, decimals),
                "max_surplus": round(max_surplus, decimals),
                "unavailable_sensors": unavailable_payload,
                "rooms": rooms_payload,
                "actions": actions_payload,
                "report": report_payload,
                "cold_start_cache_used": cold_start_cache_used,
            }
            
        except Exception as err:  # noqa: BLE001
            LOGGER.exception("AI coordinator refresh failed softly: %s", err)
            try:
                OPENCLAW_RUNTIME_ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
                with OPENCLAW_RUNTIME_ERROR_LOG.open("a", encoding="utf-8") as fh:
                    row = {
                        "stage": "coordinator_exception",
                        "entry_id": self.entry.entry_id,
                        "has_previous_data": bool(previous_data),
                        "error": str(err),
                        "traceback": traceback.format_exc(),
                    }
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            except Exception:
                pass
            with contextlib.suppress(Exception):
                await self.hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "AI Varme Styring runtime-fejl",
                        "message": f"Coordinator refresh fejlede: {err}",
                        "notification_id": f"{DOMAIN}_{self.entry.entry_id}_runtime_error",
                    },
                    blocking=False,
                )
            fallback = dict(previous_data) if isinstance(previous_data, dict) else {}
            fallback.setdefault("updated_at", dt_util.now().strftime("%Y-%m-%d %H:%M:%S"))
            fallback.setdefault("enabled", bool(self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {}).get(RUNTIME_ENABLED, True)))
            fallback.setdefault("legacy_conflicts", [])
            fallback.setdefault("provider_error_state", False)
            fallback.setdefault("sensor_error", False)
            fallback.setdefault("thermostat_handover", False)
            fallback.setdefault("heat_pump_cheap_priority_factor", DEFAULT_HEAT_PUMP_CHEAP_PRIORITY_FACTOR)
            fallback.setdefault("heat_pump_cheap_fan_mode", DEFAULT_HEAT_PUMP_CHEAP_FAN_MODE)
            fallback.setdefault("heat_source_direction_bias", DEFAULT_HEAT_SOURCE_DIRECTION_BIAS)
            fallback.setdefault("cheap_power_radiator_setback_extra_c", DEFAULT_CHEAP_POWER_RADIATOR_SETBACK_EXTRA_C)
            fallback.setdefault("opening_active", False)
            fallback.setdefault("presence_eco_active", False)
            fallback.setdefault("flow_limited", False)
            fallback.setdefault("ai_fallback_count", self._ai_fallback_count)
            fallback.setdefault("ai_structured_decision", self._ai_structured_decision if isinstance(self._ai_structured_decision, dict) else {})
            fallback.setdefault("ai_openclaw_meta", fallback.get("ai_openclaw_meta", {}))
            fallback.setdefault("ai_prev_factor", self._ai_prev_factor)
            fallback.setdefault("ai_prev_reason", self._ai_prev_reason)
            fallback.setdefault("ai_prev_confidence", self._ai_prev_confidence)
            fallback.setdefault("ai_prev_decision_source", self._ai_prev_decision_source)
            fallback.setdefault(
                "ai_prev_decision_source_display",
                _ai_decision_source_display(self._ai_prev_decision_source),
            )
            fallback.setdefault(
                "ai_decision_transition",
                f"{_ai_decision_source_display(self._ai_prev_decision_source)} -> "
                f"{_ai_decision_source_display(str(fallback.get('ai_decision_source', self._ai_decision_source)))}",
            )
            fallback.setdefault("rooms", fallback.get("rooms", []))
            fallback.setdefault("actions", [])
            fallback.setdefault("report", fallback.get("report", {"short": "Afventer data", "long": "Afventer data", "bullets": []}))
            fallback.setdefault("ai_primary_engine", fallback.get("ai_primary_engine"))
            fallback.setdefault("ai_primary_engine_display", fallback.get("ai_primary_engine_display"))
            fallback.setdefault("ai_decision_source", fallback.get("ai_decision_source"))
            fallback.setdefault("ai_decision_source_display", fallback.get("ai_decision_source_display"))
            fallback.setdefault("openclaw_enabled", fallback.get("openclaw_enabled", False))
            fallback["actions"] = list(fallback.get("actions", []))[-24:] + [f"AI styringsfejl: {err}"]
            return fallback
