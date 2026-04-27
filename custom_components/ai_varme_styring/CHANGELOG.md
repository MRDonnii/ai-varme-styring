# Changelog

All significant changes to the integration are documented here.

## v0.3.29

Date: 2026-04-27

### Fixed
- **Heat-pump anti-cycling**:
  - normal warm-room stop decisions now use a long coast period before `OFF`
  - fallback warm-room handling now lowers the heat-pump setpoint while it proves the room can hold temperature
  - `OFF` after normal overshoot now requires a stable stop request and a proven coast period
  - AI damping now coasts down instead of immediately powering the heat pump off

## v0.3.28

Date: 2026-04-26

### Fixed
- **Warm-room linked-demand guard**:
  - linked-room heat demand can no longer wake a heat pump when the heat-pump room itself is already at or above target
  - fallback control now turns an already warm heat-pump room off and locks it as `off_warm_room`
  - cheap-heat coasting now dampens toward a lower setpoint before OFF instead of keeping a warm room active at target

## v0.3.27

Date: 2026-04-26

### Fixed
- **Heat-pump start protection**:
  - heat pumps no longer wake only because electricity is cheap when their own room is already above target
  - linked-room demand can still request heat, but only when the heat-pump room is not already clearly warm
  - start diagnostics now explain whether a heat pump was allowed or blocked, including warm-room blocks

### Improved
- **Measured-first heat economy**:
  - added a dedicated economy model for heat pump, gas, and district heat price comparison
  - AI report sensors now expose strategy, confidence, validation warnings, strategy warnings, gas m3, heat-pump kWh, and validated savings
  - validated savings are only published when both measurement validation and strategy state are clean
  - fjernvarme can be compared alongside gas without removing gas support

### Fixed
- **Danish text cleanup**:
  - repaired mojibake in sensor strings so Danish text with `æ`, `ø`, `å`, and `°` renders correctly

## v0.3.26

Date: 2026-04-25

### Fixed
- **Public package cleanup**:
  - OpenClaw runtime fallback paths now use generic Home Assistant `/config` paths instead of host-specific path names
  - release scope was rescanned for private paths, hostnames, LAN IPs, room names, and token patterns

## v0.3.25

Date: 2026-04-25

### Fixed
- **Generic ECO and heat-pump control**:
  - room-level ECO heat-pump guards now apply to any configured room, not to a room name
  - heat-pump rooms use responsive default start thresholds independent of the room name
  - public release notes no longer describe the fix as a site-specific room correction

## v0.3.24

Date: 2026-04-25

### Fixed
- **Generic ECO heat-pump guard**:
  - if room-level ECO is enabled, the room has no presence, and it is already over target, the heat pump is forced OFF instead of being kept in a heat/hold phase
  - OpenClaw room mode `eco` now activates ECO immediately for empty rooms, so the room does not wait for the normal away timer when the AI already selected ECO
  - when the heat pump is cheapest and the room is under the active target, local control starts the heat pump even if AI recently suggested a softer mode
  - Qlima heat pumps are started with `set_temperature` plus `hvac_mode: heat`, fixing devices that ignore standalone `set_hvac_mode`
  - prevents heat-pump rooms from heating above target while ECO is supposed to lower the room

## v0.3.23

Date: 2026-04-24

### Fixed
- **Heat-pump short-cycle protection**:
  - heat-pump commands now use phase-aware control with warmup, hold, coast, and locked-off phases
  - stop decisions require stronger comfort confirmation before turning a pump off
  - repeated target/mode commands are held back to reduce beeps and unnecessary cycling

### Improved
- **Room and command diagnostics**:
  - AI report attributes now expose clearer room diagnostics and recent heat-pump command decisions
  - dashboards can show whether a room is heating, holding, coasting, paused by openings, or blocked by comfort logic

### Fixed
- **Danish room slug handling**:
  - room entity unique IDs now normalize real `æ`, `ø`, and `å` characters as well as mojibake variants
  - prevents duplicate broken entities such as `ka_kken` for `Køkken`

### Improved
- **Fjernvarme readiness**:
  - district heating price and consumption inputs are supported in the price-aware decision context
  - setups can transition from gas to fjernvarme without changing the control model

## v0.3.22

Date: 2026-04-19

### Changed
- **OpenClaw is now conversation-first**:
  - AI Varme Styring now uses the `openclaw_conversation` agent path as the primary OpenClaw decision flow
  - heating decisions no longer depend on MQTT delivery as the normal path
  - decision source and transport are exposed clearly as `OpenClaw conversation` / `openclaw_conversation_agent`

### Improved
- **Price-aware OpenClaw payload for cost-saving decisions**:
  - OpenClaw conversation payloads now include runtime and price context such as cheapest heat source, alternative price, and estimated savings
  - this lets the decision agent actively optimize for lower heating cost instead of reasoning without price data

### Improved
- **AI report readability and Danish text stability**:
  - report output is now structured into clearer sections like `Kort resume`, `Aktiv beslutning`, `Kontekst`, and `Rum-beslutninger`
  - report attributes and room lines now clean mojibake-prone text so Danish characters render correctly in Home Assistant cards

### Fixed
- **Reduced unnecessary AI-driven setpoint and mode churn**:
  - small OpenClaw room overrides are now held back for a stabilization window before new commands are sent
  - tiny target changes are ignored, and non-urgent mode flips are delayed
  - this reduces unnecessary heat-pump beeps and repeated state flips

## v0.3.21

Date: 2026-04-06

### Fixed
- **Linked-room heat pump activation**:
  - heat-pump rooms now include `room_adjacent_rooms` directly in shared-demand evaluation
  - prevents missed starts where a connected room is under target but the pump room is slightly over target

### Fixed
- **Stale OpenClaw mode overrides**:
  - room-level `openclaw_mode_override` values are now cleared when new decisions no longer include that room
  - prevents old `off`/`eco` mode directives from sticking in runtime state

### Fixed
- **Heat-pump stop/overheat signal source**:
  - overheat and stop/coast decisions for heat pumps now use raw room surplus where relevant
  - reduces false overheat behavior from bias-adjusted values

### Fixed
- **Opening pause safety behavior**:
  - during active opening pause, heat pumps are now damped down immediately when room is above target
  - high overtemperature during opening can now force `OFF` faster instead of waiting for long pause timers

### Improved
- **Cheap-power fan strategy is now active in control loop**:
  - `heat_pump_cheap_fan_mode` is now applied during heat/coast actions when heat pumps are cheapest
  - keeps airflow strategy aligned with heat-pump priority tuning

### Improved
- **Shared-demand anti-coast handling**:
  - linked heat pumps now stay in active heat mode with assist setpoint when shared demand exists
  - avoids premature passive coast in connected-room demand scenarios

## v0.3.20

Date: 2026-04-06

### Fixed
- **Radiator behavior in heat-pump-priority mode**:
  - radiator target in heat-pump rooms is now capped below AI target only while room deficit is small
  - if room deficit grows (>= 0.5C), radiator is allowed to help raise temperature
  - this keeps radiator down near target but still recovers cold rooms correctly

### Fixed
- **Temperature step handling by device type**:
  - heat pump targets are normalized to whole degrees
  - radiator/thermostat targets are normalized to 0.5C steps
  - avoids drift and inconsistent setpoints against device step capabilities

## v0.3.19

Date: 2026-04-06

### Fixed
- **Radiator cap in cheap-power heat-pump bias**:
  - when cheap-power heat-pump bias is active in rooms with heat pumps, radiator target is now hard-capped below room target
  - prevents cases where radiator setpoints could end up at or above room target (for example 22.5 when room target is 22.0)
  - cap strength scales slightly with positive room heat-source bias

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
- **Heat-pump room start responsiveness**:
  - heat-pump rooms now use lower default start thresholds so small deficits like 21.8 -> 22.0 are no longer ignored
  - existing heat-pump rooms that still carry the old default `0.4` thresholds are migrated at runtime to the new heat-pump defaults
  - the room editor now also shows the lower defaults for new or edited heat-pump rooms

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
