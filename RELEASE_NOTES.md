Release v0.3.7 - Minimal AI payload hardening

This release makes AI payloads safer for sparse installations by sending only the data that actually exists.

Included changes:
- OpenClaw and provider payload builders now omit unknown optional fields instead of sending placeholder `0.0` values.
- Rooms without valid current and target temperatures are skipped from the strict OpenClaw heating payload.
- Weather forecast, supply and return temperatures, humidity, and similar optional telemetry are only sent when real data exists.
- This makes new installations more robust when only the minimum required sensors are configured.
