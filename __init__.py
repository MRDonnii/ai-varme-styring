"""AI Varme Styring integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    DEFAULT_ECO_TARGET_C,
    DEFAULT_GLOBAL_TARGET_C,
    DEFAULT_ENABLE_PID_LAYER,
    DEFAULT_ENABLE_LEARNING,
    DEFAULT_ENABLE_PRESENCE_ECO,
    CONF_ENABLE_PID_LAYER,
    CONF_ENABLE_LEARNING,
    CONF_ENABLE_PRESENCE_ECO,
    DOMAIN,
    PLATFORMS,
    RUNTIME_ECO_TARGET,
    RUNTIME_ENABLED,
    RUNTIME_GLOBAL_TARGET,
    RUNTIME_PID_LAYER_ENABLED,
    RUNTIME_PRESENCE_ECO_ENABLED,
    RUNTIME_LEARNING_ENABLED,
)
from .coordinator import AiVarmeCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AI Varme Styring from config entry."""
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
    }
    coordinator = AiVarmeCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(
        entry, [Platform(p) for p in PLATFORMS]
    )
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
