# Changelog

Alle væsentlige ændringer i integrationen bliver samlet her.

## v0.1.2

Dato: 2026-03-28

### Tilføjet
- Runtime-toggle entiteter med persistens:
  - Aktiv styring
  - Presence-Eco aktiv
  - PID-lag aktiv
  - Learning mode aktiv
- Nye runtime-justerbare `number`-entiteter:
  - Presence away/return minutter
  - PID Kp/Ki/Kd, deadband, integral-grænse, max offset
  - AI confidence threshold
  - AI revert timeout
- Nye analysesensorer:
  - PID-lag status
  - Kolde rum
  - Radiatorhjælp rum
  - Fokusrum
  - Husniveau

### Forbedret
- Setup-stabilitet i `__init__.py` (runtime store initialiseres før første refresh).
- Setpoint lock/snapshot + autoritativ restore-flow.
- Confidence-gate og revert-timeout i AI beslutningsflow.
- Watchdog/sensor health-check flow.
- Learning-loop for adaptive rum-offsets.
- AI rapportflow bruger nu model + rapportinterval aktivt.
- Legacy-konfliktdetektion mod kendte gamle automation-ID'er.

### Garage-specifik parity
- Presence-eco enter/exit restore-flow.
- Hard-floor radiator guard.
- Heat failsafe når eco er aktiv og varmepumpe ikke leverer varme.
- PID reset-flow ved disable/off.

### Dokumentation
- `PARITY_TODO.md` opdateret med gennemførte faser.
- `MIGRATION_STANDALONE.md` udbygget til standalone-migrering.

