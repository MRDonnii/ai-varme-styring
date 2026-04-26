# AI Varme Styring

![AI Varme Styring logo](logo.png)

Local Home Assistant integration for AI-based heating control with OpenClaw Conversation, price-aware room decisions, and room-aware comfort control.

**Current version: 0.3.27**

## Highlights

- OpenClaw Conversation-based heating decisions with machine-readable JSON output
- Price-aware AI decisions that can lean toward the cheapest heat source
- Stabilized room overrides to reduce unnecessary heat-pump beeps and flip-flopping
- Heat-pump phase control that holds comfort before stopping, instead of short cycling
- District heating price support for fjernvarme/gas transition setups
- Fixed AI setpoint ownership: your room target stays the main target
- Optional Comfort Mode that adjusts internal behavior without rewriting your target
- Richer decision reporting with timestamp, reason, diagnostics, and room actions
- Dashboard-friendly sensors for room status, AI status, and decision context

## What is new in v0.3.27

### Heat-pump start protection and economy validation

- Heat pumps stay off when their own room is already above target, even if electricity is cheap.
- Linked-room demand can still start a pump when the pump room is not clearly warm.
- AI report attributes now show heat-pump start reasons, economy strategy, validation warnings, strategy warnings, gas use, heat-pump electricity use, and validated savings.
- Savings are only marked as validated when the measurement basis and strategy state are clean.
- Gas and fjernvarme are both kept in the economy model, so the integration can compare them during the transition.

## What was new in v0.3.26

### Public package cleanup

- Runtime fallback paths now use generic Home Assistant `/config` defaults instead of installation-specific host paths.
- Release scope was rescanned for private paths, hostnames, LAN IPs, room names, and token patterns.

## What was new in v0.3.25

### Generic ECO and heat-pump guard

- Rooms with room-level ECO enabled now stop the heat pump when there is no presence and the room is already over target.
- OpenClaw `eco` room directives now activate ECO immediately for empty rooms instead of waiting for the normal away timer.
- When the heat pump is cheapest and the room is under the active target, it starts even if AI recently suggested a softer mode.
- Qlima heat pumps are started with `set_temperature` plus `hvac_mode: heat`, because some devices ignore a standalone mode call.
- Heat-pump rooms use responsive default start thresholds generically, independent of room name.

## What was new in v0.3.24

### Generic ECO and heat-pump guard

- Rooms with room-level ECO enabled stop the heat pump when there is no presence and the room is already over target.
- OpenClaw `eco` room directives activate ECO immediately for empty rooms instead of waiting for the normal away timer.
- When the heat pump is cheapest and the room is under the active target, it starts even if AI recently suggested a softer mode.
- Qlima heat pumps are started with `set_temperature` plus `hvac_mode: heat`, because some devices ignore a standalone mode call.

## What was new in v0.3.23

### 1. Heat pumps now use phase-based comfort control

- Heat-pump rooms now expose the active phase, such as `warmup`, `hold`, `coast`, and `off_locked`.
- Stop decisions wait for a stronger comfort signal, so the pump is less likely to turn off immediately after the room has only just started recovering.
- Command cooldown and hold logic reduce repeated beeps, rapid target changes, and unnecessary on/off cycles.

### 2. Better room diagnostics for dashboards

- Room diagnostics now include clearer lines for deficit, surplus, opening pause, linked-room demand, and heat-pump phase.
- Command diagnostics are exposed for recent heat-pump actions so dashboards can show why the controller sent or held back a command.
- Danish room slugs now handle `æ`, `ø`, and `å` correctly, preventing duplicate entities like `ka_kken`.

### 3. Fjernvarme-ready price inputs

- District heating price and consumption sensors are handled alongside electricity and gas.
- This keeps AI Varme ready for homes moving from gas to fjernvarme while preserving the same price-aware decision model.

## What was new in v0.3.22

### 1. OpenClaw Conversation is now the primary path

- AI Varme Styring can now use the `openclaw_conversation` integration directly as its OpenClaw decision engine.
- The normal heating decision path no longer relies on MQTT delivery or a separate bridge service.
- Decision source and transport are visible in the AI report so you can verify that the live decision came from OpenClaw Conversation.

### 2. Cost-aware payloads are now sent to OpenClaw

- OpenClaw now receives richer price and runtime context, including:
  - `cheapest_heat_source`
  - `cheapest_alt_name`
  - `cheapest_alt_price`
  - `heat_pump_cheaper`
  - `estimated_savings_per_kwh`
  - daily and monthly savings estimates

This makes the AI decision more useful when the real goal is to save money without sacrificing comfort.

### 3. Better reports in Home Assistant

- The AI report is now easier to read and structured into sections such as:
  - `Kort resume`
  - `Aktiv beslutning`
  - `Hvorfor blev den taget?`
  - `Kontekst`
  - `Diagnostik`
  - `Rum-beslutninger`

- Danish text and room names are cleaned more aggressively so mojibake does not leak into dashboard cards.

### 4. More stable control behavior

- Small AI target adjustments are now held back unless they are actually urgent.
- Tiny target changes are ignored.
- Non-urgent mode flips are delayed.

This reduces repeated commands and helps avoid unnecessary beeps from heat pumps.

## Recommended setup

1. Install **AI Varme Styring**
2. Install and configure **OpenClaw Conversation**
3. Select OpenClaw as the AI decision engine in AI Varme Styring
4. Trigger an AI review and confirm the report shows:
   - `Beslutningsmotor: OpenClaw`
   - `AI-kilde nu: OpenClaw conversation`

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

## OpenClaw setup

For the conversation-based setup, use the `openclaw_conversation` integration in Home Assistant.

Legacy MQTT setup notes are still kept here for older installs:

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
- [`OPENCLAW_MQTT_SETUP.md`](OPENCLAW_MQTT_SETUP.md)
