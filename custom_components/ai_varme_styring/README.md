# AI Varme Styring

![AI Varme Styring logo](logo.png)

Local Home Assistant integration for AI-based heating control with OpenClaw, MQTT-backed decision delivery, and room-aware comfort control.

**Current version: 0.3.3**

## Highlights

- OpenClaw-based heating decisions with machine-readable JSON output
- MQTT-backed decision delivery for stable Home Assistant adoption
- Fixed AI setpoint ownership: your room target stays the main target
- Optional Comfort Mode that adjusts internal behavior without rewriting your target
- Richer decision reporting with timestamp, reason, diagnostics, and room actions
- Dashboard-friendly sensors for room status, AI status, and decision context

## What is new in the upcoming release

### 1. MQTT-first OpenClaw decision path

The OpenClaw heating flow can now publish finished decisions to MQTT and let Home Assistant consume the structured result from:

- `homeassistant/ai_varme/openclaw/decision`

This makes the decision chain easier to observe and more robust than instruction-wrapper style hooks.

### 1b. OpenClaw auth and setup flow

The OpenClaw setup flow now accepts a normal webhook URL directly when OpenClaw is used as the primary engine.
You no longer have to hit a dead-end validation path that asked for hidden bridge or enable flags.

Authentication can now use either:

- `OpenClaw token`
- `OpenClaw kode/password`

If both are set, token is preferred.

### 1c. Hook payload compatibility

OpenClaw webhook requests now duplicate the heating payload as top-level fields and as nested `context`, `input`, and `heating_context` objects.
This makes new OpenClaw instances more robust when their runtime wrapper expects the heating telemetry in a specific location.

Malformed OpenClaw outputs are also rejected earlier if `global`, `rooms`, `diagnostics`, or `input_summary` come back in the wrong shape.

### 1d. Presence only for ECO mode

Presence and occupancy are now reserved for ECO behavior only.
They no longer bias OpenClaw room priority, comfort reasoning, or normal heating decisions outside ECO mode.

### 2. Fixed room target ownership

The room AI setpoint is now treated as the user-owned main target.
The runtime may optimize heat pump and radiator behavior around it, but it must not silently rewrite the helper target.

### 3. Comfort Mode

Comfort Mode is now a separate switchable behavior layer.

- When it is `off`, the room AI setpoint stays fixed and comfort bias is inactive.
- When it is `on`, humidity, occupancy, comfort gap, and opening state may slightly influence internal heating behavior.
- Comfort Mode does not overwrite the room target helper.

### 4. Better AI report quality

The AI report now exposes more of the real decision context:

- last decision time
- request and run identifiers
- decision reason
- diagnostics summary
- override reasoning
- comfort notes

## Installation with HACS

1. Open HACS in Home Assistant
2. Add `https://github.com/MRDonnii/ai-varme-styring` as a custom repository
3. Choose type `Integration`
4. Install **AI Varme Styring**
5. Restart Home Assistant

## Core decision schema

Finished OpenClaw heating decisions are expected to look like this:

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

## OpenClaw and MQTT setup

For the full OpenClaw setup guide, including the exact text block you can paste into OpenClaw-side tooling, see:

- [`OPENCLAW_MQTT_SETUP.md`](OPENCLAW_MQTT_SETUP.md)

## Important notes

- This public repository is integration-only.
- Local Home Assistant configuration, secrets, dashboards, and private runtime state do not belong in the public repo.
- MQTT credentials must come from environment variables or Home Assistant configuration, never hardcoded values.

## Files you will likely care about

- `manifest.json`
- `config_flow.py`
- `coordinator.py`
- `ai_client.py`
- `sensor.py`
- `number.py`
- `switch.py`
- `CHANGELOG.md`
- `OPENCLAW_MQTT_SETUP.md`

## Release docs

- [`CHANGELOG.md`](CHANGELOG.md)
- [`RELEASE_GUIDE.md`](RELEASE_GUIDE.md)
- [`OPENCLAW_MQTT_SETUP.md`](OPENCLAW_MQTT_SETUP.md)
