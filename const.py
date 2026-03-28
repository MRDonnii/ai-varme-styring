"""Constants for AI Varme Styring."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "ai_varme_styring"

PLATFORMS: Final[list[str]] = ["sensor", "switch", "number"]

CONF_NAME: Final = "name"
CONF_ROOMS: Final = "rooms"
CONF_ROOM_NAME: Final = "room_name"
CONF_ROOM_AREA_ID: Final = "room_area_id"
CONF_ROOM_TEMP_SENSOR: Final = "room_temp_sensor"
CONF_ROOM_TARGET_NUMBER: Final = "room_target_number"
CONF_ROOM_HEAT_PUMP: Final = "room_heat_pump"
CONF_ROOM_RADIATORS: Final = "room_radiators"
CONF_ROOM_OPENING_SENSORS: Final = "room_opening_sensors"
CONF_ROOM_OCCUPANCY_SENSORS: Final = "room_occupancy_sensors"
CONF_ROOM_SENSOR_BIAS_C: Final = "room_sensor_bias_c"
CONF_ROOM_LINK_GROUP: Final = "room_link_group"
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
CONF_PRESENCE_AWAY_MIN: Final = "presence_away_min"
CONF_PRESENCE_RETURN_MIN: Final = "presence_return_min"

CONF_PRICE_MARGIN: Final = "price_margin"
CONF_START_DEFICIT_C: Final = "start_deficit_c"
CONF_STOP_SURPLUS_C: Final = "stop_surplus_c"
CONF_FLOW_LIMIT_MARGIN_C: Final = "flow_limit_margin_c"
CONF_RADIATOR_BOOST_C: Final = "radiator_boost_c"
CONF_RADIATOR_SETBACK_C: Final = "radiator_setback_c"
CONF_UPDATE_SECONDS: Final = "update_seconds"
CONF_DECIMALS: Final = "decimals"
CONF_AI_PROVIDER: Final = "ai_provider"
CONF_AI_MODEL_FAST: Final = "ai_model_fast"
CONF_AI_MODEL_REPORT: Final = "ai_model_report"
CONF_OLLAMA_HOST: Final = "ollama_host"
CONF_GEMINI_API_KEY: Final = "gemini_api_key"
CONF_GEMINI_MODEL_FAST: Final = "gemini_model_fast"
CONF_GEMINI_MODEL_REPORT: Final = "gemini_model_report"
CONF_REPORT_INTERVAL_MIN: Final = "report_interval_min"

DEFAULT_NAME: Final = "AI Varme Styring"
DEFAULT_ENABLE_PRICE_AWARENESS: Final = True
DEFAULT_ENABLE_PRESENCE_ECO: Final = False
DEFAULT_ENABLE_PID_LAYER: Final = False
DEFAULT_PRESENCE_AWAY_MIN: Final = 20
DEFAULT_PRESENCE_RETURN_MIN: Final = 5
DEFAULT_PRICE_MARGIN: Final = 0.15
DEFAULT_START_DEFICIT_C: Final = 0.4
DEFAULT_STOP_SURPLUS_C: Final = 0.7
DEFAULT_FLOW_LIMIT_MARGIN_C: Final = 0.2
DEFAULT_RADIATOR_BOOST_C: Final = 0.8
DEFAULT_RADIATOR_SETBACK_C: Final = 2.0
DEFAULT_UPDATE_SECONDS: Final = 60
DEFAULT_DECIMALS: Final = 1
DEFAULT_GLOBAL_TARGET_C: Final = 22.0
DEFAULT_ECO_TARGET_C: Final = 20.0
DEFAULT_AI_PROVIDER: Final = "ollama"
DEFAULT_AI_MODEL_FAST: Final = "qwen2.5:3b"
DEFAULT_AI_MODEL_REPORT: Final = "qwen2.5:14b"
DEFAULT_OLLAMA_HOST: Final = "http://homeassistant.local:11434"
DEFAULT_GEMINI_MODEL_FAST: Final = "gemini-2.5-flash"
DEFAULT_GEMINI_MODEL_REPORT: Final = "gemini-2.5-pro"
DEFAULT_REPORT_INTERVAL_MIN: Final = 2
DEFAULT_ROOM_SENSOR_BIAS_C: Final = 0.0
DEFAULT_ROOM_LINK_GROUP: Final = ""
DEFAULT_ROOM_ANTI_SHORT_CYCLE_MIN: Final = 3
DEFAULT_ROOM_QUICK_START_DEFICIT_C: Final = 0.4
DEFAULT_ROOM_START_DEFICIT_C: Final = 0.4
DEFAULT_ROOM_STOP_SURPLUS_C: Final = 0.7
DEFAULT_ROOM_PAUSE_AFTER_OPEN_MIN: Final = 10
DEFAULT_ROOM_RESUME_AFTER_CLOSED_MIN: Final = 10
DEFAULT_ROOM_MASSIVE_OVERHEAT_C: Final = 2.0
DEFAULT_ROOM_MASSIVE_OVERHEAT_MIN: Final = 15

AI_PROVIDER_OLLAMA: Final = "ollama"
AI_PROVIDER_GEMINI: Final = "gemini"
AI_PROVIDER_OPTIONS: Final[list[str]] = [AI_PROVIDER_OLLAMA, AI_PROVIDER_GEMINI]

RUNTIME_ENABLED: Final = "runtime_enabled"
RUNTIME_GLOBAL_TARGET: Final = "runtime_global_target"
RUNTIME_ECO_TARGET: Final = "runtime_eco_target"
RUNTIME_PRESENCE_ECO_ENABLED: Final = "runtime_presence_eco_enabled"
RUNTIME_PID_LAYER_ENABLED: Final = "runtime_pid_layer_enabled"
