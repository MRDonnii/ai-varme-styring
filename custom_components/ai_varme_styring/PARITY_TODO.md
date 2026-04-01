# Parity TODO vs existing HA heating control

Goal: reach 100% functional parity with current live behavior in `/haconfig`.

## Phase A (completed)

- [x] PID parameters configurable in the integration (Kp, Ki, Kd, deadband, integral limit, max offset)
- [x] Runtime switch for Learning mode
- [x] Report interval actively used by the engine
- [x] Report model actively used for extended AI reports
- [x] Sensor validation and outlier flags in engine status

## Phase B (completed)

- [x] Setpoint snapshot + authoritative restore (lock flow)
- [x] Learning feedback loop that tunes thresholds like existing automations
- [x] Revert logic with timeout and confidence gate
- [x] Sensor health checks and watchdog auto-recover flow

## Phase C (completed)

- [x] Full garage presence eco 1:1 behavior (including hard floor, min switch, user override release)
- [x] Garage radiator sync 1:1 under AI priority
- [x] Garage heat failsafe 1:1 when heat pump is OFF during eco
- [x] PID garage reset flow 1:1 on disable/off

## Phase D (in progress)

- [x] Port all relevant status and analysis sensors from templates
- [x] Port AI helper fields as integration entities (not legacy helpers)
- [ ] Final parity test against live operation scenario (living room/kitchen/garage)
