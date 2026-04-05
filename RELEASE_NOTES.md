Release v0.3.11 - Full helper self-heal for room control

This release hardens setup and runtime so required room target helpers are repaired automatically.

Included changes:
- Room setup and room options now always ensure `room_target_number`, even without selected area.
- Missing room target helpers are resolved from existing `input_number` entities when possible.
- If no match exists and Home Assistant supports `input_number.create`, helpers are created automatically.
- Coordinator now performs periodic runtime self-heal and persists repaired helper links to options.
- Runtime helper repair events are logged to `openclaw_services_ensure.log` for easier diagnostics.
