# Changelog

All significant changes to the integration are documented here.

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
