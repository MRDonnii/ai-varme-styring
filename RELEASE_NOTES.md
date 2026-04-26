Release v0.3.27 - Heat economy and start-cause diagnostics

What is fixed:
- Heat pumps stay off when their own room is already above target, even when electricity is cheap.
- Linked-room heat demand can still start a pump when the pump room is not already clearly warm.
- Economy reporting now separates physical validation warnings from strategy warnings.
- Validated savings are only published when measurements and strategy are both clean.
- Gas and fjernvarme can be compared alongside heat pumps without removing gas support.
- Danish sensor text has been cleaned so `æ`, `ø`, `å`, and `°` render correctly.
