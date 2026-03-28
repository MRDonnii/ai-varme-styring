# Parity TODO mod eksisterende HA varmestyring

Mål: 100% funktionel parity med nuværende drift i `/haconfig`.

## Fase A (færdig i denne runde)

- [x] PID parametre gjort konfigurerbare i integrationen (Kp, Ki, Kd, deadband, integral-limit, max-offset)
- [x] Runtime switch til Learning mode
- [x] Report-interval bruges aktivt i motoren
- [x] Rapportmodel bruges aktivt til længere AI-rapport
- [x] Sensorvalidering/outlier-flag i motorstatus

## Fase B (næste)

- [ ] Setpoint snapshot + autoritativ restore (lock-flow)
- [ ] Learning-feedback loop der tuner tærskler som i nuværende automations
- [ ] Revert-logik med timeout og confidence-gate
- [ ] Sensor health-check og watchdog-autorecover flow

## Fase C (næste)

- [ ] Garage presence-eco fuld 1:1 (inkl. hard-floor, min-switch, user override release)
- [ ] Garage radiator-sync 1:1 under AI-prioritet
- [ ] Garage heat failsafe 1:1 hvis varmepumpe er OFF under eco
- [ ] PID garage reset-flow 1:1 ved disable/off

## Fase D (næste)

- [ ] Port af alle relevante status-/analysesensorer fra templates
- [ ] Port af AI helper-felter som entiteter i integrationen (ikke gamle helpers)
- [ ] Endelig parity-test mod aktiv driftsscenarie (stue/køkken/garage)
