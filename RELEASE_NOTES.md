Release v0.3.5 - Presence wording removed from AI decisions

This hotfix removes the remaining occupancy signals from AI decision payloads and prompt schema.

Included changes:
- Removed room occupancy fields from OpenClaw heating payloads.
- Removed occupancy from compact provider decision payloads.
- Removed `occupied_rooms` from the OpenClaw output schema prompt.
- AI reasons should no longer explain no-action with `not occupied` or `ikke beboet`.
