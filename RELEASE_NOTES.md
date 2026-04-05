Release v0.3.8 - Report metadata and field hydration

This release makes the AI report sensor much more robust for dashboards and release display.

Included changes:
- The report sensor now exposes the current integration version and current changelog section as structured release metadata.
- Report fields such as cheapest heat source, flow-limited, diagnostics, and room decisions now derive from structured decision/context data with sensible fallbacks.
- Added backward-compatible attribute aliases so older dashboard cards can keep rendering the same facts while newer cards can use the cleaner keys.
- Cleaned remaining mojibake-prone report labels so Danish text stays stable.
