Release v0.3.29 - Heat-pump anti-cycling

What is fixed:
- Warm-room stop decisions now coast at a lower setpoint before full OFF.
- Normal overshoot must stay stable through a proven coast period before the pump is allowed to shut down.
- Fallback warm-room handling now lowers output first instead of immediately turning a running pump off.
- AI damping now modulates down before OFF to reduce heat-pump beeps and short cycling.
