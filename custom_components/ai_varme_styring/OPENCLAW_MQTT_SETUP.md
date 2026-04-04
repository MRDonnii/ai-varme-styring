# OpenClaw MQTT Setup Guide

This guide describes the public, reproducible setup for OpenClaw-based heating decisions that end up in Home Assistant through MQTT.

## Goal

Every new valid heating decision should end up on:

- `homeassistant/ai_varme/openclaw/decision`

Home Assistant can then read the result through the MQTT sensor path.

## Architecture

The working chain is:

```text
Home Assistant heating payload
-> OpenClaw analysis
-> finished heating decision JSON
-> OpenClaw forwarding script
-> MQTT topic homeassistant/ai_varme/openclaw/decision
-> Home Assistant sensor.ai_varme_openclaw_decision
```

Important rule:

- Forward only finished decision JSON to the MQTT stage.
- Do not forward raw input payloads.
- Do not use instruction-wrapper chat text as the MQTT payload.

## Decision schema expected by the MQTT stage

```json
{
  "request_id": "...",
  "run_id": "...",
  "factor": 1.0,
  "confidence": 88,
  "reason": "Short explanation",
  "global": {
    "mode": "normal",
    "boost": false
  },
  "rooms": []
}
```

## Typical local OpenClaw script chain

A practical OpenClaw-side setup can use these local scripts:

- `/root/.openclaw/workspace/scripts/publish-heating-decision.js`
- `/root/.openclaw/workspace/scripts/openclaw-ha-hook-forwarder.py`
- `/root/.openclaw/workspace/scripts/forward-ha-heating-json-to-mqtt.sh`
- `/root/.openclaw/workspace/scripts/openclaw-ha-completion-worker.py`

The simplest forwarding command shape is:

```bash
cat | /root/.openclaw/workspace/scripts/forward-ha-heating-json-to-mqtt.sh
```

## Plain text block to copy into OpenClaw-side tooling

Use this as the exact plain text instruction block when you want OpenClaw-side tooling to wire automatic forwarding correctly:

```text
Fix OpenClaw so every new valid HA Heating Bridge decision is automatically forwarded to MQTT.

Goal:
Every new valid HA Heating Bridge decision must automatically end up on:
homeassistant/ai_varme/openclaw/decision

Constraints:
- Do not use cron
- Do not add instruction-wrapper flows
- Do not forward raw input payloads
- Only forward finished decision JSON
- Reuse existing routing or worker logic if present
- Make the smallest robust change
- Verify after changes

What already exists:
- /root/.openclaw/workspace/scripts/publish-heating-decision.js
- /root/.openclaw/workspace/scripts/openclaw-ha-hook-forwarder.py
- /root/.openclaw/workspace/scripts/forward-ha-heating-json-to-mqtt.sh
- /root/.openclaw/workspace/scripts/openclaw-ha-completion-worker.py

What to do:
1. Find where valid HA Heating Bridge decision output materializes
2. Bind that output directly into:
   cat | /root/.openclaw/workspace/scripts/forward-ha-heating-json-to-mqtt.sh
3. Ensure the worker also catches:
   - Hook HA Heating
   - Hook HA Heating Bridge
4. Preserve request_id and run_id
5. Forward context, diagnostics, and input_summary when present
6. Restart the worker
7. Test with a fresh valid HA Heating Bridge decision
8. Confirm the new request_id appears on MQTT and in the Home Assistant sensor

Decision schema expected by MQTT stage:
{
  "request_id": "...",
  "run_id": "...",
  "factor": 1.0,
  "confidence": 88,
  "reason": "...",
  "global": {
    "mode": "normal",
    "boost": false
  },
  "rooms": []
}

Success criteria:
- A new HA Heating Bridge decision appears
- It is automatically forwarded to MQTT
- The request_id appears in Home Assistant sensor.ai_varme_openclaw_decision
- No manual test-forwarding is required
```


## Required runtime forwarding layer

A successful webhook call is not enough on its own.
A healthy OpenClaw heating setup must also have a worker or routing layer that forwards finished decision JSON to MQTT.

That means the real working chain is:

```text
HA webhook input
-> OpenClaw run
-> finished decision JSON in run or session output
-> openclaw-ha-completion-worker.py
-> forward-ha-heating-json-to-mqtt.sh
-> openclaw-ha-hook-forwarder.py
-> publish-heating-decision.js
-> MQTT
```

If the model can generate valid JSON but MQTT never updates, the missing piece is usually this worker or forwarder layer.

## What must be validated before forwarding

Before a result is sent to MQTT, validate that it is a real heating decision and not just a schema-only fallback.

Minimum checks:

- `factor` exists and is numeric
- `confidence` exists and is numeric
- `reason` exists and is a string
- `global` is an object
- `rooms` is an array

If output validation fails:

- log the root cause clearly
- do not forward the payload to MQTT

## Worker and path mapping

Verify that the worker and forwarder scripts point to the real workspace path used by that OpenClaw instance.

Example path variants:

- `/root/.openclaw/workspace/scripts/...`
- `/Volumes/appdata/openclaw/config/workspace/scripts/...`

Do not assume one path layout.
If the worker runs in a different runtime root than the stored workspace, a forwarding script can silently fail even when manual tests succeed.

## Worker start and verification

After wiring the forwarding layer, make sure the completion worker is actually running.

Typical checks:

```bash
ps | grep openclaw-ha-completion-worker.py
```

If needed, restart it using your local runtime method.

The important verification is not just HTTP 200 from the hook.
The important verification is:

1. a new hook request creates a run
2. a finished decision JSON appears in run or session output
3. the worker sees it
4. the forwarder publishes it to MQTT
5. Home Assistant receives the new `request_id`

## Troubleshooting note

If OpenClaw returns something like:

- `global: null`
- `rooms: {}`
- `reason: payload only specified output schema and provided no heating telemetry`

then the webhook runtime is still losing the real heating context before the agent sees it.
That is not an MQTT issue.
That is an input-wrapping issue between the hook request and the agent runtime.

In that case, fix the runtime so the full heating payload is available to the agent as real input, not only as a text instruction about output schema.

## Home Assistant side expectation

Home Assistant should consume the finished MQTT decision from:

- topic: `homeassistant/ai_varme/openclaw/decision`
- sensor path: `sensor.ai_varme_openclaw_decision`

Typical useful decision fields are:

- `factor`
- `confidence`
- `reason`
- `global`
- `rooms`
- `context`
- `diagnostics`
- `input_summary`

## Security and release notes

- Do not publish real MQTT passwords or API tokens.
- Use environment variables for secrets.
- Replace local IPs and private hostnames with neutral defaults in public docs.
- Keep the public repo integration-only.
