Release v0.3.2 - OpenClaw hook payload compatibility

This release hardens the OpenClaw heating path for new instances that were accepting the webhook call but dropping the actual room telemetry in runtime.

Included changes:
- The integration now sends the heating payload as top-level fields and as nested `context`, `input`, and `heating_context` objects.
- Malformed OpenClaw outputs are rejected earlier when `global`, `rooms`, `diagnostics`, or `input_summary` are returned with the wrong shape.
- The direct session path now consistently supports password auth as well as token auth.
