Release v0.3.14 - Cheap-power fan priority for heat pumps

New setting:
- `heat_pump_cheap_fan_mode`: off | auto | medium | high | max

Behavior:
- When electricity is cheap and heat pump priority is active, the integration raises fan mode on supported heat pumps.
- Outside cheap-power bias windows, it returns fan mode to auto (when fan feature is enabled and supported).
- Commands are sent only when needed, with cooldown to avoid command spam.
