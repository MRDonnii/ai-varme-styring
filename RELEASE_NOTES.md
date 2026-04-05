Release v0.3.3 - Presence limited to ECO mode

This release tightens the heating logic so presence and occupancy only affect ECO behavior.

Included changes:
- Room occupancy is no longer used as a normal heating-demand signal in OpenClaw room decisions.
- Room priority is no longer raised just because a room is occupied.
- Comfort reasoning outside ECO mode no longer depends on occupancy.
- This prevents misleading AI reasons such as a room being slightly under target but dismissed only because it is not occupied.
