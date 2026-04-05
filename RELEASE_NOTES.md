Release v0.3.6 - Occupancy removed from all AI payload variants

This hotfix removes the last remaining occupancy fields from AI and report payload variants.

Included changes:
- Removed `occupancy_active` from the main AI payload room list.
- Removed `occupancy_active` from the report payload room list.
- Together with v0.3.5, occupancy should no longer leak into AI reasons outside ECO mode.
