# Changelog

All significant changes to the integration are documented here.

## v0.2.1

Date: 2026-04-01

### Fixed
- **Heat pump command spam / anti-beep** (Qlima and other units):
  - The integration no longer sends repeated `set_temperature` or `set_hvac_mode` commands every minute when nothing has actually changed.
  - Commands are now skipped if the current climate state already matches the target.
  - Pending and recently-sent commandsare tracked within the cycle to avoid redundant calls.
- **Qlima whole-degree setpoint handling**:
  - Qlima heat pumps now receive whole-degree targets only (rounded to nearest integer).
  - Sub-degree fluctuations no longer cause unnecessary beeps or repeated IR blasts.
- **Coast instead of OFF** in normal stabilization:
  - Heat pumps now prefer staying in low-heat/coast mode rather than being turned fully OFF when near target.
  - OFF is now reserved for explicit pause, door-open, major overheat, or AI-directed off commands.
  - Avoids unnecessary compressor cycling and audible state changes.
- **Correct start threshold respected**:
  - Heat pumps now correctly use the configured `start_deficit_c` threshold before activating.
  - Units no longer react aggressively to very small deficits that are within normal measurement noise.
- **asyncio startup/runtime fix**:
  - Fixed `Coordinator refresh failed: name 'asyncio' is not defined` error on startup/refresh.
  - `asyncio` is now correctly imported at the top of `coordinator.py`.

### Note
- **Reduced conflicts with legacy AC automations** (HA-config side):
  - Legacy direct AC automations in `automations.yaml` have been conditioned to only activate when AI heating control is explicitly disabled.
  - This is a Home Assistant config change, not an integration code change. Existing installations should review their local automations if they experience control conflicts.

## v0.2.0

Date: 2026-04-01

### Added
- **OpenClaw model selection** in options flow:
  - `Foretrukken OpenClaw-model` (default: `gpt-5-mini`)
  - `Fallback OpenClaw-model` (default: `gpt-4.1`)
  - Selected models must be activated in the user's OpenClaw instance.
  - The integration sends model hints to OpenClaw; actual routing is handled by OpenClaw.
- **Per-room humidity sensor** configuration:
  - Each room can now have a dedicated humidity sensor.
  - Humidity is factored into per-room comfort gap evaluation.
- **Humidity-aware comfort analysis**:
  - Effective comfort gap now accounts for relative humidity.
  - Dry or humid air can influence AI recommendations without simply forcing more heat.

### Improved
- **Options flow restructured** into clearer sections:
  - General settings
  - AI providers (cleaner, focused on engine and model selection)
  - Advanced control (technical OpenClaw settings moved here)
- **Room-by-room AI reasoning** improved:
  - AI is given explicit effective comfort gap per room.
  - Reduces self-contradictory reasoning about room state.
  - More accurate room-level override decisions.
- **Report structure** improved:
  - Clearer sections: Kort resume / Rum / Punkter.
  - Reduced duplicate content across sections.
  - Better OpenClaw model and source visibility in report and resume.
  - Footer now shows latest run time consistently.
- **Price/heat-source wording** improved:
  - Better distinction between cheapest heat choice and cheapest alternative to heat pump.
  - Reduced misleading gas vs. heat pump comparisons.

### Fixed
- **Cold-start behavior** after HA restart:
  - Room data is now available sooner.
  - Reduced cases where startup returned empty room data to AI.
- Fixed several runtime errors introduced during earlier refactors.

### Stability
- **Recorder-safe sensor trimming**:
  - Heavy attributes trimmed on `AI Status` and `AI indikator` sensors.
  - Avoids Recorder 16 KB attribute size warnings.
- **Watchman noise reduction**:
  - Archive and backup folders ignored in Watchman config.
  - Reduces false positives from historical files.



Date: 2026-03-29

### Fixed
- Stabilized Presence Eco behavior so ECO mode remains strictly room presence-sensor driven.
- When all room presence sensors are unavailable/unknown, occupancy now falls back to last known state instead of triggering false ECO transitions.

### Added
- Added room presence debug attributes on room status sensor:
  - `presence_fallback_aktiv`
  - `presence_sidst_skiftet`
  - `presence_sensorer_utilgaengelige`

## v0.1.11

Date: 2026-03-29

### Fixed
- Fixed integration version metadata mismatch:
  - `manifest.json` now correctly reports `0.1.11`.
- Fixed HA icon compatibility in integration metadata:
  - Updated manifest icon to `mdi:thermostat` to avoid "Icon not available" in clients that reject unsupported icon identifiers.

### Compatibility
- Keeps `icon.png` and `logo.png` branding assets for HA/HACS clients requiring PNG assets.

## v0.1.9

Date: 2026-03-29

### Added
- Added new main-device switch:
  - `switch.ai_varme_styring_ai_rumstyring_alle_rum`
  - Toggles AI room control on/off for all configured rooms in one action.
- Added integration brand assets:
  - `icon.svg`
  - `logo.svg`

### Fixed
- Fixed monthly savings compatibility behavior:
  - `sensor.ai_varme_besparelse_maaned` now falls back to daily savings scaling when the direct monthly source is zero/missing.
  - Prevents monthly dashboard cards from showing empty/flat output while daily savings is present.

### Changed
- Removed temporary package-level all-room helper approach in favor of integration-native control in the AI main device.

## v0.1.8

Date: 2026-03-29

### Fixed
- Fixed presence-eco timing continuity in room control:
  - Room occupancy timestamps are now tracked continuously, even when eco mode is disabled.
  - Enabling eco while a room is already empty now uses the real empty-since timestamp instead of restarting the timer.
  - This makes eco activation behave immediately and predictably after manual toggles.

## v0.1.7

Date: 2026-03-29

### Added
- Added runtime-adjustable AI cadence controls:
  - decision interval
  - report interval
- Added per-room temperature calibration numbers for room sensor correction.
- Added report metadata attributes for active AI intervals and last report model used.

### Changed
- Automatic AI report generation now uses the fast model by default.
- Full report model is now reserved for manual full-report runs.
- Raised default automatic report cadence to reduce unnecessary Ollama load.
- Tightened Tesla charge-plan AI automation so it only reacts to real scheduled charging states instead of frequent price churn.

### Fixed
- Fixed room sensor resolution so room status entities no longer stay stuck in `Ukendt` when room data is present.
- Fixed AC control behavior so room deficit reacts from the room sensor instead of relying on misleading internal heat-pump temperature.
- Fixed AC command spam with stricter debounce/cooldown and whole-step setpoint behavior.
- Fixed savings/report fallbacks so missing price data no longer collapses into empty state as easily.
- Fixed startup behavior so room data is available sooner and AI/report work does not block initial integration load.

### Cleanup
- Rewired watchdog and ops toolkit package helpers to the new `ai_varme_styring` entities.
- Replaced legacy AI varme references in the `Varme Center` dashboard with the new integration sensors/switches where direct replacements exist.
- Removed orphaned legacy `varmepumpe_prioritet`, `varmepumpe_ollama`, `varmepumpe_gemini`, `varmepumpe_handler`, and old PID entities from Home Assistant entity registry and restore-state storage.
- Removed orphaned legacy target-lock helpers and duplicate heat-price entities.

## v0.1.6

Date: 2026-03-29

### Added
- Added two new long-horizon report sensors:
  - `sensor.ai_varme_styring_garsdag_rapport`
  - `sensor.ai_varme_styring_7_dage_rapport`
- Added aggregated reporting payloads for:
  - runtime distribution by heating mode (`AC`, `Gas`, `Mix`, `Klar`)
  - average prices by source (electricity, gas, district heat)
  - source consumption and estimated cost (when corresponding sensors are available)

### Improved
- Added internal analytics sampling in the coordinator (rolling, persisted runtime samples) to support daily/weekly operational summaries.
- Improved observability for validating whether source-priority logic actually reduces gas usage over time.
- Improved dashboard integration options by exposing summary data through sensor attributes for card rendering.

## v0.1.5

Date: 2026-03-29

### Fixed
- Fixed radiator target behavior in AC rooms:
  - During thermostat takeover (gas cheaper), radiator target now follows the room AI target instead of being lowered.
- Fixed radiator fallback logic for rooms without heat pumps:
  - Radiators now follow room AI target directly (no unintended global setback to 20°C).
- Fixed long-running room comfort handling:
  - Added sustained-deficit assist rule so AC rooms can lift radiator support after prolonged deficit.
- Fixed report scope consistency:
  - AI report remains room-based and does not reintroduce global target text.

### Improved
- Improved comfort stability in mixed AC + radiator setups when energy source priority changes.
- Improved practical handover between heat-pump priority and radiator support under real-world demand.

## v0.1.4

Date: 2026-03-29

### Fixed
- Removed global target influence from the room control loop so all rooms no longer get pulled down to 20°C by a global eco state.
- Removed global target from AI report output and report builder input. Reporting now stays room-focused.
- Fixed per-room AI target control when legacy target helpers are unavailable by adding runtime target override support.
- Fixed heat source decision behavior so heat pump availability under deficit is no longer blocked by low AI confidence.
- Fixed price-comparison behavior by prioritizing existing COP/boiler-aware heat-price sensors when present.
- Fixed garage sensor mismatch by adding safe room sensor resolution and garage-specific preference for the base temperature sensor over `_2` variants.

### Improved
- Added per-room opening pause timing controls to runtime:
  - Pause after opening (minutes)
  - Resume after closing (minutes)
- Improved migration resilience for mixed legacy/new setups where old helpers, entities, or naming patterns still exist.
- Improved dashboard consistency by aligning room-level behavior with per-room AI target ownership.

## v0.1.3

Date: 2026-03-29

### Added
- New `button` platform with manual actions:
  - Run AI review now
  - Run AI report now
  - Apply room boost now
- Per-room runtime target override in the engine, keeping AI targets stable even when legacy helpers are unavailable.
- Per-room runtime opening timing controls:
  - Pause after opening (minutes before AC pause)
  - Resume after closing (minutes before AC restart)

### Improved
- Heat source price selection logic:
  - Now prioritizes existing heat-price sensors (`sensor.varmepris_varmepumpe`, `sensor.varmepris_gasfyr`) when available.
  - Falls back to internal price calculation if sensors are missing.
- More robust heat pump start behavior during deficit:
  - Low AI confidence no longer blocks baseline heating.
  - AI now dampens aggressiveness instead of preventing required heating.
- Room eco flow behavior:
  - Eco no longer overwrites user-controlled AI target helpers.
  - More predictable return from eco mode.
- Reporting flow:
  - Improved text normalization for clearer reports.
  - Better compatibility between new and legacy report attributes.
- Better helper/name mismatch resilience:
  - The engine now resolves a valid target helper using room name patterns and known helper naming conventions.

### Stability and migration
- Better handling of legacy conflicts during migration to standalone integration mode.
- Improved compatibility with existing dashboards and room cards.

## v0.1.2

Date: 2026-03-28

### Added
- Persistent runtime toggle entities:
  - Active control
  - Presence eco active
  - PID layer active
  - Learning mode active
- New runtime-adjustable `number` entities:
  - Presence away/return minutes
  - PID Kp/Ki/Kd, deadband, integral limit, max offset
  - AI confidence threshold
  - AI revert timeout
- New analysis sensors:
  - PID layer status
  - Cold rooms
  - Radiator assist rooms
  - Focus room
  - House level

### Improved
- Setup stability in `__init__.py` (runtime store initializes before first refresh).
- Setpoint lock/snapshot and authoritative restore flow.
- Confidence gate and revert timeout in AI decision flow.
- Watchdog/sensor health checks.
- Learning loop for adaptive room offsets.
- AI reporting now actively uses model and report interval settings.
- Legacy conflict detection for known old automation IDs.

### Garage-specific parity
- Presence-eco enter/exit restore-flow.
- Hard-floor radiator guard.
- Heat failsafe when eco is active and the heat pump is not delivering heat.
- PID reset flow on disable/off.

### Documentation
- `PARITY_TODO.md` updated with completed phases.
- `MIGRATION_STANDALONE.md` expanded for standalone migration.
