# Migration til ren integration (uden legacy lag)

Mål: du skal kunne fjerne gamle varmepumpe/AI-helpers og kun køre via `AI Varme Styring`.

## 1) Aktivér integrationen som eneste motor

- Sørg for at integrationen er sat op med alle rum og enheder.
- Tjek at disse switches findes og har korrekt status:
  - `switch.*_enabled` (Aktiv styring)
  - `switch.*_presence_eco_enabled`
  - `switch.*_pid_enabled`
  - `switch.*_learning_enabled`

## 2) Deaktiver legacy varmestyring-automations

Deaktiver alle automations med disse `id`:

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

## 3) Brug konflikt-sensoren i integrationen

- Hvis `AI Status` viser `Konflikt med legacy automations`, er mindst én gammel automation stadig aktiv.
- Se attributten `legacy_conflicts` på status-sensoren for præcis liste.

## 4) Fjern først gamle helpers når drift er stabil

Vent minimum 2-3 dage med stabil drift før du sletter gamle:

- `input_boolean.varmepumpe_*`
- `input_number.varmepumpe_*`
- `input_text.varmepumpe_*`
- `input_select.varmepumpe_*`
- `input_*garage_ai_*`

## 5) Rollback

Hvis noget driller:

- Aktivér relevante legacy-automations igen.
- Slå integrationens `Aktiv styring` fra.
