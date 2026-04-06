Release v0.3.13 - Adjustable cheap-power heat pump priority

New feature:
- Added `heat_pump_cheap_priority_factor` (0.5-2.5, default 1.0).

Behavior when electricity is cheap and price awareness is enabled:
- Heat pumps start earlier (lower start thresholds).
- Heat pumps react faster after switch events (lower quick-start threshold).
- Heat pumps stay in heat/coast longer before stopping (higher stop threshold).
- Radiator targets are set further below room target in heat-pump rooms to shift more load to AC.

The active factor is now included in status/runtime payloads for diagnostics.
