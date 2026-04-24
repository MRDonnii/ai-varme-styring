"""AI Varme Styring integration."""

from __future__ import annotations

import json
import os
import re
import traceback
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    DEFAULT_ECO_TARGET_C,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_GLOBAL_TARGET_C,
    DEFAULT_ENABLE_PID_LAYER,
    DEFAULT_ENABLE_LEARNING,
    DEFAULT_ENABLE_PRESENCE_ECO,
    DEFAULT_PID_DEADBAND_C,
    DEFAULT_PID_INTEGRAL_LIMIT,
    DEFAULT_PID_KD,
    DEFAULT_PID_KI,
    DEFAULT_PID_KP,
    DEFAULT_PID_OFFSET_MAX_C,
    DEFAULT_PRESENCE_AWAY_MIN,
    DEFAULT_PRESENCE_RETURN_MIN,
    DEFAULT_REVERT_TIMEOUT_MIN,
    CONF_CONFIDENCE_THRESHOLD,
    CONF_ENABLE_PID_LAYER,
    CONF_ENABLE_LEARNING,
    CONF_ENABLE_PRESENCE_ECO,
    CONF_ROOMS,
    CONF_ROOM_NAME,
    CONF_ROOM_TARGET_NUMBER,
    CONF_PID_DEADBAND_C,
    CONF_PID_INTEGRAL_LIMIT,
    CONF_PID_KD,
    CONF_PID_KI,
    CONF_PID_KP,
    CONF_PID_OFFSET_MAX_C,
    CONF_PRESENCE_AWAY_MIN,
    CONF_PRESENCE_RETURN_MIN,
    CONF_REVERT_TIMEOUT_MIN,
    DOMAIN,
    PLATFORMS,
    RUNTIME_ECO_TARGET,
    RUNTIME_ENABLED,
    RUNTIME_CONFIDENCE_THRESHOLD,
    RUNTIME_GLOBAL_TARGET,
    RUNTIME_PID_LAYER_ENABLED,
    RUNTIME_PID_DEADBAND_C,
    RUNTIME_PID_INTEGRAL_LIMIT,
    RUNTIME_PID_KD,
    RUNTIME_PID_KI,
    RUNTIME_PID_KP,
    RUNTIME_PID_OFFSET_MAX_C,
    RUNTIME_PRESENCE_AWAY_MIN,
    RUNTIME_PRESENCE_RETURN_MIN,
    RUNTIME_REVERT_TIMEOUT_MIN,
    RUNTIME_PRESENCE_ECO_ENABLED,
    RUNTIME_LEARNING_ENABLED,
    RUNTIME_COMFORT_MODE_ENABLED,
)
from .coordinator import AiVarmeCoordinator


OPENCLAW_RUNTIME_TMP_DIR = Path(
    os.environ.get("OPENCLAW_RUNTIME_TMP_DIR", "/config/custom_components/ai_varme_styring/runtime/tmp")
)
_TRACE_FILE = OPENCLAW_RUNTIME_TMP_DIR / "ai_varme_setup_trace.log"


def _write_setup_trace(stage: str, **payload: object) -> None:
    try:
        row = {"stage": stage, **payload}
        _TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _TRACE_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _room_slug(room_name: str) -> str:
    normalized = str(room_name or "").lower()
    normalized = normalized.replace("\u00e6", "ae").replace("\u00f8", "oe").replace("\u00e5", "aa")
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return normalized or "rum"


def _find_target_helper_entity(hass: HomeAssistant, room_name: str) -> str:
    slug = _room_slug(room_name)
    preferred = [
        f"input_number.thermostat_{slug}_target",
        f"input_number.{slug}_temperature_target",
        f"input_number.ai_varme_target_{slug}",
        f"input_number.{slug}",
    ]
    for entity_id in preferred:
        if hass.states.get(entity_id) is not None:
            return entity_id

    for st in hass.states.async_all("input_number"):
        eid = str(getattr(st, "entity_id", "") or "").lower()
        if slug in eid and ("target" in eid or "temperature" in eid or "temp" in eid):
            return st.entity_id
    return ""


async def _async_create_target_helper(hass: HomeAssistant, room_name: str) -> str:
    if not hass.services.has_service("input_number", "create"):
        return ""

    slug = _room_slug(room_name)
    before = {st.entity_id for st in hass.states.async_all("input_number")}
    service_data = {
        "name": f"AI Varme {room_name} target",
        "min": 10.0,
        "max": 30.0,
        "step": 0.5,
        "mode": "box",
        "icon": "mdi:target",
    }
    try:
        await hass.services.async_call(
            "input_number",
            "create",
            service_data,
            blocking=True,
        )
    except Exception as err:  # noqa: BLE001
        _write_setup_trace("helper_create_failed", room=room_name, error=str(err))
        return ""

    after = {st.entity_id for st in hass.states.async_all("input_number")}
    created = sorted(after - before)
    if created:
        for entity_id in created:
            if slug in entity_id.lower():
                return entity_id
        return created[0]

    return _find_target_helper_entity(hass, room_name)


async def _async_ensure_room_target_helpers(hass: HomeAssistant, entry: ConfigEntry) -> None:
    cfg = {**entry.data, **entry.options}
    rooms = cfg.get(CONF_ROOMS, [])
    if not isinstance(rooms, list) or not rooms:
        return

    changed = False
    updated_rooms: list[dict[str, Any]] = []
    for room_cfg in rooms:
        if not isinstance(room_cfg, dict):
            continue

        room_copy = dict(room_cfg)
        room_name = str(room_copy.get(CONF_ROOM_NAME, "")).strip()
        if not room_name:
            updated_rooms.append(room_copy)
            continue

        current_target = str(room_copy.get(CONF_ROOM_TARGET_NUMBER, "") or "").strip()
        if current_target and hass.states.get(current_target) is not None:
            updated_rooms.append(room_copy)
            continue

        resolved = _find_target_helper_entity(hass, room_name)
        if not resolved:
            resolved = await _async_create_target_helper(hass, room_name)
        if resolved:
            room_copy[CONF_ROOM_TARGET_NUMBER] = resolved
            changed = True
            _write_setup_trace("helper_linked", room=room_name, helper=resolved)
        else:
            _write_setup_trace("helper_missing", room=room_name)

        updated_rooms.append(room_copy)

    if not changed:
        return

    new_options = dict(entry.options)
    new_options[CONF_ROOMS] = updated_rooms
    hass.config_entries.async_update_entry(entry, options=new_options)
    _write_setup_trace("helpers_options_updated", entry_id=entry.entry_id)


async def _async_remove_deprecated_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove legacy master-level entities that were moved to room level."""
    registry = er.async_get(hass)
    deprecated_unique_ids = {
        f"{entry.entry_id}_global_target",
        f"{entry.entry_id}_eco_target",
        f"{entry.entry_id}_presence_away_min",
        f"{entry.entry_id}_presence_return_min",
    }
    for ent in er.async_entries_for_config_entry(registry, entry.entry_id):
        if ent.unique_id in deprecated_unique_ids:
            registry.async_remove(ent.entity_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AI Varme Styring from config entry."""
    _write_setup_trace("setup_entry_start", entry_id=entry.entry_id, title=entry.title)
    cfg = {**entry.data, **entry.options}
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        RUNTIME_ENABLED: True,
        RUNTIME_GLOBAL_TARGET: DEFAULT_GLOBAL_TARGET_C,
        RUNTIME_ECO_TARGET: DEFAULT_ECO_TARGET_C,
        RUNTIME_PRESENCE_ECO_ENABLED: bool(
            cfg.get(CONF_ENABLE_PRESENCE_ECO, DEFAULT_ENABLE_PRESENCE_ECO)
        ),
        RUNTIME_PID_LAYER_ENABLED: bool(
            cfg.get(CONF_ENABLE_PID_LAYER, DEFAULT_ENABLE_PID_LAYER)
        ),
        RUNTIME_LEARNING_ENABLED: bool(
            cfg.get(CONF_ENABLE_LEARNING, DEFAULT_ENABLE_LEARNING)
        ),
        RUNTIME_COMFORT_MODE_ENABLED: False,
        RUNTIME_PRESENCE_AWAY_MIN: float(
            cfg.get(CONF_PRESENCE_AWAY_MIN, DEFAULT_PRESENCE_AWAY_MIN)
        ),
        RUNTIME_PRESENCE_RETURN_MIN: float(
            cfg.get(CONF_PRESENCE_RETURN_MIN, DEFAULT_PRESENCE_RETURN_MIN)
        ),
        RUNTIME_PID_KP: float(cfg.get(CONF_PID_KP, DEFAULT_PID_KP)),
        RUNTIME_PID_KI: float(cfg.get(CONF_PID_KI, DEFAULT_PID_KI)),
        RUNTIME_PID_KD: float(cfg.get(CONF_PID_KD, DEFAULT_PID_KD)),
        RUNTIME_PID_DEADBAND_C: float(
            cfg.get(CONF_PID_DEADBAND_C, DEFAULT_PID_DEADBAND_C)
        ),
        RUNTIME_PID_INTEGRAL_LIMIT: float(
            cfg.get(CONF_PID_INTEGRAL_LIMIT, DEFAULT_PID_INTEGRAL_LIMIT)
        ),
        RUNTIME_PID_OFFSET_MAX_C: float(
            cfg.get(CONF_PID_OFFSET_MAX_C, DEFAULT_PID_OFFSET_MAX_C)
        ),
        RUNTIME_CONFIDENCE_THRESHOLD: float(
            cfg.get(CONF_CONFIDENCE_THRESHOLD, DEFAULT_CONFIDENCE_THRESHOLD)
        ),
        RUNTIME_REVERT_TIMEOUT_MIN: float(
            cfg.get(CONF_REVERT_TIMEOUT_MIN, DEFAULT_REVERT_TIMEOUT_MIN)
        ),
    }
    coordinator = AiVarmeCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator
    _write_setup_trace("before_first_refresh", entry_id=entry.entry_id)
    try:
        await coordinator.async_config_entry_first_refresh()
        _write_setup_trace("after_first_refresh", entry_id=entry.entry_id, has_data=isinstance(coordinator.data, dict))
    except Exception as err:
        _write_setup_trace("first_refresh_error", entry_id=entry.entry_id, error=str(err), traceback=traceback.format_exc())
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "AI Varme Styring setup-fejl",
                "message": f"Forste refresh fejlede: {err}",
                "notification_id": f"{DOMAIN}_{entry.entry_id}_setup_error",
            },
            blocking=False,
        )
        raise

    await _async_ensure_room_target_helpers(hass, entry)
    await _async_remove_deprecated_entities(hass, entry)

    await hass.config_entries.async_forward_entry_setups(
        entry, [Platform(p) for p in PLATFORMS]
    )
    _write_setup_trace("after_forward_entry_setups", entry_id=entry.entry_id)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: AiVarmeCoordinator = data["coordinator"]
    await coordinator.async_request_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [Platform(p) for p in PLATFORMS]
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
