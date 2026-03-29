"""AI provider helper for AI Varme Styring."""

from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import AI_PROVIDER_GEMINI, AI_PROVIDER_OLLAMA

LOGGER = logging.getLogger(__name__)


class AiProviderClient:
    """Small wrapper around AI providers."""

    def __init__(self, hass) -> None:
        self.hass = hass

    async def async_decision_factor(
        self,
        *,
        provider: str,
        endpoint: str,
        api_key: str,
        model: str,
        payload: dict[str, Any],
    ) -> tuple[float, str, float]:
        """Return bounded decision factor and short rationale."""
        prompt = (
            "Return strict JSON only: "
            '{"factor": <number between 0.6 and 1.4>, "confidence": <number 0-100>, "reason": "<short danish text>"} '
            "based on this heating context:\n"
            + json.dumps(payload, ensure_ascii=False)
        )
        try:
            if provider == AI_PROVIDER_OLLAMA:
                text = await self._async_call_ollama(endpoint, model, prompt, expect_json=True)
            elif provider == AI_PROVIDER_GEMINI:
                text = await self._async_call_gemini(api_key, model, prompt)
            else:
                return 1.0, "Ukendt AI provider", 0.0
            data = self._extract_json(text)
            factor = float(data.get("factor", 1.0))
            confidence = float(data.get("confidence", 75.0))
            reason = str(data.get("reason", "AI standard"))
            factor = max(0.6, min(1.4, factor))
            confidence = max(0.0, min(100.0, confidence))
            return factor, reason, confidence
        except Exception as err:  # noqa: BLE001
            LOGGER.debug("AI decision fallback: %s", err)
            return 1.0, "AI fallback regelmotor", 0.0

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
            "Skriv kun dansk tekst i punktliste med formatet:\n"
            "Omhandler:\n"
            "- punkt 1\n"
            "- punkt 2\n"
            "- punkt 3\n"
            "Maks 8 punkter. Rund tal til 1 decimal hvor relevant.\n"
            "Undgå markdown ud over bindestreg-punkter.\n"
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
        async with session.post(url, json=payload, timeout=30) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return str(data.get("response", "")).strip()

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

    def _extract_json(self, text: str) -> dict[str, Any]:
        text = text.strip()
        if not text:
            return {}
        if text.startswith("{") and text.endswith("}"):
            return json.loads(text)
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        return {}
