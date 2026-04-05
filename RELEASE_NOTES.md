Release v0.3.12 - Runtime migration hardening and helper matching

This patch addresses a reported runtime crash and improves helper auto-linking on mixed installations.

Included changes:
- Backfills missing room runtime keys during each control cycle.
- Fixes upgrade-state crash patterns such as KeyError `closed_since`.
- Target helper resolvers now support plain helper ids like `input_number.kokken`.
- Existing rooms can relink target helpers even when old naming conventions are used.
