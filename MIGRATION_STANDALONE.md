# Migration to standalone integration mode (without legacy layer)

Goal: remove old heat pump / AI helpers and run only through `AI Varme Styring`.

## 1) Enable the integration as the only control engine

- Ensure the integration is configured with all rooms and devices.
- Verify these switches exist and have the expected states:
  - `switch.*_enabled` (Active control)
  - `switch.*_presence_eco_enabled`
  - `switch.*_pid_enabled`
  - `switch.*_learning_enabled`

## 2) Disable legacy heating automations

Disable all automations with these `id` values:

- `varmepumpe_prioritet_kontinuerlig_vurdering`
- `varmepumpe_prioritet_stue_massiv_overvarme_sluk`
- `varmepumpe_prioritet_kokken_massiv_overvarme_sluk`
- `varmepumpe_prioritet_garage_massiv_overvarme_sluk`
- `garage_varmepumpe_prioritet_setpoint_stabil`
- `varmepumpe_ollama_generate_report`
- `varmepumpe_ollama_manual_trigger`
- `varmepumpe_ai_setpoint_change_trigger_run`
- `varmepumpe_ollama_daily_report`
- `varmepumpe_ollama_sync_helpers`
- `varmepumpe_ollama_sync_live_tuning_json`
- `varmepumpe_ollama_auto_tuning_apply`
- `varmepumpe_ai_varme_sync_prioritet_to_ollama`
- `varmepumpe_ai_varme_sync_ollama_to_prioritet`
- `varmepumpe_ollama_health_check`
- `varmepumpe_sensor_validation`
- `varmepumpe_prioritet_evaluering_watchdog`
- `varmepumpe_ollama_handler_styre_temp`
- `varmepumpe_ollama_confidence_extraction`
- `varmepumpe_ollama_learning_feedback_loop`
- `varmepumpe_ollama_handler_revert_logic`
- `varmepumpe_ai_setpoint_snapshot_init`
- `varmepumpe_ai_setpoint_snapshot_update_from_user`
- `varmepumpe_ai_setpoint_restore_authoritative`
- `garage_ai_presence_eco_enter`
- `garage_ai_presence_eco_exit_on_presence`
- `garage_ai_presence_eco_exit_when_ai_off`
- `garage_ai_presence_eco_hard_floor_guard`
- `garage_ai_presence_eco_user_override_release`
- `garage_ai_presence_eco_heat_failsafe`
- `garage_radiator_sync_under_ai_priority`
- `varmepumpe_pid_layer_garage_update`
- `varmepumpe_pid_layer_garage_reset`
- `varmepumpe_ai_handler_watchdog`
- `varmepumpe_ollama_analysis_15min`

## 3) Use the integration conflict sensor

- If `AI Status` shows `Conflict with legacy automations`, at least one old automation is still active.
- Check the `legacy_conflicts` attribute on the status sensor for the exact list.

## 4) Remove old helpers only after stable operation

Wait at least 2-3 days of stable operation before deleting old helpers:

- `input_boolean.varmepumpe_*`
- `input_number.varmepumpe_*`
- `input_text.varmepumpe_*`
- `input_select.varmepumpe_*`
- `input_*garage_ai_*`

## 5) Rollback

If anything behaves incorrectly:

- Re-enable relevant legacy automations.
- Turn off the integration's `Active control` switch.
