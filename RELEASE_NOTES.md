Release v0.3.20 - Smarter radiator cap and correct setpoint steps

What is fixed:
- In heat-pump-priority mode, radiator is kept below target only while deficit is small.
- If deficit reaches 0.5C or more, radiator can assist heating again.
- Heat pump setpoints are rounded to whole degrees.
- Radiator setpoints are rounded to 0.5C steps.
