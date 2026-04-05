# AI Varme Styring

![AI Varme Styring logo](custom_components/ai_varme_styring/logo.png)

Home Assistant integration for AI-based heating control with OpenClaw, MQTT-backed decision delivery, and room-aware comfort control.

**Current version: 0.3.3**

## Highlights

- OpenClaw heating decisions with structured JSON output
- MQTT-backed decision delivery to Home Assistant
- Fixed room AI setpoint ownership
- Optional Comfort Mode
- Better decision reporting and diagnostics
- OpenClaw token or password-based authentication in the integration flow
- HACS-ready integration packaging

## Install with HACS

1. Open HACS in Home Assistant
2. Add `https://github.com/MRDonnii/ai-varme-styring` as a custom repository
3. Select type `Integration`
4. Install **AI Varme Styring**
5. Restart Home Assistant

## Documentation

- [`custom_components/ai_varme_styring/README.md`](custom_components/ai_varme_styring/README.md)
- [`custom_components/ai_varme_styring/CHANGELOG.md`](custom_components/ai_varme_styring/CHANGELOG.md)
- [`custom_components/ai_varme_styring/OPENCLAW_MQTT_SETUP.md`](custom_components/ai_varme_styring/OPENCLAW_MQTT_SETUP.md)
- [`custom_components/ai_varme_styring/RELEASE_GUIDE.md`](custom_components/ai_varme_styring/RELEASE_GUIDE.md)

## Repository scope

This repo must contain only the public integration package.
It must not contain local Home Assistant configuration, secrets, dashboards, or private runtime state.
