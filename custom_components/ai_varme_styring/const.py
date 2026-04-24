"""Constants for AI Varme Styring."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "ai_varme_styring"

PLATFORMS: Final[list[str]] = ["sensor", "switch", "number", "button"]

CONF_NAME: Final = "name"
CONF_ROOMS: Final = "rooms"
CONF_ROOM_NAME: Final = "room_name"
CONF_ROOM_AREA_ID: Final = "room_area_id"
CONF_ROOM_TEMP_SENSOR: Final = "room_temp_sensor"
CONF_ROOM_HUMIDITY_SENSOR: Final = "room_humidity_sensor"
CONF_ROOM_TARGET_NUMBER: Final = "room_target_number"
CONF_ROOM_HEAT_PUMP: Final = "room_heat_pump"
CONF_ROOM_HEAT_PUMP_POWER_SENSOR: Final = "room_heat_pump_power_sensor"
CONF_ROOM_RADIATORS: Final = "room_radiators"
CONF_ROOM_OPENING_SENSORS: Final = "room_opening_sensors"
CONF_ROOM_OCCUPANCY_SENSORS: Final = "room_occupancy_sensors"
CONF_ROOM_ENABLE_PRESENCE_ECO: Final = "room_enable_presence_eco"
CONF_ROOM_ENABLE_LEARNING: Final = "room_enable_learning"
CONF_ROOM_ENABLE_OPENING_PAUSE: Final = "room_enable_opening_pause"
CONF_ROOM_SENSOR_BIAS_C: Final = "room_sensor_bias_c"
CONF_ROOM_TARGET_STEP_C: Final = "room_target_step_c"
CONF_ROOM_LINK_GROUP: Final = "room_link_group"
CONF_ROOM_ADJACENT_ROOMS: Final = "room_adjacent_rooms"
CONF_ROOM_HEAT_SOURCE_DIRECTION_BIAS: Final = "room_heat_source_direction_bias"
CONF_ROOM_CHEAP_POWER_RADIATOR_SETBACK_EXTRA_C: Final = "room_cheap_power_radiator_setback_extra_c"
CONF_ROOM_ANTI_SHORT_CYCLE_MIN: Final = "room_anti_short_cycle_min"
CONF_ROOM_QUICK_START_DEFICIT_C: Final = "room_quick_start_deficit_c"
CONF_ROOM_START_DEFICIT_C: Final = "room_start_deficit_c"
CONF_ROOM_STOP_SURPLUS_C: Final = "room_stop_surplus_c"
CONF_ROOM_PAUSE_AFTER_OPEN_MIN: Final = "room_pause_after_open_min"
CONF_ROOM_RESUME_AFTER_CLOSED_MIN: Final = "room_resume_after_closed_min"
CONF_ROOM_MASSIVE_OVERHEAT_C: Final = "room_massive_overheat_c"
CONF_ROOM_MASSIVE_OVERHEAT_MIN: Final = "room_massive_overheat_min"
CONF_OUTDOOR_TEMP_SENSOR: Final = "outdoor_temp_sensor"
CONF_WEATHER_ENTITY: Final = "weather_entity"
CONF_ELECTRICITY_PRICE_SENSOR: Final = "electricity_price_sensor"
CONF_GAS_PRICE_SENSOR: Final = "gas_price_sensor"
CONF_DISTRICT_HEAT_PRICE_SENSOR: Final = "district_heat_price_sensor"
CONF_DISTRICT_HEAT_CONSUMPTION_SENSOR: Final = "district_heat_consumption_sensor"
CONF_GAS_CONSUMPTION_SENSOR: Final = "gas_consumption_sensor"
CONF_HEAT_PUMP_CLIMATES: Final = "heat_pump_climates"
CONF_RADIATOR_CLIMATES: Final = "radiator_climates"
CONF_ROOM_TEMPERATURE_SENSORS: Final = "room_temperature_sensors"
CONF_ROOM_TARGET_NUMBERS: Final = "room_target_numbers"
CONF_OPENING_SENSORS: Final = "opening_sensors"
CONF_OCCUPANCY_SENSORS: Final = "occupancy_sensors"
CONF_VACUUM_ENTITY: Final = "vacuum_entity"

CONF_ENABLE_PRICE_AWARENESS: Final = "enable_price_awareness"
CONF_ENABLE_PRESENCE_ECO: Final = "enable_presence_eco"
CONF_ENABLE_PID_LAYER: Final = "enable_pid_layer"
CONF_ENABLE_LEARNING: Final = "enable_learning"
CONF_PRESENCE_AWAY_MIN: Final = "presence_away_min"
CONF_PRESENCE_RETURN_MIN: Final = "presence_return_min"
CONF_PID_KP: Final = "pid_kp"
CONF_PID_KI: Final = "pid_ki"
CONF_PID_KD: Final = "pid_kd"
CONF_PID_DEADBAND_C: Final = "pid_deadband_c"
CONF_PID_INTEGRAL_LIMIT: Final = "pid_integral_limit"
CONF_PID_OFFSET_MAX_C: Final = "pid_offset_max_c"
CONF_CONFIDENCE_THRESHOLD: Final = "confidence_threshold"
CONF_REVERT_TIMEOUT_MIN: Final = "revert_timeout_min"

CONF_PRICE_MARGIN: Final = "price_margin"
CONF_START_DEFICIT_C: Final = "start_deficit_c"
CONF_STOP_SURPLUS_C: Final = "stop_surplus_c"
CONF_FLOW_LIMIT_MARGIN_C: Final = "flow_limit_margin_c"
CONF_RADIATOR_BOOST_C: Final = "radiator_boost_c"
CONF_RADIATOR_SETBACK_C: Final = "radiator_setback_c"
CONF_HEAT_PUMP_CHEAP_PRIORITY_FACTOR: Final = "heat_pump_cheap_priority_factor"
CONF_HEAT_PUMP_CHEAP_FAN_MODE: Final = "heat_pump_cheap_fan_mode"
CONF_HEAT_SOURCE_DIRECTION_BIAS: Final = "heat_source_direction_bias"
CONF_CHEAP_POWER_RADIATOR_SETBACK_EXTRA_C: Final = "cheap_power_radiator_setback_extra_c"
CONF_UPDATE_SECONDS: Final = "update_seconds"
CONF_DECIMALS: Final = "decimals"
CONF_AI_PROVIDER: Final = "ai_provider"
CONF_AI_PRIMARY_ENGINE: Final = "ai_primary_engine"
CONF_AI_FALLBACK_ENGINE: Final = "ai_fallback_engine"
CONF_AI_REPORT_ENGINE: Final = "ai_report_engine"
CONF_AI_MODEL_FAST: Final = "ai_model_fast"
CONF_AI_MODEL_REPORT: Final = "ai_model_report"
CONF_OLLAMA_HOST: Final = "ollama_host"
CONF_GEMINI_API_KEY: Final = "gemini_api_key"
CONF_GEMINI_MODEL_FAST: Final = "gemini_model_fast"
CONF_GEMINI_MODEL_REPORT: Final = "gemini_model_report"
CONF_OPENCLAW_ENABLED: Final = "openclaw_enabled"
CONF_OPENCLAW_URL: Final = "openclaw_url"
CONF_OPENCLAW_TOKEN: Final = "openclaw_token"
CONF_OPENCLAW_PASSWORD: Final = "openclaw_password"
CONF_OPENCLAW_TIMEOUT_SEC: Final = "openclaw_timeout_sec"
CONF_OPENCLAW_BRIDGE_URL: Final = "openclaw_bridge_url"
CONF_OPENCLAW_ONLY_MODE: Final = "openclaw_only_mode"
CONF_OPENCLAW_PAYLOAD_PROFILE: Final = "openclaw_payload_profile"
CONF_OPENCLAW_MODEL_PREFERRED: Final = "openclaw_model_preferred"
CONF_OPENCLAW_MODEL_FALLBACK: Final = "openclaw_model_fallback"
CONF_PROVIDER_PAYLOAD_PROFILE: Final = "provider_payload_profile"
CONF_HUMIDITY_COMFORT_ENABLED: Final = "humidity_comfort_enabled"
CONF_HUMIDITY_DRY_THRESHOLD: Final = "humidity_dry_threshold"
CONF_HUMIDITY_HUMID_THRESHOLD: Final = "humidity_humid_threshold"
CONF_HUMIDITY_MAX_OFFSET_C: Final = "humidity_max_offset_c"
CONF_REPORT_INTERVAL_MIN: Final = "report_interval_min"
CONF_AI_DECISION_INTERVAL_MIN: Final = "ai_decision_interval_min"

DEFAULT_NAME: Final = "AI Varme Styring"
DEFAULT_ENABLE_PRICE_AWARENESS: Final = True
DEFAULT_ENABLE_PRESENCE_ECO: Final = False
DEFAULT_ENABLE_PID_LAYER: Final = False
DEFAULT_ENABLE_LEARNING: Final = True
DEFAULT_PRESENCE_AWAY_MIN: Final = 20
DEFAULT_PRESENCE_RETURN_MIN: Final = 5
DEFAULT_PID_KP: Final = 1.2
DEFAULT_PID_KI: Final = 0.08
DEFAULT_PID_KD: Final = 0.20
DEFAULT_PID_DEADBAND_C: Final = 0.15
DEFAULT_PID_INTEGRAL_LIMIT: Final = 4.0
DEFAULT_PID_OFFSET_MAX_C: Final = 1.5
DEFAULT_CONFIDENCE_THRESHOLD: Final = 75.0
DEFAULT_REVERT_TIMEOUT_MIN: Final = 30
DEFAULT_PRICE_MARGIN: Final = 0.15
DEFAULT_START_DEFICIT_C: Final = 0.4
DEFAULT_STOP_SURPLUS_C: Final = 0.7
DEFAULT_FLOW_LIMIT_MARGIN_C: Final = 0.2
DEFAULT_RADIATOR_BOOST_C: Final = 0.8
DEFAULT_RADIATOR_SETBACK_C: Final = 2.0
DEFAULT_HEAT_PUMP_CHEAP_PRIORITY_FACTOR: Final = 1.0
DEFAULT_HEAT_PUMP_CHEAP_FAN_MODE: Final = "off"
DEFAULT_HEAT_SOURCE_DIRECTION_BIAS: Final = 0.0
DEFAULT_CHEAP_POWER_RADIATOR_SETBACK_EXTRA_C: Final = 0.0
DEFAULT_UPDATE_SECONDS: Final = 60
DEFAULT_DECIMALS: Final = 1
DEFAULT_GLOBAL_TARGET_C: Final = 22.0
DEFAULT_ECO_TARGET_C: Final = 20.0
DEFAULT_AI_PROVIDER: Final = "ollama"
DEFAULT_AI_PRIMARY_ENGINE: Final = "openclaw"
DEFAULT_AI_FALLBACK_ENGINE: Final = "none"
DEFAULT_AI_REPORT_ENGINE: Final = "ollama"
DEFAULT_AI_MODEL_FAST: Final = "qwen2.5:3b"
DEFAULT_AI_MODEL_REPORT: Final = "qwen2.5:14b"
DEFAULT_OLLAMA_HOST: Final = "http://homeassistant.local:11434"
DEFAULT_GEMINI_MODEL_FAST: Final = "gemini-2.5-flash"
DEFAULT_GEMINI_MODEL_REPORT: Final = "gemini-2.5-pro"
DEFAULT_OPENCLAW_ENABLED: Final = False
DEFAULT_OPENCLAW_URL: Final = "http://127.0.0.1:18789/hooks/agent"
DEFAULT_OPENCLAW_TOKEN: Final = ""
DEFAULT_OPENCLAW_PASSWORD: Final = ""
DEFAULT_OPENCLAW_TIMEOUT_SEC: Final = 12
DEFAULT_OPENCLAW_BRIDGE_URL: Final = "http://127.0.0.1:18890/heating/decision"
DEFAULT_OPENCLAW_ONLY_MODE: Final = False
DEFAULT_OPENCLAW_PAYLOAD_PROFILE: Final = "heavy"
DEFAULT_OPENCLAW_MODEL_PREFERRED: Final = "gpt-5-mini"
DEFAULT_OPENCLAW_MODEL_FALLBACK: Final = "gpt-4.1"
DEFAULT_PROVIDER_PAYLOAD_PROFILE: Final = "light"
DEFAULT_HUMIDITY_COMFORT_ENABLED: Final = True
DEFAULT_HUMIDITY_DRY_THRESHOLD: Final = 35.0
DEFAULT_HUMIDITY_HUMID_THRESHOLD: Final = 60.0
DEFAULT_HUMIDITY_MAX_OFFSET_C: Final = 0.3
DEFAULT_REPORT_INTERVAL_MIN: Final = 15
DEFAULT_AI_DECISION_INTERVAL_MIN: Final = 2
DEFAULT_ROOM_SENSOR_BIAS_C: Final = 0.0
DEFAULT_ROOM_TARGET_STEP_C: Final = 0.5
DEFAULT_ROOM_ENABLE_PRESENCE_ECO: Final = False
DEFAULT_ROOM_ENABLE_LEARNING: Final = True
DEFAULT_ROOM_ENABLE_OPENING_PAUSE: Final = True
DEFAULT_ROOM_LINK_GROUP: Final = ""
DEFAULT_ROOM_HEAT_SOURCE_DIRECTION_BIAS: Final = 0.0
DEFAULT_ROOM_CHEAP_POWER_RADIATOR_SETBACK_EXTRA_C: Final = 0.0
DEFAULT_ROOM_ANTI_SHORT_CYCLE_MIN: Final = 3
DEFAULT_ROOM_QUICK_START_DEFICIT_C: Final = 0.4
DEFAULT_ROOM_START_DEFICIT_C: Final = 0.4
DEFAULT_GARAGE_ROOM_QUICK_START_DEFICIT_C: Final = 0.15
DEFAULT_GARAGE_ROOM_START_DEFICIT_C: Final = 0.1
DEFAULT_ROOM_STOP_SURPLUS_C: Final = 0.7
DEFAULT_ROOM_PAUSE_AFTER_OPEN_MIN: Final = 10
DEFAULT_ROOM_RESUME_AFTER_CLOSED_MIN: Final = 10
DEFAULT_ROOM_MASSIVE_OVERHEAT_C: Final = 2.0
DEFAULT_ROOM_MASSIVE_OVERHEAT_MIN: Final = 15

AI_PROVIDER_OLLAMA: Final = "ollama"
AI_PROVIDER_GEMINI: Final = "gemini"
AI_PROVIDER_OPTIONS: Final[list[str]] = [AI_PROVIDER_OLLAMA, AI_PROVIDER_GEMINI]
AI_ENGINE_NONE: Final = "none"
AI_PRIMARY_ENGINE_PROVIDER: Final = "provider"
AI_PRIMARY_ENGINE_OPENCLAW: Final = "openclaw"
AI_DECISION_ENGINE_OPTIONS: Final[list[str]] = [
    AI_PRIMARY_ENGINE_OPENCLAW,
    AI_PROVIDER_OLLAMA,
    AI_PROVIDER_GEMINI,
]
AI_FALLBACK_ENGINE_OPTIONS: Final[list[str]] = [
    AI_ENGINE_NONE,
    AI_PRIMARY_ENGINE_OPENCLAW,
    AI_PROVIDER_OLLAMA,
    AI_PROVIDER_GEMINI,
]
AI_PRIMARY_ENGINE_OPTIONS: Final[list[str]] = [
    AI_PRIMARY_ENGINE_PROVIDER,
    AI_PRIMARY_ENGINE_OPENCLAW,
]

# Accept both legacy provider-specific values and current canonical values
# when reading stored config. UI should still prefer canonical options.
AI_PRIMARY_ENGINE_ACCEPTED_OPTIONS: Final[list[str]] = [
    AI_PRIMARY_ENGINE_PROVIDER,
    AI_PRIMARY_ENGINE_OPENCLAW,
    AI_PROVIDER_OLLAMA,
    AI_PROVIDER_GEMINI,
]
PAYLOAD_PROFILE_LIGHT: Final = "light"
PAYLOAD_PROFILE_HEAVY: Final = "heavy"
PAYLOAD_PROFILE_OPTIONS: Final[list[str]] = [
    PAYLOAD_PROFILE_LIGHT,
    PAYLOAD_PROFILE_HEAVY,
]

CHEAP_FAN_MODE_OPTIONS: Final[list[str]] = [
    "off",
    "auto",
    "medium",
    "high",
    "max",
]

RUNTIME_ENABLED: Final = "runtime_enabled"
RUNTIME_GLOBAL_TARGET: Final = "runtime_global_target"
RUNTIME_ECO_TARGET: Final = "runtime_eco_target"
RUNTIME_PRESENCE_ECO_ENABLED: Final = "runtime_presence_eco_enabled"
RUNTIME_PID_LAYER_ENABLED: Final = "runtime_pid_layer_enabled"
RUNTIME_LEARNING_ENABLED: Final = "runtime_learning_enabled"
RUNTIME_COMFORT_MODE_ENABLED: Final = "runtime_comfort_mode_enabled"
RUNTIME_PRESENCE_AWAY_MIN: Final = "runtime_presence_away_min"
RUNTIME_PRESENCE_RETURN_MIN: Final = "runtime_presence_return_min"
RUNTIME_PID_KP: Final = "runtime_pid_kp"
RUNTIME_PID_KI: Final = "runtime_pid_ki"
RUNTIME_PID_KD: Final = "runtime_pid_kd"
RUNTIME_PID_DEADBAND_C: Final = "runtime_pid_deadband_c"
RUNTIME_PID_INTEGRAL_LIMIT: Final = "runtime_pid_integral_limit"
RUNTIME_PID_OFFSET_MAX_C: Final = "runtime_pid_offset_max_c"
RUNTIME_CONFIDENCE_THRESHOLD: Final = "runtime_confidence_threshold"
RUNTIME_REVERT_TIMEOUT_MIN: Final = "runtime_revert_timeout_min"
RUNTIME_AI_DECISION_INTERVAL_MIN: Final = "runtime_ai_decision_interval_min"
RUNTIME_REPORT_INTERVAL_MIN: Final = "runtime_report_interval_min"
