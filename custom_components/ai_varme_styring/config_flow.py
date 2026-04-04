"""Config flow for AI Varme Styring."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import (
    AI_DECISION_ENGINE_OPTIONS,
    AI_ENGINE_NONE,
    AI_FALLBACK_ENGINE_OPTIONS,
    AI_PROVIDER_GEMINI,
    AI_PRIMARY_ENGINE_OPTIONS,
    AI_PRIMARY_ENGINE_OPENCLAW,
    AI_PROVIDER_OLLAMA,
    AI_PROVIDER_OPTIONS,
    CONF_AI_PRIMARY_ENGINE,
    CONF_AI_FALLBACK_ENGINE,
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
    CONF_NAME,
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
    CONF_OLLAMA_HOST,
    CONF_OUTDOOR_TEMP_SENSOR,
    CONF_PID_DEADBAND_C,
    CONF_PID_INTEGRAL_LIMIT,
    CONF_PID_KD,
    CONF_PID_KI,
    CONF_PID_KP,
    CONF_PID_OFFSET_MAX_C,
    CONF_PRESENCE_AWAY_MIN,
    CONF_PRESENCE_RETURN_MIN,
    CONF_PRICE_MARGIN,
    CONF_PROVIDER_PAYLOAD_PROFILE,
    CONF_RADIATOR_BOOST_C,
    CONF_RADIATOR_SETBACK_C,
    CONF_REVERT_TIMEOUT_MIN,
    CONF_REPORT_INTERVAL_MIN,
    CONF_ROOMS,
    CONF_ROOM_AREA_ID,
    CONF_ROOM_HEAT_PUMP,
    CONF_ROOM_HUMIDITY_SENSOR,
    CONF_ROOM_HEAT_PUMP_POWER_SENSOR,
    CONF_ROOM_NAME,
    CONF_ROOM_OCCUPANCY_SENSORS,
    CONF_ROOM_ENABLE_PRESENCE_ECO,
    CONF_ROOM_ENABLE_LEARNING,
    CONF_ROOM_ENABLE_OPENING_PAUSE,
    CONF_ROOM_OPENING_SENSORS,
    CONF_ROOM_RADIATORS,
    CONF_ROOM_ANTI_SHORT_CYCLE_MIN,
    CONF_ROOM_LINK_GROUP,
    CONF_ROOM_MASSIVE_OVERHEAT_C,
    CONF_ROOM_MASSIVE_OVERHEAT_MIN,
    CONF_ROOM_PAUSE_AFTER_OPEN_MIN,
    CONF_ROOM_QUICK_START_DEFICIT_C,
    CONF_ROOM_START_DEFICIT_C,
    CONF_ROOM_STOP_SURPLUS_C,
    CONF_ROOM_RESUME_AFTER_CLOSED_MIN,
    CONF_ROOM_SENSOR_BIAS_C,
    CONF_ROOM_TARGET_STEP_C,
    CONF_ROOM_TARGET_NUMBER,
    CONF_ROOM_TEMP_SENSOR,
    CONF_START_DEFICIT_C,
    CONF_STOP_SURPLUS_C,
    CONF_UPDATE_SECONDS,
    CONF_VACUUM_ENTITY,
    CONF_WEATHER_ENTITY,
    DEFAULT_AI_MODEL_FAST,
    DEFAULT_AI_MODEL_REPORT,
    DEFAULT_AI_FALLBACK_ENGINE,
    DEFAULT_AI_PRIMARY_ENGINE,
    DEFAULT_AI_PROVIDER,
    DEFAULT_AI_REPORT_ENGINE,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_DECIMALS,
    DEFAULT_ENABLE_PID_LAYER,
    DEFAULT_ENABLE_LEARNING,
    DEFAULT_ENABLE_PRESENCE_ECO,
    DEFAULT_ENABLE_PRICE_AWARENESS,
    DEFAULT_FLOW_LIMIT_MARGIN_C,
    DEFAULT_GEMINI_MODEL_FAST,
    DEFAULT_GEMINI_MODEL_REPORT,
    DEFAULT_HUMIDITY_COMFORT_ENABLED,
    DEFAULT_HUMIDITY_DRY_THRESHOLD,
    DEFAULT_HUMIDITY_HUMID_THRESHOLD,
    DEFAULT_HUMIDITY_MAX_OFFSET_C,
    DEFAULT_NAME,
    DEFAULT_OPENCLAW_ENABLED,
    DEFAULT_OPENCLAW_BRIDGE_URL,
    DEFAULT_OPENCLAW_MODEL_FALLBACK,
    DEFAULT_OPENCLAW_MODEL_PREFERRED,
    DEFAULT_OPENCLAW_ONLY_MODE,
    DEFAULT_OPENCLAW_PAYLOAD_PROFILE,
    DEFAULT_OPENCLAW_TIMEOUT_SEC,
    DEFAULT_OPENCLAW_TOKEN,
    DEFAULT_OPENCLAW_PASSWORD,
    DEFAULT_OPENCLAW_URL,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_PID_DEADBAND_C,
    DEFAULT_PID_INTEGRAL_LIMIT,
    DEFAULT_PID_KD,
    DEFAULT_PID_KI,
    DEFAULT_PID_KP,
    DEFAULT_PID_OFFSET_MAX_C,
    DEFAULT_PRESENCE_AWAY_MIN,
    DEFAULT_PRESENCE_RETURN_MIN,
    DEFAULT_PRICE_MARGIN,
    DEFAULT_PROVIDER_PAYLOAD_PROFILE,
    DEFAULT_RADIATOR_BOOST_C,
    DEFAULT_RADIATOR_SETBACK_C,
    DEFAULT_REVERT_TIMEOUT_MIN,
    DEFAULT_REPORT_INTERVAL_MIN,
    DEFAULT_START_DEFICIT_C,
    DEFAULT_STOP_SURPLUS_C,
    DEFAULT_UPDATE_SECONDS,
    DEFAULT_ROOM_ANTI_SHORT_CYCLE_MIN,
    DEFAULT_ROOM_LINK_GROUP,
    DEFAULT_ROOM_MASSIVE_OVERHEAT_C,
    DEFAULT_ROOM_MASSIVE_OVERHEAT_MIN,
    DEFAULT_ROOM_PAUSE_AFTER_OPEN_MIN,
    DEFAULT_ROOM_QUICK_START_DEFICIT_C,
    DEFAULT_ROOM_START_DEFICIT_C,
    DEFAULT_ROOM_STOP_SURPLUS_C,
    DEFAULT_ROOM_RESUME_AFTER_CLOSED_MIN,
    DEFAULT_ROOM_SENSOR_BIAS_C,
    DEFAULT_ROOM_TARGET_STEP_C,
    DEFAULT_ROOM_ENABLE_PRESENCE_ECO,
    DEFAULT_ROOM_ENABLE_LEARNING,
    DEFAULT_ROOM_ENABLE_OPENING_PAUSE,
    DOMAIN,
    PAYLOAD_PROFILE_OPTIONS,
)


OPENCLAW_MODEL_OPTIONS = [
    "claude-haiku-4.5",
    "claude-opus-4.5",
    "claude-opus-4.6",
    "claude-sonnet-4",
    "claude-sonnet-4.5",
    "claude-sonnet-4.6",
    "gemini-2.5-pro",
    "gemini-3-flash-preview",
    "gemini-3-pro-preview",
    "gemini-3.1-pro-preview",
    "gpt-4.1",
    "gpt-4o",
    "gpt-5",
    "gpt-5-mini",
    "gpt-5.1",
    "gpt-5.1-codex",
    "gpt-5.1-codex-max",
    "gpt-5.1-codex-mini",
    "gpt-5.2",
    "gpt-5.2-codex",
    "gpt-5.3-codex",
    "gpt-5.4",
    "gpt-5.4-mini",
    "grok-code-fast-1",
]

def _entity_selector(domain: str, multiple: bool = False) -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain=domain, multiple=multiple)
    )


def _add_optional_entity_field(
    schema: dict[Any, Any],
    defaults: dict[str, Any],
    key: str,
    domain: str,
    *,
    multiple: bool = False,
) -> None:
    """Add optional entity selector without invalid None default."""
    default = defaults.get(key)
    has_default = default not in (None, "", [])
    field = vol.Optional(key, default=default) if has_default else vol.Optional(key)
    schema[field] = _entity_selector(domain, multiple=multiple)


def _selected_base_values(defaults: dict[str, Any]) -> dict[str, Any]:
    primary_engine = defaults.get(CONF_AI_PRIMARY_ENGINE, DEFAULT_AI_PRIMARY_ENGINE)
    fallback_engine = defaults.get(CONF_AI_FALLBACK_ENGINE, DEFAULT_AI_FALLBACK_ENGINE)
    report_engine = defaults.get(CONF_AI_REPORT_ENGINE, DEFAULT_AI_REPORT_ENGINE)
    provider_default = defaults.get(CONF_AI_PROVIDER, DEFAULT_AI_PROVIDER)
    uses_openclaw = any(
        engine == AI_PRIMARY_ENGINE_OPENCLAW
        for engine in (primary_engine, fallback_engine, report_engine)
    ) or bool(defaults.get(CONF_OPENCLAW_ENABLED, DEFAULT_OPENCLAW_ENABLED))
    uses_ollama = any(
        engine == AI_PROVIDER_OLLAMA for engine in (primary_engine, fallback_engine, report_engine)
    ) or provider_default == AI_PROVIDER_OLLAMA
    uses_gemini = any(
        engine == AI_PROVIDER_GEMINI for engine in (primary_engine, fallback_engine, report_engine)
    ) or provider_default == AI_PROVIDER_GEMINI
    return {
        "provider_default": provider_default,
        "primary_engine": primary_engine,
        "fallback_engine": fallback_engine,
        "report_engine": report_engine,
        "uses_openclaw": uses_openclaw,
        "uses_ollama": uses_ollama,
        "uses_gemini": uses_gemini,
    }


def _merge_visible_input(existing: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    merged.update(updates)
    return merged


def _base_schema(defaults: dict[str, Any]) -> vol.Schema:
    selected = _selected_base_values(defaults)
    provider_default = selected["provider_default"]
    schema: dict[Any, Any] = {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(
                CONF_AI_PRIMARY_ENGINE,
                default=selected["primary_engine"],
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=AI_DECISION_ENGINE_OPTIONS, mode=selector.SelectSelectorMode.DROPDOWN
                )
            ),
            vol.Required(
                CONF_AI_FALLBACK_ENGINE,
                default=selected["fallback_engine"],
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=AI_FALLBACK_ENGINE_OPTIONS, mode=selector.SelectSelectorMode.DROPDOWN
                )
            ),
            vol.Required(
                CONF_AI_REPORT_ENGINE,
                default=selected["report_engine"],
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=AI_DECISION_ENGINE_OPTIONS, mode=selector.SelectSelectorMode.DROPDOWN
                )
            ),
            vol.Required(
                CONF_REPORT_INTERVAL_MIN,
                default=defaults.get(CONF_REPORT_INTERVAL_MIN, DEFAULT_REPORT_INTERVAL_MIN),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=30, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_ENABLE_PRICE_AWARENESS,
                default=defaults.get(
                    CONF_ENABLE_PRICE_AWARENESS, DEFAULT_ENABLE_PRICE_AWARENESS
                ),
            ): bool,
            vol.Required(
                CONF_ENABLE_PRESENCE_ECO,
                default=defaults.get(CONF_ENABLE_PRESENCE_ECO, DEFAULT_ENABLE_PRESENCE_ECO),
            ): bool,
            vol.Required(
                CONF_PRESENCE_AWAY_MIN,
                default=defaults.get(CONF_PRESENCE_AWAY_MIN, DEFAULT_PRESENCE_AWAY_MIN),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=240, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_PRESENCE_RETURN_MIN,
                default=defaults.get(CONF_PRESENCE_RETURN_MIN, DEFAULT_PRESENCE_RETURN_MIN),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=120, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_ENABLE_PID_LAYER,
                default=defaults.get(CONF_ENABLE_PID_LAYER, DEFAULT_ENABLE_PID_LAYER),
            ): bool,
            vol.Required(
                CONF_ENABLE_LEARNING,
                default=defaults.get(CONF_ENABLE_LEARNING, DEFAULT_ENABLE_LEARNING),
            ): bool,
            vol.Required(
                CONF_HUMIDITY_COMFORT_ENABLED,
                default=defaults.get(CONF_HUMIDITY_COMFORT_ENABLED, DEFAULT_HUMIDITY_COMFORT_ENABLED),
            ): bool,
            vol.Required(
                CONF_HUMIDITY_DRY_THRESHOLD,
                default=defaults.get(CONF_HUMIDITY_DRY_THRESHOLD, DEFAULT_HUMIDITY_DRY_THRESHOLD),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=10, max=60, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_HUMIDITY_HUMID_THRESHOLD,
                default=defaults.get(CONF_HUMIDITY_HUMID_THRESHOLD, DEFAULT_HUMIDITY_HUMID_THRESHOLD),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=40, max=90, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_HUMIDITY_MAX_OFFSET_C,
                default=defaults.get(CONF_HUMIDITY_MAX_OFFSET_C, DEFAULT_HUMIDITY_MAX_OFFSET_C),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=1.5, step=0.05, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_PID_KP,
                default=defaults.get(CONF_PID_KP, DEFAULT_PID_KP),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=5, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_PID_KI,
                default=defaults.get(CONF_PID_KI, DEFAULT_PID_KI),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=1, step=0.01, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_PID_KD,
                default=defaults.get(CONF_PID_KD, DEFAULT_PID_KD),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=2, step=0.05, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_PID_DEADBAND_C,
                default=defaults.get(CONF_PID_DEADBAND_C, DEFAULT_PID_DEADBAND_C),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=1, step=0.05, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_PID_INTEGRAL_LIMIT,
                default=defaults.get(CONF_PID_INTEGRAL_LIMIT, DEFAULT_PID_INTEGRAL_LIMIT),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=10, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_PID_OFFSET_MAX_C,
                default=defaults.get(CONF_PID_OFFSET_MAX_C, DEFAULT_PID_OFFSET_MAX_C),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=3, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_CONFIDENCE_THRESHOLD,
                default=defaults.get(CONF_CONFIDENCE_THRESHOLD, DEFAULT_CONFIDENCE_THRESHOLD),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=50, max=100, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_REVERT_TIMEOUT_MIN,
                default=defaults.get(CONF_REVERT_TIMEOUT_MIN, DEFAULT_REVERT_TIMEOUT_MIN),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=5, max=180, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_PRICE_MARGIN,
                default=defaults.get(CONF_PRICE_MARGIN, DEFAULT_PRICE_MARGIN),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=5, step=0.01, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_START_DEFICIT_C,
                default=defaults.get(CONF_START_DEFICIT_C, DEFAULT_START_DEFICIT_C),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=5, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_STOP_SURPLUS_C,
                default=defaults.get(CONF_STOP_SURPLUS_C, DEFAULT_STOP_SURPLUS_C),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=5, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_FLOW_LIMIT_MARGIN_C,
                default=defaults.get(
                    CONF_FLOW_LIMIT_MARGIN_C, DEFAULT_FLOW_LIMIT_MARGIN_C
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=3, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_RADIATOR_BOOST_C,
                default=defaults.get(CONF_RADIATOR_BOOST_C, DEFAULT_RADIATOR_BOOST_C),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=3, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_RADIATOR_SETBACK_C,
                default=defaults.get(CONF_RADIATOR_SETBACK_C, DEFAULT_RADIATOR_SETBACK_C),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=6, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_UPDATE_SECONDS,
                default=defaults.get(CONF_UPDATE_SECONDS, DEFAULT_UPDATE_SECONDS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=10, max=600, step=5, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_DECIMALS, default=defaults.get(CONF_DECIMALS, DEFAULT_DECIMALS)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=3, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_ROOM_TARGET_STEP_C,
                default=defaults.get(CONF_ROOM_TARGET_STEP_C, DEFAULT_ROOM_TARGET_STEP_C),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0.5, max=1.0, step=0.5, mode=selector.NumberSelectorMode.BOX)
            ),
        }
    if selected["uses_ollama"]:
        schema[vol.Optional(
            CONF_OLLAMA_HOST,
            default=defaults.get(CONF_OLLAMA_HOST, DEFAULT_OLLAMA_HOST),
        )] = str
        schema[vol.Optional(
            CONF_AI_MODEL_FAST,
            default=defaults.get(CONF_AI_MODEL_FAST, DEFAULT_AI_MODEL_FAST),
        )] = str
        schema[vol.Optional(
            CONF_AI_MODEL_REPORT,
            default=defaults.get(CONF_AI_MODEL_REPORT, DEFAULT_AI_MODEL_REPORT),
        )] = str
    if selected["uses_gemini"]:
        schema[vol.Optional(
            CONF_GEMINI_API_KEY, default=defaults.get(CONF_GEMINI_API_KEY, "")
        )] = selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        )
        schema[vol.Optional(
            CONF_GEMINI_MODEL_FAST,
            default=defaults.get(CONF_GEMINI_MODEL_FAST, DEFAULT_GEMINI_MODEL_FAST),
        )] = str
        schema[vol.Optional(
            CONF_GEMINI_MODEL_REPORT,
            default=defaults.get(CONF_GEMINI_MODEL_REPORT, DEFAULT_GEMINI_MODEL_REPORT),
        )] = str
    if selected["uses_openclaw"]:
        schema[vol.Optional(
            CONF_OPENCLAW_URL,
            default=defaults.get(CONF_OPENCLAW_URL, DEFAULT_OPENCLAW_URL),
        )] = str
        schema[vol.Optional(
            CONF_OPENCLAW_TOKEN,
            default=defaults.get(CONF_OPENCLAW_TOKEN, DEFAULT_OPENCLAW_TOKEN),
        )] = selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        )
        schema[vol.Optional(
            CONF_OPENCLAW_PASSWORD,
            default=defaults.get(CONF_OPENCLAW_PASSWORD, DEFAULT_OPENCLAW_PASSWORD),
        )] = selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        )
        schema[vol.Optional(
            CONF_OPENCLAW_MODEL_PREFERRED,
            default=defaults.get(CONF_OPENCLAW_MODEL_PREFERRED, DEFAULT_OPENCLAW_MODEL_PREFERRED),
        )] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=OPENCLAW_MODEL_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
        schema[vol.Optional(
            CONF_OPENCLAW_MODEL_FALLBACK,
            default=defaults.get(CONF_OPENCLAW_MODEL_FALLBACK, DEFAULT_OPENCLAW_MODEL_FALLBACK),
        )] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=OPENCLAW_MODEL_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
    _add_optional_entity_field(schema, defaults, CONF_OUTDOOR_TEMP_SENSOR, "sensor")
    _add_optional_entity_field(schema, defaults, CONF_WEATHER_ENTITY, "weather")
    _add_optional_entity_field(schema, defaults, CONF_ELECTRICITY_PRICE_SENSOR, "sensor")
    _add_optional_entity_field(schema, defaults, CONF_GAS_PRICE_SENSOR, "sensor")
    _add_optional_entity_field(schema, defaults, CONF_DISTRICT_HEAT_PRICE_SENSOR, "sensor")
    _add_optional_entity_field(schema, defaults, CONF_DISTRICT_HEAT_CONSUMPTION_SENSOR, "sensor")
    _add_optional_entity_field(schema, defaults, CONF_GAS_CONSUMPTION_SENSOR, "sensor")
    _add_optional_entity_field(schema, defaults, CONF_VACUUM_ENTITY, "vacuum")
    return vol.Schema(schema)


def _general_options_schema(defaults: dict[str, Any]) -> vol.Schema:
    schema: dict[Any, Any] = {
        vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
        vol.Required(
            CONF_REPORT_INTERVAL_MIN,
            default=defaults.get(CONF_REPORT_INTERVAL_MIN, DEFAULT_REPORT_INTERVAL_MIN),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=30, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_ENABLE_PRICE_AWARENESS,
            default=defaults.get(CONF_ENABLE_PRICE_AWARENESS, DEFAULT_ENABLE_PRICE_AWARENESS),
        ): bool,
        vol.Required(
            CONF_ENABLE_PRESENCE_ECO,
            default=defaults.get(CONF_ENABLE_PRESENCE_ECO, DEFAULT_ENABLE_PRESENCE_ECO),
        ): bool,
        vol.Required(
            CONF_PRESENCE_AWAY_MIN,
            default=defaults.get(CONF_PRESENCE_AWAY_MIN, DEFAULT_PRESENCE_AWAY_MIN),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=240, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_PRESENCE_RETURN_MIN,
            default=defaults.get(CONF_PRESENCE_RETURN_MIN, DEFAULT_PRESENCE_RETURN_MIN),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=120, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_ENABLE_PID_LAYER,
            default=defaults.get(CONF_ENABLE_PID_LAYER, DEFAULT_ENABLE_PID_LAYER),
        ): bool,
        vol.Required(
            CONF_ENABLE_LEARNING,
                default=defaults.get(CONF_ENABLE_LEARNING, DEFAULT_ENABLE_LEARNING),
        ): bool,
        vol.Required(
            CONF_HUMIDITY_COMFORT_ENABLED,
            default=defaults.get(CONF_HUMIDITY_COMFORT_ENABLED, DEFAULT_HUMIDITY_COMFORT_ENABLED),
        ): bool,
        vol.Required(
            CONF_HUMIDITY_DRY_THRESHOLD,
            default=defaults.get(CONF_HUMIDITY_DRY_THRESHOLD, DEFAULT_HUMIDITY_DRY_THRESHOLD),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=10, max=60, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_HUMIDITY_HUMID_THRESHOLD,
            default=defaults.get(CONF_HUMIDITY_HUMID_THRESHOLD, DEFAULT_HUMIDITY_HUMID_THRESHOLD),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=40, max=90, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_HUMIDITY_MAX_OFFSET_C,
            default=defaults.get(CONF_HUMIDITY_MAX_OFFSET_C, DEFAULT_HUMIDITY_MAX_OFFSET_C),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=1.5, step=0.05, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_DECIMALS,
            default=defaults.get(CONF_DECIMALS, DEFAULT_DECIMALS),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=3, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_ROOM_TARGET_STEP_C,
            default=defaults.get(CONF_ROOM_TARGET_STEP_C, DEFAULT_ROOM_TARGET_STEP_C),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0.5, max=1.0, step=0.5, mode=selector.NumberSelectorMode.BOX)
        ),
    }
    _add_optional_entity_field(schema, defaults, CONF_OUTDOOR_TEMP_SENSOR, "sensor")
    _add_optional_entity_field(schema, defaults, CONF_WEATHER_ENTITY, "weather")
    _add_optional_entity_field(schema, defaults, CONF_ELECTRICITY_PRICE_SENSOR, "sensor")
    _add_optional_entity_field(schema, defaults, CONF_GAS_PRICE_SENSOR, "sensor")
    _add_optional_entity_field(schema, defaults, CONF_DISTRICT_HEAT_PRICE_SENSOR, "sensor")
    _add_optional_entity_field(schema, defaults, CONF_DISTRICT_HEAT_CONSUMPTION_SENSOR, "sensor")
    _add_optional_entity_field(schema, defaults, CONF_GAS_CONSUMPTION_SENSOR, "sensor")
    _add_optional_entity_field(schema, defaults, CONF_VACUUM_ENTITY, "vacuum")
    return vol.Schema(schema)


def _advanced_options_schema(defaults: dict[str, Any]) -> vol.Schema:
    selected = _selected_base_values(defaults)
    schema: dict[Any, Any] = {
        vol.Required(
            CONF_PID_KP,
            default=defaults.get(CONF_PID_KP, DEFAULT_PID_KP),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=5, step=0.1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_PID_KI,
            default=defaults.get(CONF_PID_KI, DEFAULT_PID_KI),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=1, step=0.01, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_PID_KD,
            default=defaults.get(CONF_PID_KD, DEFAULT_PID_KD),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=2, step=0.05, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_PID_DEADBAND_C,
            default=defaults.get(CONF_PID_DEADBAND_C, DEFAULT_PID_DEADBAND_C),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=1, step=0.05, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_PID_INTEGRAL_LIMIT,
            default=defaults.get(CONF_PID_INTEGRAL_LIMIT, DEFAULT_PID_INTEGRAL_LIMIT),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=10, step=0.1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_PID_OFFSET_MAX_C,
            default=defaults.get(CONF_PID_OFFSET_MAX_C, DEFAULT_PID_OFFSET_MAX_C),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=3, step=0.1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_CONFIDENCE_THRESHOLD,
            default=defaults.get(CONF_CONFIDENCE_THRESHOLD, DEFAULT_CONFIDENCE_THRESHOLD),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=50, max=100, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_REVERT_TIMEOUT_MIN,
            default=defaults.get(CONF_REVERT_TIMEOUT_MIN, DEFAULT_REVERT_TIMEOUT_MIN),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=5, max=180, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_PRICE_MARGIN,
            default=defaults.get(CONF_PRICE_MARGIN, DEFAULT_PRICE_MARGIN),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=5, step=0.01, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(
            CONF_START_DEFICIT_C,
            default=defaults.get(CONF_START_DEFICIT_C, DEFAULT_START_DEFICIT_C),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=5, step=0.1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(
            CONF_STOP_SURPLUS_C,
            default=defaults.get(CONF_STOP_SURPLUS_C, DEFAULT_STOP_SURPLUS_C),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=5, step=0.1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_FLOW_LIMIT_MARGIN_C,
            default=defaults.get(CONF_FLOW_LIMIT_MARGIN_C, DEFAULT_FLOW_LIMIT_MARGIN_C),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=3, step=0.1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_RADIATOR_BOOST_C,
            default=defaults.get(CONF_RADIATOR_BOOST_C, DEFAULT_RADIATOR_BOOST_C),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=3, step=0.1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_RADIATOR_SETBACK_C,
            default=defaults.get(CONF_RADIATOR_SETBACK_C, DEFAULT_RADIATOR_SETBACK_C),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=6, step=0.1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_UPDATE_SECONDS,
            default=defaults.get(CONF_UPDATE_SECONDS, DEFAULT_UPDATE_SECONDS),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=10, max=600, step=5, mode=selector.NumberSelectorMode.BOX)
        ),
    }
    if selected["uses_ollama"] or selected["uses_gemini"]:
        schema[vol.Required(
            CONF_PROVIDER_PAYLOAD_PROFILE,
            default=defaults.get(CONF_PROVIDER_PAYLOAD_PROFILE, DEFAULT_PROVIDER_PAYLOAD_PROFILE),
        )] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=PAYLOAD_PROFILE_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
    if selected["uses_openclaw"]:
        schema[vol.Optional(
            CONF_OPENCLAW_BRIDGE_URL,
            default=defaults.get(CONF_OPENCLAW_BRIDGE_URL, DEFAULT_OPENCLAW_BRIDGE_URL),
        )] = str
        schema[vol.Optional(
            CONF_OPENCLAW_TIMEOUT_SEC,
            default=defaults.get(CONF_OPENCLAW_TIMEOUT_SEC, DEFAULT_OPENCLAW_TIMEOUT_SEC),
        )] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=3, max=30, step=1, mode=selector.NumberSelectorMode.BOX)
        )
        schema[vol.Required(
            CONF_OPENCLAW_PAYLOAD_PROFILE,
            default=defaults.get(CONF_OPENCLAW_PAYLOAD_PROFILE, DEFAULT_OPENCLAW_PAYLOAD_PROFILE),
        )] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=PAYLOAD_PROFILE_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
    return vol.Schema(schema)


def _providers_schema(defaults: dict[str, Any]) -> vol.Schema:
    selected = _selected_base_values(defaults)
    schema: dict[Any, Any] = {
        vol.Required(
            CONF_AI_PRIMARY_ENGINE,
            default=selected["primary_engine"],
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=AI_DECISION_ENGINE_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(
            CONF_AI_FALLBACK_ENGINE,
            default=selected["fallback_engine"],
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=AI_FALLBACK_ENGINE_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(
            CONF_AI_REPORT_ENGINE,
            default=selected["report_engine"],
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=AI_DECISION_ENGINE_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
    }
    if selected["uses_ollama"]:
        schema[vol.Optional(
            CONF_OLLAMA_HOST,
            default=defaults.get(CONF_OLLAMA_HOST, DEFAULT_OLLAMA_HOST),
        )] = str
        schema[vol.Optional(
            CONF_AI_MODEL_FAST,
            default=defaults.get(CONF_AI_MODEL_FAST, DEFAULT_AI_MODEL_FAST),
        )] = str
        schema[vol.Optional(
            CONF_AI_MODEL_REPORT,
            default=defaults.get(CONF_AI_MODEL_REPORT, DEFAULT_AI_MODEL_REPORT),
        )] = str
    if selected["uses_gemini"]:
        schema[vol.Optional(
            CONF_GEMINI_API_KEY,
            default=defaults.get(CONF_GEMINI_API_KEY, ""),
        )] = selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        )
        schema[vol.Optional(
            CONF_GEMINI_MODEL_FAST,
            default=defaults.get(CONF_GEMINI_MODEL_FAST, DEFAULT_GEMINI_MODEL_FAST),
        )] = str
        schema[vol.Optional(
            CONF_GEMINI_MODEL_REPORT,
            default=defaults.get(CONF_GEMINI_MODEL_REPORT, DEFAULT_GEMINI_MODEL_REPORT),
        )] = str
    if selected["uses_openclaw"]:
        schema[vol.Optional(
            CONF_OPENCLAW_URL,
            default=defaults.get(CONF_OPENCLAW_URL, DEFAULT_OPENCLAW_URL),
        )] = str
        schema[vol.Optional(
            CONF_OPENCLAW_TOKEN,
            default=defaults.get(CONF_OPENCLAW_TOKEN, DEFAULT_OPENCLAW_TOKEN),
        )] = selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        )
        schema[vol.Optional(
            CONF_OPENCLAW_PASSWORD,
            default=defaults.get(CONF_OPENCLAW_PASSWORD, DEFAULT_OPENCLAW_PASSWORD),
        )] = selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        )
        schema[vol.Optional(
            CONF_OPENCLAW_MODEL_PREFERRED,
            default=defaults.get(CONF_OPENCLAW_MODEL_PREFERRED, DEFAULT_OPENCLAW_MODEL_PREFERRED),
        )] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=OPENCLAW_MODEL_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
        schema[vol.Optional(
            CONF_OPENCLAW_MODEL_FALLBACK,
            default=defaults.get(CONF_OPENCLAW_MODEL_FALLBACK, DEFAULT_OPENCLAW_MODEL_FALLBACK),
        )] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=OPENCLAW_MODEL_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
    return vol.Schema(schema)


def _room_schema(
    defaults: dict[str, Any] | None = None, *, include_add_another: bool = True
) -> vol.Schema:
    defaults = defaults or {}
    schema: dict[Any, Any] = {
            vol.Required(CONF_ROOM_NAME, default=defaults.get(CONF_ROOM_NAME, "")): str,
            vol.Required(
                CONF_ROOM_SENSOR_BIAS_C,
                default=defaults.get(CONF_ROOM_SENSOR_BIAS_C, DEFAULT_ROOM_SENSOR_BIAS_C),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-3, max=3, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_ROOM_ENABLE_PRESENCE_ECO,
                default=defaults.get(CONF_ROOM_ENABLE_PRESENCE_ECO, DEFAULT_ROOM_ENABLE_PRESENCE_ECO),
            ): bool,
            vol.Required(
                CONF_ROOM_ENABLE_LEARNING,
                default=defaults.get(CONF_ROOM_ENABLE_LEARNING, DEFAULT_ROOM_ENABLE_LEARNING),
            ): bool,
            vol.Required(
                CONF_ROOM_ENABLE_OPENING_PAUSE,
                default=defaults.get(CONF_ROOM_ENABLE_OPENING_PAUSE, DEFAULT_ROOM_ENABLE_OPENING_PAUSE),
            ): bool,
            vol.Optional(
                CONF_ROOM_LINK_GROUP,
                default=defaults.get(CONF_ROOM_LINK_GROUP, DEFAULT_ROOM_LINK_GROUP),
            ): str,
            vol.Required(
                CONF_ROOM_ANTI_SHORT_CYCLE_MIN,
                default=defaults.get(
                    CONF_ROOM_ANTI_SHORT_CYCLE_MIN, DEFAULT_ROOM_ANTI_SHORT_CYCLE_MIN
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=30, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_ROOM_QUICK_START_DEFICIT_C,
                default=defaults.get(
                    CONF_ROOM_QUICK_START_DEFICIT_C, DEFAULT_ROOM_QUICK_START_DEFICIT_C
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=3, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_ROOM_START_DEFICIT_C,
                default=defaults.get(
                    CONF_ROOM_START_DEFICIT_C, DEFAULT_ROOM_START_DEFICIT_C
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=3, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_ROOM_STOP_SURPLUS_C,
                default=defaults.get(
                    CONF_ROOM_STOP_SURPLUS_C, DEFAULT_ROOM_STOP_SURPLUS_C
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=3, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_ROOM_PAUSE_AFTER_OPEN_MIN,
                default=defaults.get(
                    CONF_ROOM_PAUSE_AFTER_OPEN_MIN, DEFAULT_ROOM_PAUSE_AFTER_OPEN_MIN
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=60, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_ROOM_RESUME_AFTER_CLOSED_MIN,
                default=defaults.get(
                    CONF_ROOM_RESUME_AFTER_CLOSED_MIN, DEFAULT_ROOM_RESUME_AFTER_CLOSED_MIN
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=60, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_ROOM_MASSIVE_OVERHEAT_C,
                default=defaults.get(
                    CONF_ROOM_MASSIVE_OVERHEAT_C, DEFAULT_ROOM_MASSIVE_OVERHEAT_C
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0.5, max=5, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_ROOM_MASSIVE_OVERHEAT_MIN,
                default=defaults.get(
                    CONF_ROOM_MASSIVE_OVERHEAT_MIN, DEFAULT_ROOM_MASSIVE_OVERHEAT_MIN
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=120, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
        }
    area_default = defaults.get(CONF_ROOM_AREA_ID)
    if area_default not in (None, "", []):
        schema[vol.Optional(CONF_ROOM_AREA_ID, default=area_default)] = selector.AreaSelector(
            selector.AreaSelectorConfig()
        )
    else:
        schema[vol.Optional(CONF_ROOM_AREA_ID)] = selector.AreaSelector(
            selector.AreaSelectorConfig()
        )
    temp_default = defaults.get(CONF_ROOM_TEMP_SENSOR)
    if temp_default not in (None, "", []):
        schema[vol.Required(CONF_ROOM_TEMP_SENSOR, default=temp_default)] = _entity_selector("sensor")
    else:
        schema[vol.Required(CONF_ROOM_TEMP_SENSOR)] = _entity_selector("sensor")
    _add_optional_entity_field(schema, defaults, CONF_ROOM_HUMIDITY_SENSOR, "sensor")
    _add_optional_entity_field(schema, defaults, CONF_ROOM_TARGET_NUMBER, "input_number")
    _add_optional_entity_field(schema, defaults, CONF_ROOM_HEAT_PUMP, "climate")
    _add_optional_entity_field(schema, defaults, CONF_ROOM_HEAT_PUMP_POWER_SENSOR, "sensor")
    _add_optional_entity_field(schema, defaults, CONF_ROOM_RADIATORS, "climate", multiple=True)
    _add_optional_entity_field(schema, defaults, CONF_ROOM_OPENING_SENSORS, "binary_sensor", multiple=True)
    _add_optional_entity_field(schema, defaults, CONF_ROOM_OCCUPANCY_SENSORS, "binary_sensor", multiple=True)
    if include_add_another:
        schema[vol.Required("add_another", default=True)] = bool
    return vol.Schema(schema)


def _validate_provider_input(user_input: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    has_gas = bool(user_input.get(CONF_GAS_PRICE_SENSOR))
    has_fjern = bool(user_input.get(CONF_DISTRICT_HEAT_PRICE_SENSOR))

    if has_gas and has_fjern:
        errors["base"] = "choose_one_alt_heat_source"
        return errors
    if not has_gas and not has_fjern:
        errors["base"] = "alt_heat_source_required"
        return errors

    if bool(user_input.get(CONF_OPENCLAW_ENABLED, DEFAULT_OPENCLAW_ENABLED)):
        if not str(user_input.get(CONF_OPENCLAW_URL, "")).strip():
            errors["base"] = "openclaw_url_required"
            return errors
    primary_engine = user_input.get(CONF_AI_PRIMARY_ENGINE, DEFAULT_AI_PRIMARY_ENGINE)
    fallback_engine = user_input.get(CONF_AI_FALLBACK_ENGINE, DEFAULT_AI_FALLBACK_ENGINE)
    report_engine = user_input.get(CONF_AI_REPORT_ENGINE, DEFAULT_AI_REPORT_ENGINE)

    if primary_engine == AI_PRIMARY_ENGINE_OPENCLAW:
        bridge = str(user_input.get(CONF_OPENCLAW_BRIDGE_URL, "")).strip()
        hook_url = str(user_input.get(CONF_OPENCLAW_URL, "")).strip()
        if not bridge and not hook_url:
            errors["base"] = "openclaw_bridge_or_hook_required"
            return errors
    if primary_engine not in AI_DECISION_ENGINE_OPTIONS and primary_engine not in AI_PRIMARY_ENGINE_OPTIONS:
        errors["base"] = "primary_engine_invalid"
        return errors
    if fallback_engine not in AI_FALLBACK_ENGINE_OPTIONS:
        errors["base"] = "fallback_engine_invalid"
        return errors
    if report_engine not in AI_DECISION_ENGINE_OPTIONS:
        errors["base"] = "report_engine_invalid"
        return errors
    if str(user_input.get(CONF_OPENCLAW_PAYLOAD_PROFILE, DEFAULT_OPENCLAW_PAYLOAD_PROFILE)) not in PAYLOAD_PROFILE_OPTIONS:
        errors["base"] = "openclaw_payload_profile_invalid"
        return errors
    if str(user_input.get(CONF_PROVIDER_PAYLOAD_PROFILE, DEFAULT_PROVIDER_PAYLOAD_PROFILE)) not in PAYLOAD_PROFILE_OPTIONS:
        errors["base"] = "provider_payload_profile_invalid"
        return errors

    engines_in_use = {
        str(user_input.get(CONF_AI_PRIMARY_ENGINE, DEFAULT_AI_PRIMARY_ENGINE)).strip().lower(),
        str(user_input.get(CONF_AI_FALLBACK_ENGINE, DEFAULT_AI_FALLBACK_ENGINE)).strip().lower(),
        str(user_input.get(CONF_AI_REPORT_ENGINE, DEFAULT_AI_REPORT_ENGINE)).strip().lower(),
    }
    provider = str(user_input.get(CONF_AI_PROVIDER, DEFAULT_AI_PROVIDER)).strip().lower()
    uses_ollama = AI_PROVIDER_OLLAMA in engines_in_use or provider == AI_PROVIDER_OLLAMA
    uses_gemini = AI_PROVIDER_GEMINI in engines_in_use or provider == AI_PROVIDER_GEMINI

    if uses_ollama:
        if not str(user_input.get(CONF_OLLAMA_HOST, "")).strip():
            errors["base"] = "ollama_host_required"
        if not str(user_input.get(CONF_AI_MODEL_FAST, "")).strip():
            errors["base"] = "ollama_model_fast_required"
        if not str(user_input.get(CONF_AI_MODEL_REPORT, "")).strip():
            errors["base"] = "ollama_model_report_required"
    elif uses_gemini:
        if not str(user_input.get(CONF_GEMINI_API_KEY, "")).strip():
            errors["base"] = "gemini_api_key_required"
        if not str(user_input.get(CONF_GEMINI_MODEL_FAST, "")).strip():
            errors["base"] = "gemini_model_fast_required"
        if not str(user_input.get(CONF_GEMINI_MODEL_REPORT, "")).strip():
            errors["base"] = "gemini_model_report_required"
    elif provider not in AI_PROVIDER_OPTIONS:
        errors["base"] = "provider_invalid"
    return errors


class AiVarmeStyringConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AI Varme Styring."""

    VERSION = 3

    def __init__(self) -> None:
        self._base_input: dict[str, Any] = {}
        self._rooms: list[dict[str, Any]] = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            merged_input = _merge_visible_input(self._base_input, user_input)
            errors = _validate_provider_input(merged_input)
            if not errors:
                self._base_input = dict(merged_input)
                await self.async_set_unique_id(merged_input[CONF_NAME].strip().lower())
                self._abort_if_unique_id_configured()
                return await self.async_step_room()

        return self.async_show_form(
            step_id="user",
            data_schema=_base_schema(_merge_visible_input({CONF_NAME: DEFAULT_NAME}, user_input or {})),
            errors=errors,
        )

    async def async_step_room(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = await self._auto_fill_room_from_area(user_input)
            room_name = user_input[CONF_ROOM_NAME].strip()
            if not room_name:
                errors["base"] = "room_name_required"
            else:
                room = dict(user_input)
                room[CONF_ROOM_NAME] = room_name
                add_another = bool(room.pop("add_another", False))
                self._rooms.append(room)
                if add_another:
                    return self.async_show_form(
                        step_id="room",
                        data_schema=_room_schema(),
                        description_placeholders={"room_count": str(len(self._rooms))},
                    )
                data = dict(self._base_input)
                data[CONF_ROOMS] = self._rooms
                return self.async_create_entry(title=data[CONF_NAME], data=data)

        return self.async_show_form(
            step_id="room",
            data_schema=_room_schema(),
            errors=errors,
            description_placeholders={"room_count": str(len(self._rooms))},
        )

    async def _auto_fill_room_from_area(self, room_input: dict[str, Any]) -> dict[str, Any]:
        """Auto-fill room fields from selected HA area when possible."""
        area_id = room_input.get(CONF_ROOM_AREA_ID)
        if not area_id:
            return room_input

        entity_reg = er.async_get(self.hass)
        area_reg = ar.async_get(self.hass)
        area = area_reg.async_get_area(area_id)

        if area and not str(room_input.get(CONF_ROOM_NAME, "")).strip():
            room_input[CONF_ROOM_NAME] = area.name

        entities = [e.entity_id for e in entity_reg.entities.values() if e.area_id == area_id and e.entity_id]

        def first(domain: str, keywords: tuple[str, ...] = ()) -> str | None:
            candidates = [eid for eid in entities if eid.startswith(f"{domain}.")]
            if not candidates:
                return None
            if keywords:
                for eid in candidates:
                    low = eid.lower()
                    if any(k in low for k in keywords):
                        return eid
            return candidates[0]

        def many(domain: str, keywords: tuple[str, ...] = ()) -> list[str]:
            candidates = [eid for eid in entities if eid.startswith(f"{domain}.")]
            if not keywords:
                return candidates
            return [eid for eid in candidates if any(k in eid.lower() for k in keywords)]

        if not room_input.get(CONF_ROOM_TEMP_SENSOR):
            suggestion = first("sensor", ("temp", "temperature"))
            if suggestion:
                room_input[CONF_ROOM_TEMP_SENSOR] = suggestion

        if not room_input.get(CONF_ROOM_TARGET_NUMBER):
            suggestion = first("input_number", ("target", "temperature", "temp", "maal", "mål"))
            if suggestion:
                room_input[CONF_ROOM_TARGET_NUMBER] = suggestion

        if not room_input.get(CONF_ROOM_HUMIDITY_SENSOR):
            suggestion = first("sensor", ("humidity", "fugt"))
            if suggestion:
                room_input[CONF_ROOM_HUMIDITY_SENSOR] = suggestion

        if not room_input.get(CONF_ROOM_HEAT_PUMP):
            suggestion = first("climate", ("qlima", "ac", "varmepumpe", "heat_pump", "pump"))
            if suggestion:
                room_input[CONF_ROOM_HEAT_PUMP] = suggestion
        if not room_input.get(CONF_ROOM_HEAT_PUMP_POWER_SENSOR):
            suggestion = first("sensor", ("power", "watt", "forbrug", "consumption", "effekt"))
            if suggestion:
                room_input[CONF_ROOM_HEAT_PUMP_POWER_SENSOR] = suggestion

        if not room_input.get(CONF_ROOM_RADIATORS):
            climates = many("climate")
            hp = room_input.get(CONF_ROOM_HEAT_PUMP)
            room_input[CONF_ROOM_RADIATORS] = [eid for eid in climates if eid != hp]

        if not room_input.get(CONF_ROOM_OPENING_SENSORS):
            room_input[CONF_ROOM_OPENING_SENSORS] = many(
                "binary_sensor",
                ("window", "door", "vindue", "dor", "dør", "open", "abning", "åbning", "kontakt"),
            )

        if not room_input.get(CONF_ROOM_OCCUPANCY_SENSORS):
            room_input[CONF_ROOM_OCCUPANCY_SENSORS] = many(
                "binary_sensor", ("motion", "presence", "occupancy", "bevag", "bevæg", "tilstede")
            )

        return room_input

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return AiVarmeStyringOptionsFlow(config_entry)


class AiVarmeStyringOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry
        self._working_base: dict[str, Any] | None = None
        self._rooms: list[dict[str, Any]] = []
        self._selected_room_index: int | None = None

    def _ensure_state(self) -> None:
        if self._working_base is not None:
            return
        defaults = {**self._config_entry.data, **self._config_entry.options}
        self._working_base = {
            k: v for k, v in defaults.items() if k != CONF_ROOMS
        }
        self._rooms = list(defaults.get(CONF_ROOMS, []))

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        self._ensure_state()
        errors: dict[str, str] = {}
        assert self._working_base is not None
        actions = [
            {"value": "providers", "label": "AI providers"},
            {"value": "advanced", "label": "Avanceret styring"},
            {"value": "add_room", "label": "Tilføj rum"},
            {"value": "edit_room", "label": "Rediger rum"},
            {"value": "remove_room", "label": "Fjern rum"},
            {"value": "save", "label": "Gem"},
        ]

        if user_input is not None:
            action = user_input.get("room_action")
            base_input = _merge_visible_input(self._working_base, user_input)
            base_input.pop("room_action", None)
            errors = _validate_provider_input(base_input)
            if not errors:
                self._working_base = base_input
                if action == "providers":
                    return await self.async_step_providers()
                if action == "advanced":
                    return await self.async_step_advanced()
                if action == "add_room":
                    return await self.async_step_room_add()
                if action == "edit_room":
                    if not self._rooms:
                        errors["base"] = "no_rooms"
                    else:
                        return await self.async_step_room_edit_select()
                if action == "remove_room":
                    if not self._rooms:
                        errors["base"] = "no_rooms"
                    else:
                        return await self.async_step_room_remove_select()
                if not self._rooms:
                    errors["base"] = "at_least_one_room"
                else:
                    payload = dict(self._working_base)
                    payload[CONF_ROOMS] = self._rooms
                    return self.async_create_entry(title="", data=payload)

        schema = _general_options_schema(_merge_visible_input(self._working_base, user_input or {})).extend(
            {
                vol.Required("room_action", default="save"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=actions,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
            description_placeholders={"room_count": str(len(self._rooms))},
        )

    async def async_step_providers(self, user_input: dict[str, Any] | None = None):
        self._ensure_state()
        assert self._working_base is not None
        errors: dict[str, str] = {}
        if user_input is not None:
            merged = _merge_visible_input(self._working_base, user_input)
            errors = _validate_provider_input(merged)
            if not errors:
                self._working_base = merged
                return await self.async_step_init()

        return self.async_show_form(
            step_id="providers",
            data_schema=_providers_schema(_merge_visible_input(self._working_base, user_input or {})),
            errors=errors,
        )

    async def async_step_advanced(self, user_input: dict[str, Any] | None = None):
        self._ensure_state()
        assert self._working_base is not None
        if user_input is not None:
            self._working_base = _merge_visible_input(self._working_base, user_input)
            return await self.async_step_init()

        return self.async_show_form(
            step_id="advanced",
            data_schema=_advanced_options_schema(_merge_visible_input(self._working_base, user_input or {})),
            errors={},
        )

    async def async_step_room_add(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = await self._auto_fill_room_from_area(user_input)
            room_name = str(user_input.get(CONF_ROOM_NAME, "")).strip()
            if not room_name:
                errors["base"] = "room_name_required"
            else:
                room = dict(user_input)
                room[CONF_ROOM_NAME] = room_name
                self._rooms.append(room)
                return await self.async_step_init()
        return self.async_show_form(
            step_id="room_add",
            data_schema=_room_schema(include_add_another=False),
            errors=errors,
        )

    async def async_step_room_edit_select(
        self, user_input: dict[str, Any] | None = None
    ):
        room_options = [f"{idx}: {room.get(CONF_ROOM_NAME, f'Rum {idx+1}')}" for idx, room in enumerate(self._rooms)]
        if user_input is not None:
            self._selected_room_index = int(user_input["room_index"])
            return await self.async_step_room_edit()
        return self.async_show_form(
            step_id="room_edit_select",
            data_schema=vol.Schema(
                {
                    vol.Required("room_index"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": str(i), "label": label}
                                for i, label in enumerate(room_options)
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def async_step_room_edit(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        idx = self._selected_room_index
        if idx is None or idx < 0 or idx >= len(self._rooms):
            return await self.async_step_init()
        if user_input is not None:
            user_input = await self._auto_fill_room_from_area(user_input)
            room_name = str(user_input.get(CONF_ROOM_NAME, "")).strip()
            if not room_name:
                errors["base"] = "room_name_required"
            else:
                room = dict(user_input)
                room[CONF_ROOM_NAME] = room_name
                self._rooms[idx] = room
                self._selected_room_index = None
                return await self.async_step_init()
        return self.async_show_form(
            step_id="room_edit",
            data_schema=_room_schema(self._rooms[idx], include_add_another=False),
            errors=errors,
        )

    async def async_step_room_remove_select(
        self, user_input: dict[str, Any] | None = None
    ):
        room_options = [f"{idx}: {room.get(CONF_ROOM_NAME, f'Rum {idx+1}')}" for idx, room in enumerate(self._rooms)]
        if user_input is not None:
            idx = int(user_input["room_index"])
            if 0 <= idx < len(self._rooms):
                self._rooms.pop(idx)
            return await self.async_step_init()
        return self.async_show_form(
            step_id="room_remove_select",
            data_schema=vol.Schema(
                {
                    vol.Required("room_index"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": str(i), "label": label}
                                for i, label in enumerate(room_options)
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def _auto_fill_room_from_area(self, room_input: dict[str, Any]) -> dict[str, Any]:
        """Auto-fill room fields from selected HA area when possible."""
        area_id = room_input.get(CONF_ROOM_AREA_ID)
        if not area_id:
            return room_input

        entity_reg = er.async_get(self.hass)
        area_reg = ar.async_get(self.hass)
        area = area_reg.async_get_area(area_id)
        if area and not str(room_input.get(CONF_ROOM_NAME, "")).strip():
            room_input[CONF_ROOM_NAME] = area.name

        entities = [e.entity_id for e in entity_reg.entities.values() if e.area_id == area_id and e.entity_id]

        def first(domain: str, keywords: tuple[str, ...] = ()) -> str | None:
            candidates = [eid for eid in entities if eid.startswith(f"{domain}.")]
            if not candidates:
                return None
            if keywords:
                for eid in candidates:
                    low = eid.lower()
                    if any(k in low for k in keywords):
                        return eid
            return candidates[0]

        def many(domain: str, keywords: tuple[str, ...] = ()) -> list[str]:
            candidates = [eid for eid in entities if eid.startswith(f"{domain}.")]
            if not keywords:
                return candidates
            return [eid for eid in candidates if any(k in eid.lower() for k in keywords)]

        if not room_input.get(CONF_ROOM_TEMP_SENSOR):
            suggestion = first("sensor", ("temp", "temperature"))
            if suggestion:
                room_input[CONF_ROOM_TEMP_SENSOR] = suggestion
        if not room_input.get(CONF_ROOM_TARGET_NUMBER):
            suggestion = first("input_number", ("target", "temperature", "temp", "maal", "mål"))
            if suggestion:
                room_input[CONF_ROOM_TARGET_NUMBER] = suggestion
        if not room_input.get(CONF_ROOM_HEAT_PUMP):
            suggestion = first("climate", ("qlima", "ac", "varmepumpe", "heat_pump", "pump"))
            if suggestion:
                room_input[CONF_ROOM_HEAT_PUMP] = suggestion
        if not room_input.get(CONF_ROOM_HEAT_PUMP_POWER_SENSOR):
            suggestion = first("sensor", ("power", "watt", "forbrug", "consumption", "effekt"))
            if suggestion:
                room_input[CONF_ROOM_HEAT_PUMP_POWER_SENSOR] = suggestion
        if not room_input.get(CONF_ROOM_RADIATORS):
            climates = many("climate")
            hp = room_input.get(CONF_ROOM_HEAT_PUMP)
            room_input[CONF_ROOM_RADIATORS] = [eid for eid in climates if eid != hp]
        if not room_input.get(CONF_ROOM_OPENING_SENSORS):
            room_input[CONF_ROOM_OPENING_SENSORS] = many(
                "binary_sensor",
                ("window", "door", "vindue", "dor", "dør", "open", "abning", "åbning", "kontakt"),
            )
        if not room_input.get(CONF_ROOM_OCCUPANCY_SENSORS):
            room_input[CONF_ROOM_OCCUPANCY_SENSORS] = many(
                "binary_sensor", ("motion", "presence", "occupancy", "bevag", "bevæg", "tilstede")
            )
        return room_input
