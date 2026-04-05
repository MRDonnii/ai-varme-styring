Release v0.3.10 - Room target helper auto-ensure

This hotfix makes fresh installations and migrated setups more robust by ensuring room target helpers are linked and usable.

Included changes:
- The integration now validates room target helper links during setup.
- Missing helper links are repaired by resolving existing matching input_number entities.
- If no match exists and Home Assistant exposes `input_number.create`, a target helper is created automatically.
- Updated helper links are persisted to config entry options to survive restart.
