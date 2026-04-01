"""AI Varme Styring integration."""

from __future__ import annotations

import json
import os
import traceback
from pathlib import Path

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
)
from .coordinator import AiVarmeCoordinator


OPENCLAW_RUNTIME_TMP_DIR = Path(
    os.environ.get("OPENCLAW_RUNTIME_TMP_DIR", "/config/tools/openclaw_runtime/tmp")
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
                "message": f"Første refresh fejlede: {err}",
                "notification_id": f"{DOMAIN}_{entry.entry_id}_setup_error",
            },
            blocking=False,
        )
        raise
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
