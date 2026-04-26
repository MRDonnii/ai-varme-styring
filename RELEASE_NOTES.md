Release v0.3.28 - Warm-room linked-demand guard

What is fixed:
- Linked-room heat demand can no longer wake a heat pump when the heat-pump room itself is already at or above target.
- Fallback control now turns warm heat-pump rooms off and marks them as off_warm_room.
- Cheap-heat coasting now lowers the heat-pump setpoint before OFF instead of keeping a warm room active at target.
- This prevents Køkken/Stue-style short runs when nearby rooms only have small demand but the pump room is already warm.
