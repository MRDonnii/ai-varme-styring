# AI Varme Styring

`AI Varme Styring` is a custom Home Assistant integration for room-by-room heating control with price-aware logic, presence eco behavior, and an optional PID layer.
Release notes are documented in `CHANGELOG.md`.

## Note

This project is primarily built for my own Home Assistant installation.
There is no guarantee of ongoing development or broad compatibility across other setups.

## What it does

- Controls heating per room using dedicated sensors, setpoints, and devices.
- Supports both heat pump and radiator in the same room.
- Uses an AI provider for decision factor generation:
  - Ollama
  - Gemini
- Uses price-aware operation with electricity price and alternative heat source price (gas or district heating).
- Supports Presence Eco windows (away/return) to lower targets when the house is empty.
- Includes an optional PID layer on top of standard control, toggleable at runtime.
- Exposes status and reporting sensors for dashboards.

## Entities created by the integration

- Switches:
  - Active control
  - Presence eco active
  - PID layer active
  - Learning mode active
- Number entities:
  - Global AI target
  - Eco AI target
  - Presence and PID tuning values
  - Confidence threshold and revert timeout
- Sensors:
  - AI status
  - Cheapest heat source
  - Largest deficit
  - PID layer status
  - AI report
  - Analysis sensors (cold rooms, focus room, house level, etc.)

## Setup

1. Install the integration as a custom component.
2. Add the integration in Home Assistant.
3. Select AI provider and global sensors.
4. Add the rooms you want to control (only selected rooms are managed).
5. Fine-tune thresholds and enable Presence Eco and PID layer if needed.

## Status

Current repo release notes: `v0.1.3` (see `CHANGELOG.md`).

## Standalone migration

The integration is designed to run without legacy heat-pump automations.
See the migration guide:

- `MIGRATION_STANDALONE.md`
