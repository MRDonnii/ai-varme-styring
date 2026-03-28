"""Coordinator and AI motor for AI Varme Styring."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.climate.const import HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .ai_client import AiProviderClient
from .const import (
    AI_PROVIDER_GEMINI,
    AI_PROVIDER_OLLAMA,
    CONF_AI_MODEL_FAST,
    CONF_AI_MODEL_REPORT,
    CONF_AI_PROVIDER,
    CONF_DECIMALS,
    CONF_DISTRICT_HEAT_CONSUMPTION_SENSOR,
    CONF_DISTRICT_HEAT_PRICE_SENSOR,
    CONF_ELECTRICITY_PRICE_SENSOR,
    CONF_ENABLE_PRESENCE_ECO,
    CONF_ENABLE_PRICE_AWARENESS,
    CONF_FLOW_LIMIT_MARGIN_C,
    CONF_GAS_PRICE_SENSOR,
    CONF_GAS_CONSUMPTION_SENSOR,
    CONF_GEMINI_API_KEY,
    CONF_GEMINI_MODEL_FAST,
    CONF_GEMINI_MODEL_REPORT,
    CONF_OLLAMA_HOST,
    CONF_OUTDOOR_TEMP_SENSOR,
    CONF_PRESENCE_AWAY_MIN,
    CONF_PRESENCE_RETURN_MIN,
    CONF_PRICE_MARGIN,
    CONF_RADIATOR_BOOST_C,
    CONF_RADIATOR_SETBACK_C,
    CONF_ROOMS,
    CONF_ROOM_ANTI_SHORT_CYCLE_MIN,
    CONF_ROOM_HEAT_PUMP,
    CONF_ROOM_LINK_GROUP,
    CONF_ROOM_MASSIVE_OVERHEAT_C,
    CONF_ROOM_MASSIVE_OVERHEAT_MIN,
    CONF_ROOM_NAME,
    CONF_ROOM_OCCUPANCY_SENSORS,
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
    DEFAULT_AI_MODEL_FAST,
    DEFAULT_AI_MODEL_REPORT,
    DEFAULT_AI_PROVIDER,
    DEFAULT_DECIMALS,
    DEFAULT_FLOW_LIMIT_MARGIN_C,
    DEFAULT_PRICE_MARGIN,
    DEFAULT_PRESENCE_AWAY_MIN,
    DEFAULT_PRESENCE_RETURN_MIN,
    DEFAULT_RADIATOR_BOOST_C,
    DEFAULT_RADIATOR_SETBACK_C,
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
    DEFAULT_UPDATE_SECONDS,
    DOMAIN,
    RUNTIME_ECO_TARGET,
    RUNTIME_ENABLED,
    RUNTIME_GLOBAL_TARGET,
    RUNTIME_PID_LAYER_ENABLED,
    RUNTIME_PRESENCE_ECO_ENABLED,
)

LOGGER = logging.getLogger(__name__)
_STORE_VERSION = 1


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


@dataclass
class RoomSnapshot:
    """Room state used by AI motor."""

    name: str
    sensor_entity: str
    raw_temperature: float
    temperature: float
    target: float
    deficit: float
    surplus: float
    opening_active: bool
    occupancy_active: bool
    heat_pump: str | None
    radiators: list[str]
    link_group: str
    anti_short_cycle_min: float
    quick_start_deficit_c: float
    start_deficit_c: float
    stop_surplus_c: float
    pause_after_open_min: float
    resume_after_closed_min: float
    massive_overheat_c: float
    massive_overheat_min: float


class AiVarmeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """AI engine and state coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.ai_client = AiProviderClient(hass)
        self._room_runtime: dict[str, dict[str, Any]] = {}
        self._ai_factor: float = 1.0
        self._ai_reason: str = "AI standard"
        self._last_ai_update = None
        self._manual_baseline: dict[str, dict[str, Any]] = {}
        self._runtime_events: dict[str, float | None] = {
            "enabled_last_changed": None,
            "presence_eco_last_changed": None,
            "pid_last_changed": None,
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
        baseline = data.get("manual_baseline")
        if isinstance(baseline, dict):
            self._manual_baseline = baseline
        events = data.get("runtime_events")
        if isinstance(events, dict):
            for key in self._runtime_events:
                val = events.get(key)
                if isinstance(val, (int, float)):
                    self._runtime_events[key] = float(val)
        factor = data.get("ai_factor")
        reason = data.get("ai_reason")
        last_ai = data.get("last_ai_update_ts")
        if isinstance(factor, (int, float)):
            self._ai_factor = float(factor)
        if isinstance(reason, str):
            self._ai_reason = reason
        if isinstance(last_ai, (int, float)):
            self._last_ai_update = float(last_ai)

    async def _async_save_runtime(self) -> None:
        await self._store.async_save(
            {
                "room_runtime": self._room_runtime,
                "manual_baseline": self._manual_baseline,
                "runtime_events": self._runtime_events,
                "ai_factor": self._ai_factor,
                "ai_reason": self._ai_reason,
                "last_ai_update_ts": self._last_ai_update,
            }
        )

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

    async def _async_update_data(self) -> dict[str, Any]:
        await self._async_load_runtime()
        cfg = {**self.entry.data, **self.entry.options}
        runtime = self.hass.data[DOMAIN][self.entry.entry_id]
        now = dt_util.utcnow()
        now_ts = now.timestamp()

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

        ai_provider = str(cfg.get(CONF_AI_PROVIDER, DEFAULT_AI_PROVIDER))
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

        vacuum_entity: str | None = cfg.get(CONF_VACUUM_ENTITY)
        vacuum_running = (
            self.hass.states.get(vacuum_entity).state == "cleaning"
            if vacuum_entity and self.hass.states.get(vacuum_entity)
            else False
        )

        rooms_cfg: list[dict[str, Any]] = list(cfg.get(CONF_ROOMS, []))
        occupancy_global = False
        for room_cfg in rooms_cfg:
            for sensor in room_cfg.get(CONF_ROOM_OCCUPANCY_SENSORS, []):
                st = self.hass.states.get(sensor)
                if st and _is_on(st.state):
                    occupancy_global = True
                    break
            if occupancy_global:
                break

        presence_away_min = float(cfg.get(CONF_PRESENCE_AWAY_MIN, DEFAULT_PRESENCE_AWAY_MIN))
        presence_return_min = float(cfg.get(CONF_PRESENCE_RETURN_MIN, DEFAULT_PRESENCE_RETURN_MIN))
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
        target_base = eco_target if presence_eco_active else global_target

        rooms: list[RoomSnapshot] = []
        unavailable = 0
        for idx, room_cfg in enumerate(rooms_cfg):
            name = str(room_cfg.get(CONF_ROOM_NAME) or f"Rum {idx + 1}")
            temp_entity = room_cfg.get(CONF_ROOM_TEMP_SENSOR)
            if not temp_entity:
                unavailable += 1
                continue
            st = self.hass.states.get(temp_entity)
            raw_temp = _safe_float(st.state if st else None)
            if raw_temp is None:
                unavailable += 1
                continue

            bias = float(room_cfg.get(CONF_ROOM_SENSOR_BIAS_C, DEFAULT_ROOM_SENSOR_BIAS_C))
            adj_temp = raw_temp - bias

            target = target_base
            tgt_number = room_cfg.get(CONF_ROOM_TARGET_NUMBER)
            if tgt_number:
                tgt_state = self.hass.states.get(tgt_number)
                tgt = _safe_float(tgt_state.state if tgt_state else None)
                if tgt is not None:
                    target = tgt

            opening_active = any(
                _is_on(self.hass.states.get(s).state if self.hass.states.get(s) else None)
                for s in room_cfg.get(CONF_ROOM_OPENING_SENSORS, [])
            )
            occupancy_active = any(
                _is_on(self.hass.states.get(s).state if self.hass.states.get(s) else None)
                for s in room_cfg.get(CONF_ROOM_OCCUPANCY_SENSORS, [])
            )

            rooms.append(
                RoomSnapshot(
                    name=name,
                    sensor_entity=temp_entity,
                    raw_temperature=raw_temp,
                    temperature=adj_temp,
                    target=target,
                    deficit=max(target - adj_temp, 0.0),
                    surplus=max(adj_temp - target, 0.0),
                    opening_active=opening_active,
                    occupancy_active=occupancy_active,
                    heat_pump=room_cfg.get(CONF_ROOM_HEAT_PUMP),
                    radiators=list(room_cfg.get(CONF_ROOM_RADIATORS, [])),
                    link_group=str(room_cfg.get(CONF_ROOM_LINK_GROUP, DEFAULT_ROOM_LINK_GROUP)).strip().lower(),
                    anti_short_cycle_min=float(
                        room_cfg.get(CONF_ROOM_ANTI_SHORT_CYCLE_MIN, DEFAULT_ROOM_ANTI_SHORT_CYCLE_MIN)
                    ),
                    quick_start_deficit_c=float(
                        room_cfg.get(CONF_ROOM_QUICK_START_DEFICIT_C, DEFAULT_ROOM_QUICK_START_DEFICIT_C)
                    ),
                    start_deficit_c=float(
                        room_cfg.get(
                            CONF_ROOM_START_DEFICIT_C,
                            cfg.get(CONF_START_DEFICIT_C, DEFAULT_ROOM_START_DEFICIT_C),
                        )
                    ),
                    stop_surplus_c=float(
                        room_cfg.get(
                            CONF_ROOM_STOP_SURPLUS_C,
                            cfg.get(CONF_STOP_SURPLUS_C, DEFAULT_ROOM_STOP_SURPLUS_C),
                        )
                    ),
                    pause_after_open_min=float(
                        room_cfg.get(CONF_ROOM_PAUSE_AFTER_OPEN_MIN, DEFAULT_ROOM_PAUSE_AFTER_OPEN_MIN)
                    ),
                    resume_after_closed_min=float(
                        room_cfg.get(CONF_ROOM_RESUME_AFTER_CLOSED_MIN, DEFAULT_ROOM_RESUME_AFTER_CLOSED_MIN)
                    ),
                    massive_overheat_c=float(
                        room_cfg.get(CONF_ROOM_MASSIVE_OVERHEAT_C, DEFAULT_ROOM_MASSIVE_OVERHEAT_C)
                    ),
                    massive_overheat_min=float(
                        room_cfg.get(CONF_ROOM_MASSIVE_OVERHEAT_MIN, DEFAULT_ROOM_MASSIVE_OVERHEAT_MIN)
                    ),
                )
            )

        max_deficit = max((r.deficit for r in rooms), default=0.0)
        max_surplus = max((r.surplus for r in rooms), default=0.0)

        el_price = _safe_float(
            self.hass.states.get(cfg.get(CONF_ELECTRICITY_PRICE_SENSOR, "")).state
            if cfg.get(CONF_ELECTRICITY_PRICE_SENSOR) and self.hass.states.get(cfg.get(CONF_ELECTRICITY_PRICE_SENSOR))
            else None
        )
        gas_price = _safe_float(
            self.hass.states.get(cfg.get(CONF_GAS_PRICE_SENSOR, "")).state
            if cfg.get(CONF_GAS_PRICE_SENSOR) and self.hass.states.get(cfg.get(CONF_GAS_PRICE_SENSOR))
            else None
        )
        district_heat_price = _safe_float(
            self.hass.states.get(cfg.get(CONF_DISTRICT_HEAT_PRICE_SENSOR, "")).state
            if cfg.get(CONF_DISTRICT_HEAT_PRICE_SENSOR)
            and self.hass.states.get(cfg.get(CONF_DISTRICT_HEAT_PRICE_SENSOR))
            else None
        )
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
        price_margin = float(cfg.get(CONF_PRICE_MARGIN, DEFAULT_PRICE_MARGIN))
        price_awareness = bool(cfg.get(CONF_ENABLE_PRICE_AWARENESS, True))
        heat_pump_cheaper = (
            el_price is not None and gas_price is not None and (gas_price - el_price) >= price_margin
        )
        cheapest_alt_price = None
        cheapest_alt_name = None
        for name, price in (("Gas", gas_price), ("Fjernvarme", district_heat_price)):
            if price is None:
                continue
            if cheapest_alt_price is None or price < cheapest_alt_price:
                cheapest_alt_price = price
                cheapest_alt_name = name
        estimated_savings_per_kwh = None
        if el_price is not None and cheapest_alt_price is not None:
            estimated_savings_per_kwh = round(max(cheapest_alt_price - el_price, 0.0), decimals)
        estimated_daily_savings = None
        if estimated_savings_per_kwh is not None and district_heat_consumption is not None:
            estimated_daily_savings = round(estimated_savings_per_kwh * district_heat_consumption, decimals)

        flow_limit_margin = float(cfg.get(CONF_FLOW_LIMIT_MARGIN_C, DEFAULT_FLOW_LIMIT_MARGIN_C))
        radiator_boost = float(cfg.get(CONF_RADIATOR_BOOST_C, DEFAULT_RADIATOR_BOOST_C))
        radiator_setback = float(cfg.get(CONF_RADIATOR_SETBACK_C, DEFAULT_RADIATOR_SETBACK_C))

        if provider_ready and _minutes_since(self._last_ai_update, now_ts) >= 2:
            outdoor_for_ai = None
            if cfg.get(CONF_OUTDOOR_TEMP_SENSOR):
                s = self.hass.states.get(cfg.get(CONF_OUTDOOR_TEMP_SENSOR))
                outdoor_for_ai = _safe_float(s.state if s else None)
            if outdoor_for_ai is None and cfg.get(CONF_WEATHER_ENTITY):
                w = self.hass.states.get(cfg.get(CONF_WEATHER_ENTITY))
                outdoor_for_ai = _safe_float((w.attributes if w else {}).get("temperature"))
            ai_payload = {
                "max_deficit": round(max_deficit, 2),
                "max_surplus": round(max_surplus, 2),
                "price_awareness": price_awareness,
                "heat_pump_cheaper": heat_pump_cheaper,
                "outdoor_temp": outdoor_for_ai,
                "rooms": [
                    {"name": r.name, "temp": round(r.temperature, 2), "target": round(r.target, 2)}
                    for r in rooms
                ],
            }
            self._ai_factor, self._ai_reason = await self.ai_client.async_decision_factor(
                provider=ai_provider,
                endpoint=provider_endpoint,
                api_key=provider_api_key,
                model=ai_model_fast,
                payload=ai_payload,
            )
            self._last_ai_update = now_ts

        actions: list[str] = []
        opening_active_any = any(r.opening_active for r in rooms)
        flow_limited = any(r.temperature >= (r.target + flow_limit_margin) for r in rooms)
        pid_rows: list[dict[str, Any]] = []
        if enabled and provider_ready:
            allow_heat_pumps = (not price_awareness) or heat_pump_cheaper
            for room in rooms:
                rt = self._room_runtime.setdefault(
                    room.name,
                    {
                        "open_since": None,
                        "closed_since": None,
                        "paused_by_open": False,
                        "last_hvac_mode": "heat",
                        "last_switch": None,
                        "overheat_since": None,
                        "pid_integral": 0.0,
                        "pid_last_error": None,
                        "pid_last_ts": None,
                    },
                )

                if room.opening_active:
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

                if room.heat_pump and rt["paused_by_open"]:
                    if _minutes_since(rt["closed_since"], now_ts) >= room.resume_after_closed_min:
                        restore = str(rt.get("last_hvac_mode", "heat"))
                        if restore not in {"heat", "cool", "auto", "dry", "fan_only", "heat_cool"}:
                            restore = "heat"
                        await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode(restore), actions)
                        rt["paused_by_open"] = False
                        rt["last_switch"] = now_ts
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
                hp_boost = 0.0
                if room.deficit >= 1.2:
                    hp_boost = 2.0
                elif room.deficit >= 0.5:
                    hp_boost = 1.0
                hp_boost = round(hp_boost * self._ai_factor, 1)

                pid_output = 0.0
                if pid_enabled:
                    last_pid_ts = rt.get("pid_last_ts")
                    dt_min = min(max(_minutes_since(last_pid_ts, now_ts), 0.1), 10.0)
                    integral = float(rt.get("pid_integral", 0.0)) + (error * dt_min)
                    integral = max(-6.0, min(6.0, integral))
                    last_error = rt.get("pid_last_error")
                    derivative = 0.0
                    if isinstance(last_error, (int, float)):
                        derivative = (error - float(last_error)) / dt_min
                    kp, ki, kd = 0.7, 0.08, 0.25
                    pid_output = (kp * error) + (ki * integral) + (kd * derivative)
                    pid_output = max(-2.5, min(2.5, pid_output))
                    rt["pid_integral"] = integral
                    rt["pid_last_error"] = error
                    rt["pid_last_ts"] = now_ts

                hp_target = round(max(16.0, min(30.0, room.target + hp_boost)), decimals)
                if linked_hot or room.surplus >= room.stop_surplus_c:
                    hp_target = round(room.target, decimals)

                allow_start = (
                    room.deficit >= room.start_deficit_c
                    and allow_heat_pumps
                    and not massive_overheat_active
                )
                last_switch = rt.get("last_switch")
                if allow_start:
                    if _minutes_since(last_switch, now_ts) < room.anti_short_cycle_min and room.deficit < room.quick_start_deficit_c:
                        allow_start = False

                if room.heat_pump:
                    if allow_start:
                        if pid_enabled:
                            hp_target = round(
                                max(16.0, min(30.0, room.target + max(hp_boost, max(0.0, pid_output)))),
                                decimals,
                            )
                        await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode.HEAT, actions)
                        await self._async_set_temperature_if_needed(room.heat_pump, hp_target, actions)
                    elif massive_overheat_active or room.surplus >= room.stop_surplus_c or (price_awareness and not allow_heat_pumps):
                        await self._async_set_hvac_mode_if_needed(room.heat_pump, HVACMode.OFF, actions)

                rad_target = round(
                    max(7.0, min(25.0, (room.target - radiator_setback) + (radiator_boost if (room.deficit > 0 and linked_hot) else 0))),
                    decimals,
                )
                for rad in room.radiators:
                    await self._async_set_temperature_if_needed(rad, rad_target, actions)

                pid_rows.append(
                    {
                        "rum": room.name,
                        "error": round(error, decimals),
                        "integral": round(float(rt.get("pid_integral", 0.0)), decimals),
                        "output": round(pid_output, decimals),
                        "setpunkt": hp_target if room.heat_pump else None,
                    }
                )
        elif enabled and not provider_ready:
            actions.append("AI provider ikke klar - styring pauset")

        outdoor_temp = None
        if cfg.get(CONF_OUTDOOR_TEMP_SENSOR):
            st = self.hass.states.get(cfg[CONF_OUTDOOR_TEMP_SENSOR])
            outdoor_temp = _safe_float(st.state if st else None)
        if outdoor_temp is None and cfg.get(CONF_WEATHER_ENTITY):
            weather_state = self.hass.states.get(cfg[CONF_WEATHER_ENTITY])
            outdoor_temp = _safe_float((weather_state.attributes if weather_state else {}).get("temperature"))

        report = self._build_report(
            ai_provider=ai_provider,
            ai_model_fast=ai_model_fast,
            ai_model_report=ai_model_report,
            provider_ready=provider_ready,
            target_base=round(target_base, decimals),
            flow_limited=flow_limited,
            heat_pump_cheaper=heat_pump_cheaper,
            cheapest_alt_name=cheapest_alt_name,
            estimated_savings_per_kwh=estimated_savings_per_kwh,
            estimated_daily_savings=estimated_daily_savings,
            rooms=rooms,
            actions=actions,
            decimals=decimals,
        )

        await self._async_save_runtime()

        return {
            "updated_at": dt_util.now().strftime("%Y-%m-%d %H:%M:%S"),
            "enabled": enabled,
            "ai_provider": ai_provider,
            "ai_model_fast": ai_model_fast,
            "ai_model_report": ai_model_report,
            "ai_provider_ready": provider_ready,
            "ai_provider_endpoint": provider_endpoint,
            "ai_factor": self._ai_factor,
            "ai_reason": self._ai_reason,
            "enabled_last_changed": _fmt_ts(self._runtime_events.get("enabled_last_changed")),
            "presence_eco_enabled": presence_eco_enabled,
            "presence_eco_active": presence_eco_active,
            "presence_eco_last_changed": _fmt_ts(
                self._runtime_events.get("presence_eco_last_changed")
                or self._room_runtime.get("__presence__", {}).get("last_change")
            ),
            "pid_enabled": pid_enabled,
            "pid_last_changed": _fmt_ts(self._runtime_events.get("pid_last_changed")),
            "pid_status": "Aktiv" if pid_enabled else "Inaktiv",
            "pid_rooms": pid_rows,
            "vacuum_running": vacuum_running,
            "target_base": round(target_base, decimals),
            "outdoor_temp": outdoor_temp,
            "el_price": el_price,
            "gas_price": gas_price,
            "district_heat_price": district_heat_price,
            "district_heat_consumption": district_heat_consumption,
            "gas_consumption": gas_consumption,
            "heat_pump_cheaper": heat_pump_cheaper,
            "cheapest_alt_name": cheapest_alt_name,
            "estimated_savings_per_kwh": estimated_savings_per_kwh,
            "estimated_daily_savings": estimated_daily_savings,
            "price_awareness": price_awareness,
            "flow_limited": flow_limited,
            "opening_active": opening_active_any,
            "max_deficit": round(max_deficit, decimals),
            "max_surplus": round(max_surplus, decimals),
            "unavailable_sensors": unavailable,
            "rooms": [
                {
                    "name": r.name,
                    "sensor": r.sensor_entity,
                    "temperature_raw": round(r.raw_temperature, decimals),
                    "temperature": round(r.temperature, decimals),
                    "target": round(r.target, decimals),
                    "deficit": round(r.deficit, decimals),
                    "surplus": round(r.surplus, decimals),
                    "opening_active": r.opening_active,
                    "occupancy_active": r.occupancy_active,
                    "heat_pump": r.heat_pump,
                    "radiators": r.radiators,
                    "link_group": r.link_group,
                }
                for r in rooms
            ],
            "actions": actions[-25:],
            "report": report,
        }

    def _build_report(
        self,
        *,
        ai_provider: str,
        ai_model_fast: str,
        ai_model_report: str,
        provider_ready: bool,
        target_base: float,
        flow_limited: bool,
        heat_pump_cheaper: bool,
        cheapest_alt_name: str | None,
        estimated_savings_per_kwh: float | None,
        estimated_daily_savings: float | None,
        rooms: list[RoomSnapshot],
        actions: list[str],
        decimals: int,
    ) -> dict[str, str | list[str]]:
        provider_name = "Gemini" if ai_provider == AI_PROVIDER_GEMINI else "Ollama"
        cold_rooms = [r for r in rooms if r.deficit > 0.2]
        hot_rooms = [r for r in rooms if r.surplus > 0.4]
        cold_txt = ", ".join(f"{r.name} ({round(r.deficit, decimals)}°C)" for r in cold_rooms) or "Ingen"
        hot_txt = ", ".join(f"{r.name} ({round(r.surplus, decimals)}°C)" for r in hot_rooms) or "Ingen"

        bullets = [
            f"AI-provider: {provider_name}",
            f"Hurtig model: {ai_model_fast}",
            f"Rapport model: {ai_model_report}",
            f"Provider klar: {'Ja' if provider_ready else 'Nej'}",
            f"AI-faktor: {self._ai_factor:.1f} ({self._ai_reason})",
            f"Globalt mål: {target_base:.{decimals}f}°C",
            f"Billigste varmekilde nu: {'Varmepumpe' if heat_pump_cheaper else 'Radiator/Gas'}",
            f"Sammenlignet mod: {cheapest_alt_name or 'Ingen'}",
            f"Estimeret besparelse: {estimated_savings_per_kwh if estimated_savings_per_kwh is not None else '-'} kr/kWh",
            f"Estimeret dagsbesparelse: {estimated_daily_savings if estimated_daily_savings is not None else '-'} kr/dag",
            f"Kolde rum: {cold_txt}",
            f"Varme rum: {hot_txt}",
            f"Flowbegrænsning: {'Aktiv' if flow_limited else 'Inaktiv'}",
        ]
        if actions:
            bullets.append(f"Seneste handling: {actions[-1]}")
        return {
            "short": " | ".join(bullets[:3]),
            "long": "Omhandler:\n" + "\n".join(f"- {b}" for b in bullets),
            "bullets": bullets,
        }

    async def _async_set_hvac_mode_if_needed(self, climate_entity: str, mode: HVACMode, actions: list[str]) -> None:
        state = self.hass.states.get(climate_entity)
        if not state or state.state == mode:
            return
        self._remember_manual_baseline(climate_entity)
        await self.hass.services.async_call(
            "climate",
            "set_hvac_mode",
            {"entity_id": climate_entity, "hvac_mode": mode},
            blocking=False,
        )
        actions.append(f"{climate_entity}: hvac_mode -> {mode}")

    async def _async_set_temperature_if_needed(self, climate_entity: str, temperature: float, actions: list[str]) -> None:
        state = self.hass.states.get(climate_entity)
        if not state:
            return
        cur = _safe_float(state.attributes.get("temperature"))
        if cur is not None and abs(cur - temperature) < 0.05:
            return
        self._remember_manual_baseline(climate_entity)
        await self.hass.services.async_call(
            "climate",
            "set_temperature",
            {"entity_id": climate_entity, "temperature": temperature},
            blocking=False,
        )
        actions.append(f"{climate_entity}: setpoint -> {temperature}")
