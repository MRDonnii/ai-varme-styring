Release v0.3.16 - Heat source direction slider and stronger radiator setback

New in cheap-power tuning:
- `heat_source_direction_bias` slider (-2.0 to +2.0)
  - negative = more radiator priority
  - positive = more heat pump priority
- `cheap_power_radiator_setback_extra_c`
  - lowers radiator targets further during cheap-power heat-pump bias

These are grouped under:
- Billig strom: varmepumpe-prioritet
