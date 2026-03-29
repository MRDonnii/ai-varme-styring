# AI Varme Styring

AI Varme Styring is a custom Home Assistant integration for deterministic room-first heating control.
It is designed for mixed systems with heat pumps and radiators, and it keeps room comfort as the primary objective while still optimizing energy source choices.

Release history is maintained in CHANGELOG.md.

## Project note

This project is primarily built and validated on my own Home Assistant installation.
It can be reused in other setups, but you should expect environment-specific tuning.

## What the integration does

- Controls each room independently with room-level target ownership.
- Supports hybrid rooms with both heat pump and radiator.
- Supports radiator-only rooms without forcing global setback behavior.
- Uses price-aware source selection between electricity and alternative heat source.
- Adds optional AI factor and reporting (Ollama or Gemini).
- Includes optional runtime features such as Presence Eco and PID layer.
- Exposes runtime controls and diagnostics as entities for dashboards and tuning.

## Core control model

- Room-first targeting:
  - The room AI target is authoritative for room decisions.
  - Global values are not allowed to unintentionally override room comfort.
- Hybrid handover:
  - During source handover scenarios, radiator behavior follows room intent.
  - Sustained deficit assist can increase radiator support for prolonged deficits.
- Fallback behavior:
  - If legacy helpers are missing, runtime target overrides keep control stable.
  - Sensor and helper resolution is defensive to avoid hard failures.

## Price and source selection

- If available, COP and boiler-aware heat-price sensors are prioritized.
- Internal fallback calculations are used when external price sensors are missing.
- Source switching is designed for stable comfort during changing prices and demand.

## AI and reporting

- AI provider options:
  - Ollama
  - Gemini
- AI is used as a decision modifier, not as uncontrolled authority.
- Reporting stays room-focused and avoids reintroducing global-side effects.
- Runtime-adjustable AI decision interval and AI report interval are exposed as number entities.
- Includes long-horizon summary reporting sensors:
  - `sensor.ai_varme_styring_garsdag_rapport`
  - `sensor.ai_varme_styring_7_dage_rapport`
- Persists rolling analytics samples for daily and weekly operational summaries.
- Report metadata includes active AI intervals and the last report model used.

## Runtime features

- Presence Eco with away and return timing windows.
- Optional PID layer for smoothing and precision.
- Learning mode for adaptive behavior over time.
- Per-room opening timing controls:
  - Pause after opening (minutes)
  - Resume after closing (minutes)

## Entities created by the integration

- Switches:
  - Active control
  - AI room control all rooms (main device)
  - Presence eco active
  - PID layer active
  - Learning mode active
- Number entities:
  - Global target and eco target
  - AI decision interval and AI report interval
  - Presence timing values
  - PID tuning values
  - Per-room temperature calibration values
  - Confidence threshold and revert timeout
  - Per-room timing and boost controls
- Buttons:
  - Run AI review now
  - Run AI report now
  - Apply room boost now
- Sensors:
  - AI status
  - Cheapest heat source
  - Largest deficit
  - PID layer status
  - AI report
  - Yesterday summary report
  - 7-day summary report
  - Analysis sensors such as cold rooms, focus room, and house level

## Setup

1. Install as a custom component in Home Assistant.
2. Add the integration from Devices and Services.
3. Select AI provider and global sensors.
4. Add rooms that should be controlled.
5. Validate switch states and room sensors.
6. Tune runtime numbers for your house.

## Migration and standalone mode

This integration is designed to run standalone without legacy automation control loops.
For migration steps, see MIGRATION_STANDALONE.md.

## Dashboard and operations

- Put status, report, and key runtime controls on one operations view.
- Keep per-room controls visible for quick troubleshooting.
- Use AI status and analysis sensors to detect migration conflicts or sensor issues.
- Use daily and weekly summary sensors to validate source-priority behavior over time.
- Track mode distribution (`AC`, `Gas`, `Mix`, `Klar`) and average source prices to evaluate cost impact.
- Use per-room calibration numbers and report metadata to validate room sensor quality and AI cadence behavior.

## Current status

Current documented release: v0.1.11.
See CHANGELOG.md for full release details.

## Brand assets

- Integration icon: `icon.svg`
- Integration logo: `logo.svg`

## Release process note

README should be updated on every release together with CHANGELOG so GitHub always reflects:
- What changed
- Why it changed
- Which user-facing features and controls are available
