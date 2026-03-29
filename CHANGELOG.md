# Changelog

Alle væsentlige ændringer i integrationen bliver samlet her.

## v0.1.3

Dato: 2026-03-29

### Tilføjet
- Ny `button` platform med manuelle triggere:
  - Kør AI-gennemgang nu
  - Kør AI-rapport nu
  - Rum-boost nu
- Per-rum runtime mål-overstyring i motoren, så AI-mål kan styres stabilt selv hvis gammel helper er utilgængelig.
- Per-rum justering af åbningstider i runtime:
  - Pause efter åbning (minutter før AC pause)
  - Genstart efter lukning (minutter før AC genoptag)

### Forbedret
- Prislogik for varmekildevalg:
  - Prioriterer nu eksisterende varmeprissensorer (`sensor.varmepris_varmepumpe`, `sensor.varmepris_gasfyr`) når de findes.
  - Fallback til intern beregning ved manglende sensorer.
- Varmepumpe-start ved underskud er gjort mere robust:
  - Lav AI-konfidens blokerer ikke længere basal varmelevering.
  - AI dæmper aggressivitet i stedet for at stoppe nødvendig opvarmning.
- Eco-flow i rum:
  - Eco overskriver ikke længere brugerens AI-mål-helper.
  - Bedre og mere forudsigelig tilbagevenden fra eco-tilstand.
- Rapportflow:
  - Stabiliseret tekstnormalisering for mere læsbare danske rapporter.
  - Forbedret kompatibilitet mellem nye/legacy rapport-attributter.
- Bedre robusthed ved helper/navne-mismatch:
  - Motoren forsøger at resolve gyldig target-helper ud fra rum-navn og kendte mønstre.

### Stabilitet og migration
- Flere gamle legacy-konflikter håndteres bedre ved migration til standalone integration.
- Forbedret kompatibilitet med eksisterende dashboards og rumkort.

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
