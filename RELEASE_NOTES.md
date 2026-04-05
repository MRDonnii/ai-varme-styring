Release v0.3.9 - Garage heat-start responsiveness

This hotfix makes Garage react sooner when it is slightly below target.

Included changes:
- Garage rooms now use lower default heat-pump start thresholds so small deficits like 21.8 to 22.0 are not held back by the old 0.4?C defaults.
- Existing installations that still carry the old default garage thresholds are migrated automatically at runtime.
- The room editor now shows the lower garage defaults for new or edited garage rooms.
