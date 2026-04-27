Release v0.3.30 - AI off no climate commands

What is fixed:
- Turning off AI Varme Styring now blocks all integration climate commands.
- The restored main switch state is synced into the coordinator at startup, so the UI and control loop cannot disagree after restart.
- Reports and sensors still refresh while disabled, but radiators and heat pumps are left untouched.

Local cleanup note:
- Old local Home Assistant climate-control automations are not part of this public integration release. Keep AI Varme Styring as the only heating-control owner.
