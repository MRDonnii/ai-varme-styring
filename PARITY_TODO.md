# Parity TODO mod eksisterende HA varmestyring

Mål: 100% funktionel parity med nuværende drift i `/haconfig`.

## Fase A (færdig i denne runde)

- [x] PID parametre gjort konfigurerbare i integrationen (Kp, Ki, Kd, deadband, integral-limit, max-offset)
- [x] Runtime switch til Learning mode
- [x] Report-interval bruges aktivt i motoren
- [x] Rapportmodel bruges aktivt til længere AI-rapport
- [x] Sensorvalidering/outlier-flag i motorstatus

## Fase B (næste)

- [x] Setpoint snapshot + autoritativ restore (lock-flow)
- [x] Learning-feedback loop der tuner tærskler som i nuværende automations
- [x] Revert-logik med timeout og confidence-gate
- [x] Sensor health-check og watchdog-autorecover flow

## Fase C (næste)

- [x] Garage presence-eco fuld 1:1 (inkl. hard-floor, min-switch, user override release)
- [x] Garage radiator-sync 1:1 under AI-prioritet
- [x] Garage heat failsafe 1:1 hvis varmepumpe er OFF under eco
- [x] PID garage reset-flow 1:1 ved disable/off

## Fase D (næste)

- [x] Port af alle relevante status-/analysesensorer fra templates
- [x] Port af AI helper-felter som entiteter i integrationen (ikke gamle helpers)
- [ ] Endelig parity-test mod aktiv driftsscenarie (stue/køkken/garage)
