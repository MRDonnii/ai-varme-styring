"""AI provider helper for AI Varme Styring."""

from __future__ import annotations

import asyncio
import contextlib
import datetime as dt
import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    AI_ENGINE_NONE,
    AI_PROVIDER_GEMINI,
    AI_PROVIDER_OLLAMA,
)

LOGGER = logging.getLogger(__name__)
OPENCLAW_RUNTIME_TMP_DIR = Path(
    os.environ.get("OPENCLAW_RUNTIME_TMP_DIR", "/config/custom_components/ai_varme_styring/runtime/tmp")
)
OPENCLAW_SESSIONS_DIR = Path(
    os.environ.get("OPENCLAW_SESSIONS_DIR", "/openclaw-data/config/agents/main/sessions")
)
OPENCLAW_QUEUE_DIR = Path(
    os.environ.get("OPENCLAW_QUEUE_DIR", str(OPENCLAW_RUNTIME_TMP_DIR / "openclaw_decision_queue"))
)
OPENCLAW_DEBUG_LOG = Path(
    os.environ.get("OPENCLAW_DEBUG_LOG", str(OPENCLAW_RUNTIME_TMP_DIR / "ai_openclaw_debug.log"))
)
OPENCLAW_DEBUG_ENABLED = os.environ.get("OPENCLAW_DEBUG_ENABLED", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
OPENCLAW_RESULTS_FILE = Path(
    os.environ.get(
        "OPENCLAW_COMPLETION_RESULTS_FILE",
        str(OPENCLAW_RUNTIME_TMP_DIR / "openclaw_completion_results.json"),
    )
)
OPENCLAW_RESULTS_FILE_HOST = Path("/haconfig/custom_components/ai_varme_styring/runtime/tmp/openclaw_completion_results.json")
OPENCLAW_QUEUE_DIR_HOST = Path("/haconfig/custom_components/ai_varme_styring/runtime/tmp/openclaw_decision_queue")
OPENCLAW_RESULTS_FILE_LEGACY = Path("/config/_tmp_openclaw_completion_results.json")
OPENCLAW_QUEUE_DIR_LEGACY = Path("/config/_tmp_openclaw_decision_queue")
OPENCLAW_QUEUE_DIR_HOST_LEGACY = Path("/haconfig/_tmp_openclaw_decision_queue")
OPENCLAW_QUEUE_ENABLED = os.environ.get("OPENCLAW_QUEUE_ENABLED", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
OPENCLAW_DIRECT_FIRST = os.environ.get("OPENCLAW_DIRECT_FIRST", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
OPENCLAW_USE_BRIDGE = os.environ.get("OPENCLAW_USE_BRIDGE", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
OPENCLAW_MQTT_DECISION_ENTITY = os.environ.get(
    "OPENCLAW_MQTT_DECISION_ENTITY",
    "sensor.ai_varme_openclaw_decision",
).strip()
OPENCLAW_MQTT_MAX_AGE_SEC = float(os.environ.get("OPENCLAW_MQTT_MAX_AGE_SEC", "300"))
OPENCLAW_REPLY_TRANSPORT = os.environ.get("OPENCLAW_REPLY_TRANSPORT", "mqtt").strip() or "mqtt"
OPENCLAW_REPLY_TOPIC = os.environ.get(
    "OPENCLAW_REPLY_TOPIC",
    "homeassistant/ai_varme/openclaw/decision",
).strip() or "homeassistant/ai_varme/openclaw/decision"
OPENCLAW_REQUEST_RE = re.compile(
    r"\b([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b",
    re.I,
)
OPENCLAW_FACTOR_RE = re.compile(r'"factor"\s*:\s*(-?\d+(?:\.\d+)?)', re.I)
OPENCLAW_CONFIDENCE_RE = re.compile(r'"confidence"\s*:\s*(-?\d+(?:\.\d+)?)', re.I)
OPENCLAW_REASON_RE = re.compile(r'"reason"\s*:\s*"((?:\\.|[^"\\])*)"', re.I)


class AiProviderClient:
    """Small wrapper around AI providers."""

    def _reconcile_reason_with_payload(
        self,
        payload: dict[str, Any],
        factor: float,
        reason: str,
        confidence: float,
        data: dict[str, Any],
    ) -> tuple[float, str, float, dict[str, Any]]:
        rooms = payload.get("rooms") if isinstance(payload, dict) else None
        if not isinstance(rooms, list):
            return factor, reason, confidence, data
        deficit_rooms: list[tuple[str, float, bool, float, bool]] = []
        cold_without_heat: list[tuple[str, float]] = []
        comfort_sensitive_rooms: list[tuple[str, float, str]] = []
        for room in rooms:
            if not isinstance(room, dict):
                continue
            try:
                deficit = float(room.get("deficit") or 0.0)
            except Exception:
                deficit = 0.0
            try:
                comfort_gap = float(room.get("comfort_gap") or 0.0)
            except Exception:
                comfort_gap = 0.0
            effective_gap = max(deficit, comfort_gap)
            heating = bool(room.get("is_heating_now"))
            name = str(room.get("name") or "Rum")
            comfort_band = str(room.get("comfort_band") or "").strip().lower()
            if effective_gap > 0.05:
                deficit_rooms.append((name, deficit, heating, effective_gap, comfort_gap > deficit + 0.05))
                if effective_gap >= 0.15 and not heating:
                    cold_without_heat.append((name, effective_gap))
            if comfort_band in {"tør", "fugtig"} and effective_gap <= 0.05:
                comfort_sensitive_rooms.append((name, comfort_gap, comfort_band))
        if not deficit_rooms:
            return factor, reason, confidence, data
        reason_l = str(reason or "").strip().lower()
        misleading_phrases = [
            'alle rum er ved eller over',
            'alle rum er på eller over',
            'alle rum er over',
            'alle rum er enten ved eller over',
            'alle rum er tæt på eller over',
            'alle rum er tæt på deres måltemperatur',
            'ingen rum har underskud',
            'ingen ændring nødvendig',
            'ingen ændringer nødvendige',
            'ingen justering nødvendig',
            'ingen justeringer nødvendige',
            'ingen konkrete ændringer',
            'ingen rum kræver ændring',
            'ingen akut regulering nødvendig',
        ]
        reason_mentions_deficit = any(word in reason_l for word in ['under mål', 'under target', 'underskud', 'lidt under'])
        inaccurate_claim = (
            'ingen rum har underskud' in reason_l
            or (any(phrase in reason_l for phrase in misleading_phrases) and not reason_mentions_deficit)
        )
        if not inaccurate_claim:
            return factor, reason, confidence, data
        deficit_names = ', '.join(name for name, *_ in deficit_rooms[:3])
        if cold_without_heat:
            cold_names = ', '.join(name for name, _ in cold_without_heat[:3])
            reason = f'Nogle rum er lidt under mål; {cold_names} er under mål uden aktiv varme.'
            confidence = min(float(confidence), 82.0)
        elif comfort_sensitive_rooms and not any("fugt" in reason_l or "komfort" in reason_l for _ in [0]):
            comfort_names = ', '.join(name for name, _, _ in comfort_sensitive_rooms[:2])
            reason = f'Nogle rum er termisk tæt på mål ({deficit_names}), men komforten i {comfort_names} påvirkes også af luftfugtigheden.'
            confidence = min(float(confidence), 86.0)
        else:
            reason = f'Nogle rum er lidt under mål ({deficit_names}), men afvigelserne er små.'
            confidence = min(float(confidence), 88.0)
        updated = dict(data or {})
        updated['reason'] = reason
        updated['confidence'] = confidence
        meta = updated.get('_openclaw_meta') if isinstance(updated.get('_openclaw_meta'), dict) else {}
        updated['_openclaw_meta'] = {**meta, 'reason_reconciled': True}
        return factor, reason, confidence, updated

    def _candidate_results_files(self) -> list[Path]:
        paths: list[Path] = []
        for candidate in (
            OPENCLAW_RESULTS_FILE,
            OPENCLAW_RESULTS_FILE_HOST,
            OPENCLAW_RESULTS_FILE_LEGACY,
        ):
            if candidate not in paths:
                paths.append(candidate)
        return paths

    def _candidate_queue_dirs(self) -> list[Path]:
        paths: list[Path] = []
        env_candidate = OPENCLAW_QUEUE_DIR
        host_candidate = OPENCLAW_QUEUE_DIR_HOST
        for candidate in (
            env_candidate,
            host_candidate,
            OPENCLAW_QUEUE_DIR_LEGACY,
            OPENCLAW_QUEUE_DIR_HOST_LEGACY,
        ):
            if candidate not in paths:
                paths.append(candidate)
        return paths

    def _active_queue_dir(self) -> Path:
        for candidate in self._candidate_queue_dirs():
            if candidate.exists():
                return candidate
        return self._candidate_queue_dirs()[0]

    def _openclaw_queue_wait_budget(self, timeout_sec: float) -> float:
        """Keep queue wait short so a slow queue does not consume the whole AI window."""
        base = max(4.0, float(timeout_sec) * 0.45)
        return min(12.0, base)

    def _openclaw_session_wait_budget(self, timeout_sec: float, *, sessions_available: bool) -> float:
        """Use a shorter budget when only callback/results polling is possible."""
        extra = 12.0 if sessions_available else 4.0
        cap = 40.0 if sessions_available else 24.0
        return max(8.0, min(cap, float(timeout_sec) + extra))

    def __init__(self, hass) -> None:
        self.hass = hass
        self._debug_openclaw({"stage": "client_init"})

    def _debug_openclaw(self, payload: dict[str, Any]) -> None:
        if not OPENCLAW_DEBUG_ENABLED:
            return
        try:
            OPENCLAW_DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
            with OPENCLAW_DEBUG_LOG.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            return

    async def async_decision_factor(
        self,
        *,
        ollama_endpoint: str,
        ollama_model: str,
        gemini_api_key: str,
        gemini_model: str,
        payload_openclaw: dict[str, Any],
        payload_provider: dict[str, Any] | None = None,
        openclaw_enabled: bool = False,
        openclaw_bridge_url: str = "",
        openclaw_url: str = "",
        openclaw_token: str = "",
        openclaw_timeout_sec: float = 12.0,
        openclaw_model_preferred: str = "",
        openclaw_model_fallback: str = "",
        primary_engine: str = "openclaw",
        fallback_engine: str = AI_ENGINE_NONE,
        last_good: tuple[float, str, float] | None = None,
    ) -> tuple[float, str, float, str, dict[str, Any]]:
        """Return bounded decision factor, rationale, source, and structured decision."""
        provider_payload = payload_provider if isinstance(payload_provider, dict) else payload_openclaw
        last_engine_error: dict[str, str] = {}

        def _build_prompt(payload: dict[str, Any], request_id: str = "") -> str:
            request_hint = ""
            if request_id:
                request_hint = (
                    f"\nRequest ID: {request_id}\n"
                    "Return the same request_id unchanged in the JSON output."
                )
            model_hint = ""
            if str(openclaw_model_preferred).strip():
                model_hint += f"\nPreferred model: {str(openclaw_model_preferred).strip()}"
            if str(openclaw_model_fallback).strip():
                model_hint += f"\nFallback model: {str(openclaw_model_fallback).strip()}"
            return (
                "Return strict JSON only. No markdown, no prose before or after JSON. "
                "Use this exact schema: "
                '{'
                '"request_id": "<same request id>", '
                '"run_id": "<short id or run id>", '
                '"factor": <number between 0.6 and 1.4>, '
                '"confidence": <number 0-100>, '
                '"reason": "<short danish text>", '
                '"global": {"mode": "normal|eco|boost|off", "boost": <true|false>}, '
                '"rooms": ['
                '{"name": "<room name>", "entity_id": "<heat pump or target entity id>", '
                '"target_temperature": <number 7-25>, "mode": "heat|off|auto|eco", '
                '"should_change": <true|false>, "reason": "<short danish text>"}'
                "], "
                '"context": <object>, '
                '"diagnostics": <object>, '
                '"input_summary": {'
                '"outside_temperature": <number|null>, '
                '"mode": "<normal|night|away|boost|eco|off>", '
                '"boost": <true|false>, '
                '"room_count": <integer>, '
                '"occupied_rooms": <integer>'
                "}"
                "} "
                "Rules: "
                "Be factually consistent with the payload. "
                "If any room has deficit > 0.05 C, do not say that all rooms are at or above target. "
                "If any room has comfort_gap > deficit by more than 0.05 C, mention humidity or perceived comfort explicitly. "
                "If any room has deficit >= 0.15 C and no active heat source, strongly consider a room override or explain why not. "
                "If any room has effective comfort need >= 0.08 C and no active heat source, include it in rooms unless the room is intentionally paused because of opening or anti-short-cycle constraints. "
                "If rooms are only slightly below target but already heating, you may keep factor=1.0, but the reason must still mention the small deficit honestly. "
                "Never write both that a room is under target and that no rooms have deficit. "
                "Assess every room mentally, even if only some rooms end up in the rooms override list. "
                "Use humidity, comfort_target, comfort_gap and comfort_band when present to judge perceived comfort, not only raw temperature. "
                "If a room is dry or humid enough to affect comfort, mention that in the reason or room reason when relevant. "
                "When a room is only 0.05-0.12 C under target, be conservative but still name the room if it is the main room needing attention. "
                "If no override is needed, keep rooms as an empty list but explain the top 1-2 rooms that were closest to needing action. "
                "Only include rooms that need a concrete override. "
                "Use factor=1.0 when room overrides already express the main decision. "
                "Always include request_id and run_id in the output JSON. "
                "Always include context, diagnostics and input_summary objects in output JSON. "
                "Use short, precise Danish. "
                "Base the decision on this heating context:\n"
                + json.dumps(payload, ensure_ascii=False)
                + model_hint
                + request_hint
            )

        openclaw_prompt = _build_prompt(payload_openclaw)
        provider_prompt = _build_prompt(provider_payload)

        async def _try_openclaw() -> tuple[float, str, float, str, dict[str, Any]]:
            self._debug_openclaw(
                {
                    "stage": "try_openclaw_start",
                    "bridge_url": openclaw_bridge_url,
                    "openclaw_url": openclaw_url,
                    "has_token": bool(str(openclaw_token).strip()),
                    "model_preferred": str(openclaw_model_preferred).strip(),
                    "model_fallback": str(openclaw_model_fallback).strip(),
                    "queue_enabled": OPENCLAW_QUEUE_ENABLED,
                    "direct_first": OPENCLAW_DIRECT_FIRST,
                    "use_bridge": OPENCLAW_USE_BRIDGE,
                    "queue_dir_exists": any(path.exists() for path in self._candidate_queue_dirs()),
                    "sessions_dir_exists": OPENCLAW_SESSIONS_DIR.exists(),
                    "timeout_sec": float(openclaw_timeout_sec),
                }
            )
            # Prefer the shared-file queue path for OpenClaw decisions.
            # It lets the host-side bridge own completion delivery and avoids
            # HA-runtime session polling issues when the session directory is
            # unavailable or slow to reflect new runs.
            if OPENCLAW_QUEUE_ENABLED:
                try:
                    text, queue_source, queue_meta = await self._async_call_openclaw_queue(
                        payload=payload_openclaw,
                        ollama_endpoint=ollama_endpoint,
                        ollama_model=ollama_model,
                        timeout_sec=float(openclaw_timeout_sec),
                        openclaw_model_preferred=openclaw_model_preferred,
                        openclaw_model_fallback=openclaw_model_fallback,
                    )
                    data = self._extract_json(text)
                    if queue_meta:
                        data["_openclaw_meta"] = queue_meta
                    factor, reason, confidence = self._validate_decision_factor(data)
                    factor, reason, confidence, data = self._reconcile_reason_with_payload(payload_openclaw, factor, reason, confidence, data)
                    self._debug_openclaw({"stage": "try_openclaw_queue_ok", "source": queue_source, "meta": queue_meta})
                    return factor, reason, confidence, f"openclaw_queue:{queue_source}", data
                except Exception as err:  # noqa: BLE001
                    self._debug_openclaw({"stage": "try_openclaw_queue_error", "error": str(err)})
                    LOGGER.warning("OpenClaw queue path failed, trying next path: %s", err)
            else:
                self._debug_openclaw(
                    {
                        "stage": "try_openclaw_queue_skipped",
                        "reason": "queue_disabled",
                        "queue_wait_budget_sec": self._openclaw_queue_wait_budget(float(openclaw_timeout_sec)),
                    }
                )
            openclaw_request_id = str(uuid.uuid4())
            if OPENCLAW_DIRECT_FIRST and openclaw_enabled and str(openclaw_url).strip():
                try:
                    text = await self._async_call_openclaw(
                        url=openclaw_url,
                        token=openclaw_token,
                        prompt=_build_prompt(payload_openclaw, openclaw_request_id),
                        timeout_sec=float(openclaw_timeout_sec),
                        context_payload=payload_openclaw,
                        request_id=openclaw_request_id,
                    )
                    data = self._extract_json(text)
                    factor, reason, confidence = self._validate_decision_factor(data)
                    factor, reason, confidence, data = self._reconcile_reason_with_payload(
                        payload_openclaw, factor, reason, confidence, data
                    )
                    self._debug_openclaw({"stage": "try_openclaw_direct_inline_ok"})
                    return factor, reason, confidence, "openclaw_inline", data
                except Exception as err:  # noqa: BLE001
                    self._debug_openclaw({"stage": "try_openclaw_direct_inline_error", "error": str(err)})
                    LOGGER.warning("OpenClaw direct inline path failed, trying next path: %s", err)
            if OPENCLAW_USE_BRIDGE and str(openclaw_bridge_url).strip():
                try:
                    text, bridge_source, bridge_meta = await self._async_call_openclaw_bridge(
                        url=openclaw_bridge_url,
                        token=openclaw_token,
                        payload=payload_openclaw,
                        ollama_endpoint=ollama_endpoint,
                        ollama_model=ollama_model,
                        timeout_sec=float(openclaw_timeout_sec),
                        openclaw_model_preferred=openclaw_model_preferred,
                        openclaw_model_fallback=openclaw_model_fallback,
                    )
                    data = self._extract_json(text)
                    if bridge_meta:
                        data["_openclaw_meta"] = bridge_meta
                    factor, reason, confidence = self._validate_decision_factor(data)
                    factor, reason, confidence, data = self._reconcile_reason_with_payload(payload_openclaw, factor, reason, confidence, data)
                    self._debug_openclaw({"stage": "try_openclaw_bridge_ok", "source": bridge_source, "meta": bridge_meta})
                    return factor, reason, confidence, f"openclaw_bridge:{bridge_source}", data
                except Exception as err:  # noqa: BLE001
                    self._debug_openclaw({"stage": "try_openclaw_bridge_error", "error": str(err)})
                    LOGGER.warning("OpenClaw bridge path failed, trying direct session path: %s", err)
            elif str(openclaw_bridge_url).strip():
                self._debug_openclaw(
                    {
                        "stage": "try_openclaw_bridge_skipped",
                        "reason": "bridge_disabled_by_env",
                    }
                )
            request_id = openclaw_request_id
            text, meta = await self._async_call_openclaw_with_session(
                url=openclaw_url,
                token=openclaw_token,
                prompt=_build_prompt(payload_openclaw, request_id),
                timeout_sec=float(openclaw_timeout_sec),
                request_id=request_id,
                context_payload=payload_openclaw,
                openclaw_model_preferred=openclaw_model_preferred,
                openclaw_model_fallback=openclaw_model_fallback,
            )
            data = self._extract_json(text)
            if meta:
                data["_openclaw_meta"] = meta
            factor, reason, confidence = self._validate_decision_factor(data)
            factor, reason, confidence, data = self._reconcile_reason_with_payload(payload_openclaw, factor, reason, confidence, data)
            self._debug_openclaw({"stage": "try_openclaw_direct_ok", "meta": meta})
            return factor, reason, confidence, "openclaw_session", data

        async def _try_ollama() -> tuple[float, str, float, str, dict[str, Any]]:
            text = await self._async_call_ollama(
                ollama_endpoint, ollama_model, provider_prompt, expect_json=True
            )
            data = self._extract_json(text)
            factor, reason, confidence = self._validate_decision_factor(data)
            return factor, reason, confidence, AI_PROVIDER_OLLAMA, data

        async def _try_gemini() -> tuple[float, str, float, str, dict[str, Any]]:
            text = await self._async_call_gemini(gemini_api_key, gemini_model, provider_prompt)
            data = self._extract_json(text)
            factor, reason, confidence = self._validate_decision_factor(data)
            return factor, reason, confidence, AI_PROVIDER_GEMINI, data

        engine_order: list[str] = [str(primary_engine or "").strip().lower()]
        fallback_engine_norm = str(fallback_engine or "").strip().lower()
        if fallback_engine_norm and fallback_engine_norm != AI_ENGINE_NONE and fallback_engine_norm not in engine_order:
            engine_order.append(fallback_engine_norm)

        for source in engine_order:
            try:
                if source == "openclaw":
                    if not (
                        str(openclaw_bridge_url).strip()
                        or (openclaw_enabled and str(openclaw_url).strip())
                    ):
                        continue
                    return await _try_openclaw()
                if source == AI_PROVIDER_OLLAMA:
                    if not (str(ollama_endpoint).strip() and str(ollama_model).strip()):
                        continue
                    return await _try_ollama()
                if source == AI_PROVIDER_GEMINI:
                    if not (str(gemini_api_key).strip() and str(gemini_model).strip()):
                        continue
                    return await _try_gemini()
            except Exception as err:  # noqa: BLE001
                last_engine_error[source] = str(err)
                LOGGER.warning("%s decision failed, fallback chain continues: %s", source, err)

        mqtt_decision = self._mqtt_sensor_decision()
        if isinstance(mqtt_decision, dict):
            try:
                factor, reason, confidence = self._validate_decision_factor(mqtt_decision)
                return factor, reason, confidence, "openclaw_mqtt_sensor", mqtt_decision
            except Exception as err:  # noqa: BLE001
                last_engine_error["openclaw_mqtt_sensor"] = str(err)

        if last_good is not None:
            try:
                factor, reason, confidence = self._validate_decision_factor(
                    {
                        "factor": last_good[0],
                        "reason": last_good[1],
                        "confidence": last_good[2],
                    }
                )
                return factor, reason, confidence, "last_good", {
                    "factor": factor,
                    "reason": reason,
                    "confidence": confidence,
                    "_errors": last_engine_error,
                }
            except Exception:  # noqa: BLE001
                pass

        # Fail soft: keep deterministic control active without hard provider-error state.
        return 1.0, "AI fallback regelmotor", 55.0, "safe_default", {
            "factor": 1.0,
            "reason": "AI fallback regelmotor",
            "confidence": 55.0,
            "_errors": last_engine_error,
        }

    async def async_generate_report(
        self,
        *,
        provider: str,
        endpoint: str,
        api_key: str,
        model: str,
        payload: dict[str, Any],
    ) -> str:
        """Generate a compact Danish report in bullet format."""
        prompt = (
            "Du er en dansk varmeekspert. Skriv naturligt, flydende dansk uden maskinoversættelses-stil.\n"
            "Svar KUN som en punktliste med denne struktur:\n"
            "Omhandler:\n"
            "- 4 til 8 konkrete punkter\n"
            "Krav:\n"
            "- Hvert punkt skal være kort, klart og handlingsrelevant.\n"
            "- Brug danske fagord: måltemperatur, underskud, overskud, varmepumpe, radiator, elpris, gaspris.\n"
            "- Undgå engelske ord som setpoint, target, fallback, mode, trigger, confidence.\n"
            "- Rund tal til 1 decimal hvor relevant.\n"
            "- Ingen placeholders: 'punkt 1', 'punkt 2', 'punkt 3', 'todo', 'lorem ipsum'.\n"
            "- Ingen JSON, ingen kodeblokke, ingen ekstra overskrifter.\n"
            "Data:\n"
            + json.dumps(payload, ensure_ascii=False)
        )
        try:
            if provider == AI_PROVIDER_OLLAMA:
                return await self._async_call_ollama(endpoint, model, prompt)
            if provider == AI_PROVIDER_GEMINI:
                return await self._async_call_gemini(api_key, model, prompt)
        except Exception as err:  # noqa: BLE001
            LOGGER.debug("AI report fallback: %s", err)
        return ""

    async def _async_call_ollama(self, endpoint: str, model: str, prompt: str, *, expect_json: bool = False) -> str:
        session = async_get_clientsession(self.hass)
        url = endpoint.rstrip("/") + "/api/generate"
        payload = {"model": model, "prompt": prompt, "stream": False}
        if expect_json:
            payload["format"] = "json"
        # Keep Ollama bounded so heating decisions do not stall for ~1 minute.
        last_err: Exception | None = None
        for attempt in range(2):
            try:
                async with session.post(url, json=payload, timeout=12) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    return str(data.get("response", "")).strip()
            except Exception as err:  # noqa: BLE001
                last_err = err
                if attempt == 0:
                    await asyncio.sleep(0.6)
                    continue
                raise
        if last_err:
            raise last_err
        return ""

    async def _async_call_gemini(self, api_key: str, model: str, prompt: str) -> str:
        session = async_get_clientsession(self.hass)
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        async with session.post(url, json=payload, timeout=30) as resp:
            resp.raise_for_status()
            data = await resp.json()
            cands = data.get("candidates", [])
            if not cands:
                return ""
            parts = cands[0].get("content", {}).get("parts", [])
            if not parts:
                return ""
            return str(parts[0].get("text", "")).strip()

    async def _async_call_openclaw(
        self,
        *,
        url: str,
        token: str,
        prompt: str,
        timeout_sec: float,
        context_payload: dict[str, Any] | None = None,
        request_id: str = "",
    ) -> str:
        """Call OpenClaw webhook endpoint and normalize text output for JSON parsing."""
        session = async_get_clientsession(self.hass)
        headers = {"Content-Type": "application/json"}
        if str(token).strip():
            headers["Authorization"] = f"Bearer {token.strip()}"
        payload: dict[str, Any] = dict(context_payload) if isinstance(context_payload, dict) else {}
        payload.setdefault("type", "heating_decision")
        if request_id:
            payload["request_id"] = request_id
        payload.setdefault("reply_transport", OPENCLAW_REPLY_TRANSPORT)
        payload.setdefault("reply_topic", OPENCLAW_REPLY_TOPIC)
        payload.update(
            {
            "message": prompt,
            "name": "HA Heating",
            "wakeMode": "now",
            "deliver": True,
            "timeoutSeconds": int(max(3, min(60, round(timeout_sec)))),
            }
        )
        async with session.post(
            str(url).strip(),
            headers=headers,
            json=payload,
            timeout=max(3.0, min(60.0, float(timeout_sec))),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            if isinstance(data, dict):
                if isinstance(data.get("response"), str):
                    return str(data.get("response", "")).strip()
                if isinstance(data.get("output"), str):
                    return str(data.get("output", "")).strip()
                if isinstance(data.get("text"), str):
                    return str(data.get("text", "")).strip()
                if isinstance(data.get("message"), str):
                    return str(data.get("message", "")).strip()
                if any(k in data for k in ("factor", "confidence", "reason")):
                    return json.dumps(data, ensure_ascii=False)
            if isinstance(data, str):
                return data.strip()
            return json.dumps(data, ensure_ascii=False)

    async def _async_call_openclaw_with_session(
        self,
        *,
        url: str,
        token: str,
        prompt: str,
        timeout_sec: float,
        request_id: str,
        context_payload: dict[str, Any] | None = None,
        openclaw_model_preferred: str = "",
        openclaw_model_fallback: str = "",
    ) -> tuple[str, dict[str, Any]]:
        """Call OpenClaw and poll local session files for the final JSON output."""
        normalized_url = self._normalize_openclaw_url(url)
        session = async_get_clientsession(self.hass)
        headers = {"Content-Type": "application/json"}
        if str(token).strip():
            headers["Authorization"] = f"Bearer {token.strip()}"
        body: dict[str, Any] = dict(context_payload) if isinstance(context_payload, dict) else {}
        body.setdefault("type", "heating_decision")
        body.setdefault("request_id", request_id)
        body.setdefault("reply_transport", OPENCLAW_REPLY_TRANSPORT)
        body.setdefault("reply_topic", OPENCLAW_REPLY_TOPIC)
        body.update(
            {
            "message": prompt,
            "name": f"HA Heating Bridge {request_id[:8]}",
            "wakeMode": "now",
            "deliver": True,
            "timeoutSeconds": int(max(3, min(60, round(timeout_sec)))),
            "request_id": request_id,
            "model_preferred": str(openclaw_model_preferred).strip(),
            "model_fallback": str(openclaw_model_fallback).strip(),
            }
        )
        meta: dict[str, Any] = {
            "request_id": request_id,
            "openclaw_url": normalized_url,
            "requested_model": str(openclaw_model_preferred).strip(),
            "fallback_model": str(openclaw_model_fallback).strip(),
        }
        sessions_available = OPENCLAW_SESSIONS_DIR.exists()
        meta["session_poll_available"] = sessions_available
        started = asyncio.get_running_loop().time()
        async with session.post(
            normalized_url,
            headers=headers,
            json=body,
            timeout=max(3.0, min(60.0, float(timeout_sec) + 5.0)),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            meta["openclaw_response"] = data
            if isinstance(data, dict) and isinstance(data.get("runId"), str):
                meta["openclaw_run_id"] = data.get("runId")
            parsed = self._extract_json(json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else str(data))
            if parsed and any(k in parsed for k in ("factor", "confidence", "reason")):
                return json.dumps(parsed, ensure_ascii=False), meta

        deadline = started + self._openclaw_session_wait_budget(
            timeout_sec,
            sessions_available=sessions_available,
        )
        poll_checks = 0
        while asyncio.get_running_loop().time() < deadline:
            poll_checks += 1
            callback_decision = await self.hass.async_add_executor_job(
                self._find_openclaw_callback_decision,
                request_id,
            )
            if isinstance(callback_decision, dict):
                meta["poll_checks"] = poll_checks
                meta["result_source"] = "callback_results"
                return json.dumps(callback_decision, ensure_ascii=False), meta
            if sessions_available:
                decision = await self.hass.async_add_executor_job(
                    self._find_openclaw_session_decision,
                    request_id,
                )
                if isinstance(decision, dict):
                    meta["poll_checks"] = poll_checks
                    meta["result_source"] = "session_files"
                    return json.dumps(decision, ensure_ascii=False), meta
            await asyncio.sleep(0.5)

        # Grace period: callback delivery can land just after polling deadline.
        # Keep this short to avoid blocking control flow, but reduce unnecessary
        # last_good/safe_default fallbacks.
        grace_checks = 4
        for _ in range(grace_checks):
            callback_decision = await self.hass.async_add_executor_job(
                self._find_openclaw_callback_decision,
                request_id,
            )
            if isinstance(callback_decision, dict):
                meta["poll_checks"] = poll_checks
                meta["late_callback"] = True
                meta["grace_callback_checks"] = grace_checks
                meta["result_source"] = "callback_results_late"
                return json.dumps(callback_decision, ensure_ascii=False), meta
            await asyncio.sleep(0.35)
        meta["poll_checks"] = poll_checks
        meta["grace_callback_checks"] = grace_checks
        raise TimeoutError(f"OpenClaw session result timeout for {request_id}")

    async def _async_call_openclaw_queue(
        self,
        *,
        payload: dict[str, Any],
        ollama_endpoint: str,
        ollama_model: str,
        timeout_sec: float,
        openclaw_model_preferred: str = "",
        openclaw_model_fallback: str = "",
    ) -> tuple[str, str, dict[str, Any]]:
        """Use a shared-file queue so HA can ask the host-side bridge for a decision."""
        queue_dir = self._active_queue_dir()
        await self.hass.async_add_executor_job(queue_dir.mkdir, 0o755, True, True)
        request_id = str(uuid.uuid4())
        request_path = queue_dir / f"{request_id}.request.json"
        response_path = queue_dir / f"{request_id}.response.json"
        body = {
            "request_id": request_id,
            "context": payload,
            "model": {
                "preferred": str(openclaw_model_preferred).strip(),
                "fallback": str(openclaw_model_fallback).strip(),
            },
            "fallback": {
                "ollama_endpoint": ollama_endpoint,
                "ollama_model": ollama_model,
            },
            "response_schema": {
                "factor_min": 0.6,
                "factor_max": 1.4,
                "confidence_min": 0,
                "confidence_max": 100,
            },
        }
        await self.hass.async_add_executor_job(
            request_path.write_text,
            json.dumps(body, ensure_ascii=False),
            "utf-8",
        )
        self._debug_openclaw(
            {
                "stage": "queue_request_written",
                "request_id": request_id,
                "request_path": str(request_path),
            }
        )
        deadline = asyncio.get_running_loop().time() + self._openclaw_queue_wait_budget(timeout_sec)
        try:
            while asyncio.get_running_loop().time() < deadline:
                if await self.hass.async_add_executor_job(response_path.exists):
                    raw = await self.hass.async_add_executor_job(response_path.read_text, "utf-8")
                    self._debug_openclaw(
                        {
                            "stage": "queue_response_found",
                            "request_id": request_id,
                            "response_path": str(response_path),
                            "raw": raw[:1000],
                        }
                    )
                    data = json.loads(raw)
                    source = str(data.get("source", "unknown"))
                    meta = data.get("meta", {}) if isinstance(data.get("meta"), dict) else {}
                    if isinstance(data.get("decision"), dict):
                        return json.dumps(data["decision"], ensure_ascii=False), source, meta
                    if any(k in data for k in ("factor", "confidence", "reason")):
                        return json.dumps(data, ensure_ascii=False), source, meta
                    return json.dumps(data, ensure_ascii=False), source, meta
                await asyncio.sleep(0.4)
        finally:
            for path in (request_path, response_path):
                with contextlib.suppress(Exception):
                    await self.hass.async_add_executor_job(path.unlink)
        raise TimeoutError(f"OpenClaw queue result timeout for {request_id}")

    async def _async_call_openclaw_bridge(
        self,
        *,
        url: str,
        token: str,
        payload: dict[str, Any],
        ollama_endpoint: str,
        ollama_model: str,
        timeout_sec: float,
        openclaw_model_preferred: str = "",
        openclaw_model_fallback: str = "",
    ) -> tuple[str, str, dict[str, Any]]:
        """Call a synchronous local decision bridge that returns decision JSON."""
        session = async_get_clientsession(self.hass)
        headers = {"Content-Type": "application/json"}
        if str(token).strip():
            headers["Authorization"] = f"Bearer {token.strip()}"
        body = {
            "context": payload,
            "model": {
                "preferred": str(openclaw_model_preferred).strip(),
                "fallback": str(openclaw_model_fallback).strip(),
            },
            "fallback": {
                "ollama_endpoint": ollama_endpoint,
                "ollama_model": ollama_model,
            },
            "response_schema": {
                "factor_min": 0.6,
                "factor_max": 1.4,
                "confidence_min": 0,
                "confidence_max": 100,
            },
        }
        async with session.post(
            str(url).strip(),
            headers=headers,
            json=body,
            timeout=max(3.0, min(45.0, float(timeout_sec) + 8.0)),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            if isinstance(data, dict):
                source = str(data.get("source", "unknown"))
                meta = data.get("meta", {}) if isinstance(data.get("meta"), dict) else {}
                latency_ms = data.get("latency_ms")
                if isinstance(latency_ms, (int, float)):
                    meta["latency_ms"] = int(latency_ms)
                if isinstance(data.get("decision"), dict):
                    return json.dumps(data.get("decision"), ensure_ascii=False), source, meta
                if any(k in data for k in ("factor", "confidence", "reason")):
                    return json.dumps(data, ensure_ascii=False), source, meta
                if isinstance(data.get("output"), dict):
                    return json.dumps(data.get("output"), ensure_ascii=False), source, meta
                return json.dumps(data, ensure_ascii=False), source, meta
            return json.dumps(data, ensure_ascii=False), "unknown", {}

    def _validate_decision_factor(self, data: dict[str, Any]) -> tuple[float, str, float]:
        if not isinstance(data, dict):
            raise ValueError("Decision payload must be dict")
        factor = data.get("factor", 1.0)
        confidence = data.get("confidence", 55.0)
        reason = data.get("reason", "AI standard")
        if not isinstance(factor, (int, float)):
            raise ValueError("factor must be numeric")
        if not isinstance(confidence, (int, float)):
            raise ValueError("confidence must be numeric")
        if not isinstance(reason, str):
            raise ValueError("reason must be string")
        bounded_factor = max(0.6, min(1.4, float(factor)))
        bounded_confidence = max(0.0, min(100.0, float(confidence)))
        return bounded_factor, reason.strip() or "AI standard", bounded_confidence

    def _mqtt_sensor_decision(self) -> dict[str, Any] | None:
        """Read latest MQTT decision sensor as fallback when API call paths fail."""
        entity_id = str(OPENCLAW_MQTT_DECISION_ENTITY or "").strip()
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None:
            return None

        attrs = dict(state.attributes or {})
        raw = attrs.get("raw") if isinstance(attrs.get("raw"), dict) else {}
        payload = raw if raw else attrs
        if not isinstance(payload, dict):
            return None
        factor_value = payload.get("factor")
        if factor_value is None:
            factor_value = state.state
        confidence_value = payload.get("confidence", attrs.get("confidence"))
        reason_value = payload.get("reason", attrs.get("reason"))
        if factor_value in (None, "", "unknown", "unavailable"):
            return None
        if reason_value in (None, ""):
            return None

        age_sec: float | None = None
        ts_text = payload.get("ts_utc") or attrs.get("ts_utc")
        if isinstance(ts_text, str) and ts_text.strip():
            ts_value = ts_text.strip()
            if ts_value.endswith("Z"):
                ts_value = ts_value[:-1] + "+00:00"
            try:
                parsed_ts = dt.datetime.fromisoformat(ts_value)
                if parsed_ts.tzinfo is None:
                    parsed_ts = parsed_ts.replace(tzinfo=dt.timezone.utc)
                age_sec = (dt.datetime.now(dt.timezone.utc) - parsed_ts).total_seconds()
            except Exception:  # noqa: BLE001
                age_sec = None
        elif getattr(state, "last_updated", None):
            try:
                updated = state.last_updated
                if updated.tzinfo is None:
                    updated = updated.replace(tzinfo=dt.timezone.utc)
                age_sec = (dt.datetime.now(dt.timezone.utc) - updated).total_seconds()
            except Exception:  # noqa: BLE001
                age_sec = None

        if isinstance(age_sec, (int, float)) and age_sec > OPENCLAW_MQTT_MAX_AGE_SEC:
            return None

        return {
            "factor": factor_value,
            "confidence": confidence_value,
            "reason": reason_value,
            "decision_type": payload.get("decision_type", "heating_decision"),
            "global": payload.get("global", {}),
            "rooms": payload.get("rooms", []),
            "context": payload.get("context", {}),
            "diagnostics": payload.get("diagnostics", {}),
            "input_summary": payload.get("input_summary", {}),
            "run_id": payload.get("run_id") or attrs.get("run_id"),
            "_openclaw_meta": {
                "source": "openclaw_mqtt_sensor",
                "entity_id": entity_id,
                "request_id": payload.get("request_id") or attrs.get("request_id"),
                "run_id": payload.get("run_id") or attrs.get("run_id"),
                "ts_utc": payload.get("ts_utc") or attrs.get("ts_utc"),
                "age_sec": round(float(age_sec), 2) if isinstance(age_sec, (int, float)) else None,
            },
        }

    def _normalize_openclaw_url(self, url: str) -> str:
        candidate = str(url or "").strip()
        if not candidate:
            return "http://homeassistant.local:18789/hooks/agent"
        if "127.0.0.1:18789" in candidate or "localhost:18789" in candidate:
            return "http://homeassistant.local:18789/hooks/agent"
        return candidate

    def _extract_texts_from_message(self, obj: dict[str, Any]) -> list[str]:
        message = obj.get("message") or {}
        content = message.get("content") or []
        texts: list[str] = []
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                    texts.append(item["text"])
        elif isinstance(content, str):
            texts.append(content)
        return texts

    def _find_openclaw_session_decision(self, request_id: str) -> dict[str, Any] | None:
        if not OPENCLAW_SESSIONS_DIR.exists():
            return None
        session_paths = sorted(
            OPENCLAW_SESSIONS_DIR.glob("*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for path in session_paths[:80]:
            try:
                raw_text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:  # noqa: BLE001
                continue
            matched_request = False
            for line in raw_text.splitlines():
                try:
                    obj = json.loads(line)
                except Exception:  # noqa: BLE001
                    continue
                if obj.get("type") != "message":
                    continue
                role = (obj.get("message") or {}).get("role")
                combined = "\n".join(self._extract_texts_from_message(obj)).strip()
                if not combined:
                    continue
                if role == "user":
                    if request_id in combined:
                        matched_request = True
                        continue
                    match = OPENCLAW_REQUEST_RE.search(combined)
                    if match and match.group(1).lower() == request_id.lower():
                        matched_request = True
                        continue
                if role == "assistant" and matched_request:
                    parsed = self._extract_json(combined)
                    if isinstance(parsed, dict) and all(k in parsed for k in ("factor", "confidence", "reason")):
                        return parsed
                    partial = self._extract_partial_decision(combined)
                    if isinstance(partial, dict):
                        return partial
        return None

    def _find_openclaw_callback_decision(self, request_id: str) -> dict[str, Any] | None:
        for results_file in self._candidate_results_files():
            if not results_file.exists():
                continue
            try:
                data = json.loads(results_file.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            if not isinstance(data, dict):
                continue
            row = data.get(request_id)
            if not isinstance(row, dict):
                continue
            decision = row.get("decision")
            if isinstance(decision, dict) and all(k in decision for k in ("factor", "confidence", "reason")):
                return decision
        return None

    def _extract_json(self, text: str) -> dict[str, Any]:
        text = text.strip()
        if not text:
            return {}
        if text.startswith("{") and text.endswith("}"):
            try:
                return json.loads(text)
            except Exception:  # noqa: BLE001
                partial = self._extract_partial_decision(text)
                return partial if isinstance(partial, dict) else {}
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:  # noqa: BLE001
                partial = self._extract_partial_decision(text)
                return partial if isinstance(partial, dict) else {}
        partial = self._extract_partial_decision(text)
        if isinstance(partial, dict):
            return partial
        return {}

    def _extract_partial_decision(self, text: str) -> dict[str, Any] | None:
        factor_match = OPENCLAW_FACTOR_RE.search(text)
        confidence_match = OPENCLAW_CONFIDENCE_RE.search(text)
        reason_match = OPENCLAW_REASON_RE.search(text)
        if not (factor_match and confidence_match and reason_match):
            return None
        try:
            reason = json.loads(f'"{reason_match.group(1)}"')
        except Exception:  # noqa: BLE001
            reason = reason_match.group(1)
        return {
            "factor": float(factor_match.group(1)),
            "confidence": float(confidence_match.group(1)),
            "reason": str(reason).strip(),
        }
