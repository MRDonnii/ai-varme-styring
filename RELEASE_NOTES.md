Release v0.2.1 — Clean HACS release

This release prepares the integration for HACS by sanitizing internal host paths and adding branding assets.

Included changes:
- Sanitized internal /haconfig paths and added guidance to README.
- Added root hacs.json and integration custom_components/ai_varme_styring/hacs.json with content_in_root: false.
- Added logo.svg and logo_small.svg (and PNG fallback) for HACS display.
- Added sanitization_report.txt documenting the scan performed.

Notes for reviewers:
- Verify the custom_components/ai_varme_styring/manifest.json version matches the changelog (0.2.1).
- Confirm no sensitive files (secrets, .pem, .storage, internal host paths) are included in this branch.
- Confirm the README renders properly in GitHub and HACS.

Changelog: see custom_components/ai_varme_styring/CHANGELOG.md (v0.2.1).
