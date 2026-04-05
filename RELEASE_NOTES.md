Release v0.3.4 - Room occupancy stale-state fix

This hotfix resolves a stale occupancy fallback issue in AI Varme Styring.

Included changes:
- Rooms without configured occupancy sensors no longer reuse an old `last_occupancy_active` value.
- Occupancy fallback is now only used when occupancy sensors are configured but temporarily unavailable.
- Removing a presence sensor from a room now clears the old occupancy signal instead of keeping stale occupied or unoccupied state in runtime.
