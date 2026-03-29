# Changelog

All significant changes to the integration are documented here.

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
