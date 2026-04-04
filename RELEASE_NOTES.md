Release v0.3.1 - OpenClaw setup and auth fix

This release fixes the OpenClaw setup path for new installations and adds flexible OpenClaw authentication in the integration flow.

Included changes:
- Fixed OpenClaw config flow so `openclaw_url` is enough to pass validation when OpenClaw is selected as the primary engine.
- Added support for either `OpenClaw token` or `OpenClaw kode/password` in the integration UI and runtime.
- Kept token as the preferred path when both token and password are set.

Checks to perform before publishing:
- Confirm `manifest.json` version is `0.3.1`.
- Confirm `README.md` and `custom_components/ai_varme_styring/README.md` mention the new OpenClaw auth flow.
- Confirm no secrets, private IPs, or local paths leaked into the repo.
- Confirm Python compile succeeds for the updated integration files.
