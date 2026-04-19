# AI Varme Styring

![AI Varme Styring logo](custom_components/ai_varme_styring/logo.png)

Home Assistant integration for AI-based heating control with OpenClaw Conversation, price-aware room decisions, and room-aware comfort control.

**Current version: 0.3.22**

## Highlights

- OpenClaw Conversation-based heating decisions with machine-readable JSON output
- Price-aware AI decisions that can lean toward the cheapest heat source
- Stabilized room overrides to reduce unnecessary heat-pump beeps and flip-flopping
- Fixed AI setpoint ownership so your room target stays the main target
- Better decision reporting and diagnostics in Home Assistant
- HACS-ready integration packaging

## Install with HACS

1. Open HACS in Home Assistant
2. Add `https://github.com/MRDonnii/ai-varme-styring` as a custom repository
3. Select type `Integration`
4. Install **AI Varme Styring**
5. Restart Home Assistant

## Recommended OpenClaw setup

For new installations, use **OpenClaw Conversation** inside Home Assistant and let AI Varme Styring call that conversation agent directly.

The AI report should show:
- `Beslutningsmotor: OpenClaw`
- `AI-kilde nu: OpenClaw conversation`

Legacy MQTT notes are still kept for older installations, but they are no longer the recommended path.

## Documentation

- [`custom_components/ai_varme_styring/README.md`](custom_components/ai_varme_styring/README.md)
- [`custom_components/ai_varme_styring/CHANGELOG.md`](custom_components/ai_varme_styring/CHANGELOG.md)
- [`custom_components/ai_varme_styring/OPENCLAW_MQTT_SETUP.md`](custom_components/ai_varme_styring/OPENCLAW_MQTT_SETUP.md)

## Repository scope

This repo contains only the public integration package.
It must not contain local Home Assistant configuration, secrets, dashboards, or private runtime state.