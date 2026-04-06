# Changelog

All significant changes to the integration are documented here.

## v0.3.18

Date: 2026-04-06

### Changed
- `room_link_group` is now editable as a selectable field in room edit:
  - can choose existing room/group values
  - can clear it to remove link
  - can type a new group id directly
- Heat source direction slider is now room-first:
  - kept in room edit where day-to-day tuning happens
  - removed from the dedicated cheap-power settings section to avoid duplicate tuning locations

### Improved
- Room save flow now normalizes link-group values and keeps adjacent-room selections stable.

## v0.3.17

Date: 2026-04-06

### Added
- **Room-level heat source bias controls** under room edit:
  - `room_heat_source_direction_bias` (radiator (-) <-> varmepumpe (+))
  - `room_cheap_power_radiator_setback_extra_c` (extra radiator reduction)
- **Room adjacency selection** under room edit:
  - `room_adjacent_rooms` lets you choose connected rooms for shared-airflow strategy

### Changed
- Cheap-power control now uses room-level bias values when present.
- Adjacent rooms linked to heat-pump rooms can now get additional radiator reduction when cheap-power heat-pump bias is active.

## v0.3.16

Date: 2026-04-06

### Added
- **Direction slider for heat source strategy (radiator <-> heat pump)**:
  - new slider `heat_source_direction_bias` from `-2.0` to `+2.0`
  - negative values prioritize radiator support
  - positive values prioritize heat pump usage
- **Extra radiator reduction at cheap power**:
  - new setting `cheap_power_radiator_setback_extra_c` to lower radiator targets further when cheap-power heat-pump bias is active
- **Clear grouped setup** in `Billig strom: varmepumpe-prioritet` with explicit direction description

### Changed
- Cheap-power control now combines:
  - `heat_pump_cheap_priority_factor`
  - `heat_source_direction_bias`
  - `cheap_power_radiator_setback_extra_c`
  to tune start/stop behavior and radiator setback in one coherent strategy.

## v0.3.15

Date: 2026-04-06

### Added
- **Dedicated setup section for cheap-power heat-pump tuning**:
  - new options menu entry: `Billig strom: varmepumpe-prioritet`
  - groups key fields in one place:
    - `enable_price_awareness`
    - `price_margin`
    - `heat_pump_cheap_priority_factor`
    - `heat_pump_cheap_fan_mode`
    - `radiator_setback_c`
  - makes tuning easier without digging through generic advanced settings

## v0.3.14

Date: 2026-04-06

### Added
- **Cheap-power fan priority for heat pumps**:
  - new setting `heat_pump_cheap_fan_mode` with options: `off`, `auto`, `medium`, `high`, `max`
  - when cheap-power heat-pump bias is active, integration now requests higher fan mode on supported heat pumps
  - when cheap-power bias is not active and fan feature is enabled, integration falls back to `auto` when supported
  - fan-mode changes are throttled and only sent when mode actually changes

### Added
- **Cheap-power priority tuning from v0.3.13 is now combined with fan control** for stronger load shift toward heat pumps.

## v0.3.13

Date: 2026-04-06

### Added
- **Adjustable heat-pump priority when electricity is cheap**:
  - new setting `heat_pump_cheap_priority_factor` (0.5 to 2.5, default 1.0)
  - when price awareness is active and heat pump is the cheapest source, higher factor now:
    - lowers heat-pump start thresholds (starts earlier)
    - lowers quick-start anti-short-cycle threshold (reacts faster)
    - increases stop-surplus threshold (stays in heat/coast longer)
    - increases radiator setback in heat-pump rooms to shift more load to AC
  - current factor is exposed in runtime status payload as `heat_pump_cheap_priority_factor`

## v0.3.12

Date: 2026-04-05

### Fixed
- **Runtime stability for existing room state migrations**:
  - room runtime state now backfills missing control keys on each cycle
  - this prevents KeyError cases like `'closed_since'` on upgraded installations with older runtime state
- **More tolerant target-helper matching**:
  - helper resolvers now also accept plain `input_number.<room_slug>` entities
  - rooms with helpers like `input_number.kokken` can now auto-link without requiring `_target` naming

## v0.3.11

Date: 2026-04-05

### Fixed
- **Full room-target helper self-heal across setup, options and runtime**:
  - room forms now ensure a valid `room_target_number` even when no area is selected
  - options room add/edit now auto-resolve or auto-create the target helper the same way as first-time setup
  - coordinator now runs periodic runtime self-heal to relink missing room target helpers
  - when runtime repairs links, updated room helper mappings are persisted back to entry options automatically
  - helper self-heal writes operational trace rows to `openclaw_services_ensure.log` for troubleshooting

## v0.3.10

Date: 2026-04-05

### Fixed
- **Room target helpers are now ensured at setup**:
  - on startup the integration now validates each room target helper link
  - if a linked helper is missing, it first resolves existing matching input_number entities
  - if no match exists and `input_number.create` is available, it creates a helper automatically
  - resolved/created helper links are persisted back to entry options so room controls keep working after restart

## v0.3.9

Date: 2026-04-05

### Fixed
- **Garage heat-start responsiveness**:
  - garage rooms now use lower default heat-pump start thresholds so small deficits like 21.8 -> 22.0 are no longer ignored
  - existing installations that still carry the old default `0.4` garage thresholds are migrated at runtime to the new garage-specific defaults
  - the room editor now also shows the lower garage defaults for new or edited garage rooms

## v0.3.8

Date: 2026-04-05

### Fixed
- **AI report metadata and field hydration**:
  - the report sensor now exposes the current integration version and current changelog section as structured release fields
  - report fields such as cheapest heat source, flow-limited, diagnostics, and room decisions now fall back to structured decision/context data before showing empty placeholders
  - added backward-compatible report attribute aliases so existing dashboards can read the same facts without brittle key mismatches
  - cleaned remaining report-sensor mojibake-prone labels so Danish text stays stable in runtime

## v0.3.7

Date: 2026-04-05

### Changed
- **Minimal AI payload hardening**:
  - OpenClaw and provider payload builders now omit unknown optional fields instead of sending placeholder `0.0` values
  - rooms without valid current/target temperature are skipped from the strict OpenClaw heating payload
  - weather forecast, supply/return temperatures, humidity, and other optional telemetry are only sent when real data exists
  - this makes new installations more tolerant of sparse setups with only the minimum required sensors

## v0.3.6

Date: 2026-04-05

### Fixed
- **Occupancy still leaking into AI/report payloads**:
  - removed `occupancy_active` from the main AI payload room list
  - removed `occupancy_active` from the report payload room list
  - together with v0.3.5 this fully removes occupancy as an AI reasoning signal outside ECO mode

## v0.3.5

Date: 2026-04-05

### Fixed
- **Presence wording still leaking into AI reasons**:
  - removed room occupancy fields from OpenClaw heating payloads
  - removed occupancy from compact provider decision payloads
  - removed `occupied_rooms` from the OpenClaw output schema prompt
  - AI decisions should no longer justify no-action with phrases like `not occupied` or `ikke beboet`

## v0.3.4

Date: 2026-04-05

### Fixed
- **Stale room occupancy fallback**:
  - rooms without configured occupancy sensors no longer inherit an old `last_occupancy_active` value
  - occupancy fallback is now only used when sensors are configured but temporarily unavailable
  - removing a presence sensor from a room now clears the old occupancy signal instead of keeping the room marked as unoccupied or occupied

## v0.3.3

Date: 2026-04-05

### Changed
- **Presence only affects ECO mode**:
  - room occupancy is no longer sent as a real heating-demand signal to OpenClaw room decisions
  - room priority is no longer raised because a room is occupied
  - comfort bias outside ECO mode no longer depends on room occupancy

### Fixed
- **Misleading AI reasons about non-occupied rooms**:
  - small deficits are no longer dismissed just because a room is marked as not occupied
  - this prevents explanations like `not occupied, no heating needed now` from being caused by presence outside ECO mode

## v0.3.2

Date: 2026-04-04

### Fixed
- **OpenClaw hook payload compatibility**:
  - the integration now sends heating telemetry both as top-level fields and as nested `context`, `input`, and `heating_context` objects
  - this prevents OpenClaw runtimes from dropping room telemetry when their wrapper only reads one payload location
- **Malformed OpenClaw output handling**:
  - outputs with invalid `global`, `rooms`, `diagnostics`, or `input_summary` shapes are now rejected earlier instead of being treated as valid decisions
- **OpenClaw direct session auth path**:
  - the session-based OpenClaw call now consistently carries the password auth field as well as token auth

## v0.3.1

Date: 2026-04-04

### Fixed
- **OpenClaw config flow dead-end**:
  - OpenClaw can now be saved from the normal config flow when a valid `openclaw_url` is provided.
  - The validation no longer requires hidden or non-exposed `openclaw_enabled` / bridge flags to pass.
- **OpenClaw authentication flexibility**:
  - the integration now accepts either `OpenClaw token` or `OpenClaw kode/password`
  - token remains the preferred auth path when both are present

### Changed
- **OpenClaw setup UX**:
  - the provider/options forms now expose both token and password-style credentials for OpenClaw webhook auth
  - this makes first-time setup on a new machine consistent with the real form fields the user can enter

## v0.3.0

Date: 2026-04-04

### Added
- **MQTT-backed OpenClaw decision flow**:
  - finished OpenClaw heating decisions can now be adopted through the MQTT topic `homeassistant/ai_varme/openclaw/decision`
  - the integration is now documented around a stable decision-delivery path instead of instruction-wrapper style hooks
- **Comfort Mode**:
  - new switchable comfort behavior layer via `switch.ai_varme_styring_komfort_mode_aktiv`
  - comfort mode can use humidity, occupancy, comfort gap, and opening state to influence internal heating behavior
  - comfort mode does not overwrite the room's fixed AI setpoint
- **Expanded room comfort observability**:
  - room status now exposes comfort-related fields such as `komfort_target`, `komfort_gap`, `komfort_offset_c`, `effektivt_varmebehov`, `komfort_b?nd`, and `komfort_?rsag`
- **Public OpenClaw setup guide**:
  - new `OPENCLAW_MQTT_SETUP.md` explains the OpenClaw-to-MQTT setup and includes a copy-paste plain text block for OpenClaw-side tooling

### Changed
- **AI setpoint ownership is now strict**:
  - the room AI setpoint is treated as the user-owned main target
  - runtime comfort and heating logic must optimize around it instead of silently rewriting it
- **AI reporting is richer and more operational**:
  - full report now includes last decision time, request and run identifiers, richer diagnostics, override reasoning, and comfort notes
- **OpenClaw documentation is now release-oriented**:
  - README content is now aligned with HACS/GitHub usage and the documented MQTT delivery path

### Fixed
- **Comfort switch status consistency**:
  - `komfort_status` now follows the real switch state instead of stale coordinator text
- **Away-mode payload mapping**:
  - OpenClaw payload mode no longer mislabels the house as away just because presence eco is active
- **Room control responsiveness**:
  - room target controls and AI room status behavior were hardened so the dashboard reflects changes more reliably
- **Decision report clarity**:
  - better explanation of why a decision was taken and when it was last updated

## v0.2.1

Date: 2026-04-01

### Fixed
- **Heat pump command spam / anti-beep** (Qlima and other units):
  - The integration no longer sends repeated `set_temperature` or `set_hvac_mode` commands every minute when nothing has actually changed.
  - Commands are now skipped if the current climate state already matches the target.
  - Pending and recently-sent commandsare tracked within the cycle to avoid redundant calls.
- **Qlima whole-degree setpoint handling**:
  - Qlima heat pumps now receive whole-degree targets only (rounded to nearest integer).
  - Sub-degree fluctuations no longer cause unnecessary beeps or repeated IR blasts.
- **Coast instead of OFF** in normal stabilization:
  - Heat pumps now prefer staying in low-heat/coast mode rather than being turned fully OFF when near target.
  - OFF is now reserved for explicit pause, door-open, major overheat, or AI-directed off commands.
  - Avoids unnecessary compressor cycling and audible state changes.
- **Correct start threshold respected**:
  - Heat pumps now correctly use the configured `start_deficit_c` threshold before activating.
  - Units no longer react aggressively to very small deficits that are within normal measurement noise.
- **asyncio startup/runtime fix**:
  - Fixed `Coordinator refresh failed: name 'asyncio' is not defined` error on startup/refresh.
  - `asyncio` is now correctly imported at the top of `coordinator.py`.

### Note
- **Reduced conflicts with legacy AC automations** (HA-config side):
  - Legacy direct AC automations in `automations.yaml` have been conditioned to only activate when AI heating control is explicitly disabled.
  - This is a Home Assistant config change, not an integration code change. Existing installations should review their local automations if they experience control conflicts.

## v0.2.0

Date: 2026-04-01

### Added
- **OpenClaw model selection** in options flow:
  - `Foretrukken OpenClaw-model` (default: `gpt-5-mini`)
  - `Fallback OpenClaw-model` (default: `gpt-4.1`)
  - Selected models must be activated in the user's OpenClaw instance.
  - The integration sends model hints to OpenClaw; actual routing is handled by OpenClaw.
- **Per-room humidity sensor** configuration:
  - Each room can now have a dedicated humidity sensor.
  - Humidity is factored into per-room comfort gap evaluation.
- **Humidity-aware comfort analysis**:
  - Effective comfort gap now accounts for relative humidity.
  - Dry or humid air can influence AI recommendations without simply forcing more heat.

### Improved
- **Options flow restructured** into clearer sections:
  - General settings
  - AI providers (cleaner, focused on engine and model selection)
  - Advanced control (technical OpenClaw settings moved here)
- **Room-by-room AI reasoning** improved:
  - AI is given explicit effective comfort gap per room.
  - Reduces self-contradictory reasoning about room state.
  - More accurate room-level override decisions.
- **Report structure** improved:
  - Clearer sections: Kort resume / Rum / Punkter.
  - Reduced duplicate content across sections.
  - Better OpenClaw model and source visibility in report and resume.
  - Footer now shows latest run time consistently.
- **Price/heat-source wording** improved:
  - Better distinction between cheapest heat choice and cheapest alternative to heat pump.
  - Reduced misleading gas vs. heat pump comparisons.

### Fixed
- **Cold-start behavior** after HA restart:
  - Room data is now available sooner.
  - Reduced cases where startup returned empty room data to AI.
- Fixed several runtime errors introduced during earlier refactors.

### Stability
- **Recorder-safe sensor trimming**:
  - Heavy attributes trimmed on `AI Status` and `AI indikator` sensors.
  - Avoids Recorder 16 KB attribute size warnings.
- **Watchman noise reduction**:
  - Archive and backup folders ignored in Watchman config.
  - Reduces false positives from historical files.
