# AI Varme Styring

Lokal Home Assistant-integration til AI-baseret varmestyring med valgbar beslutningsmotor.

**Aktuel version: 0.2.1**

## Formål

Integrationen samler varmestyring, rapportering og observability i én HA-integration.
Brugeren kan vælge mellem flere AI-motorer og stadig beholde en stabil, lokal styringslogik.

OpenClaw er nu den primært anbefalede beslutningsmotor.
Integration med Ollama og Gemini understøttes fortsat som alternativer.

## Beslutningsmotorer

Integrationens beslutningslag understøtter:
- `OpenClaw` *(anbefalet primær motor)*
- `Ollama`
- `Gemini`

Brugeren kan vælge i integrationens options:
- `Primær beslutningsmotor`
- `Fallback-motor`
- `Rapportmotor`
- `Payload-profil` for OpenClaw og provider-sporet (`light` eller `heavy`)

## OpenClaw modelvalg

Hvis OpenClaw bruges, kan brugeren angive foretrukne modeller i options-flowet:

- `Foretrukken OpenClaw-model`: den model der bruges til primære beslutninger
- `Fallback OpenClaw-model`: bruges hvis den foretrukne model ikke svarer

Standardanbefalinger:
| Felt | Standard |
|---|---|
| Foretrukken model | `gpt-5-mini` |
| Fallback model | `gpt-4.1` |

**Vigtigt:** Vælg kun modeller der faktisk er aktiverede i din OpenClaw-instans.
Integrationen sender model-hint videre til OpenClaw, men kan ikke verificere om modellen er tilgængelig.

## Sådan konfigureres AI (options-flowet)

Options-flowet er opdelt i tre sektioner:

### Generelle indstillinger
- Navn og rum-opsætning.
- Aktivering af temperaturkalibrering, bevægelsesøkonomi og PID-lag.

### AI-udbydere
- `Primær beslutningsmotor`: den motor der bruges til AI-beslutninger (anbefalet: `OpenClaw`)
- `Fallback-motor`: bruges hvis primærmotoren fejler (anbefalet: `none` eller `Ollama`)
- `Rapportmotor`: bruges til AI-genererede rapporter
- `Foretrukken OpenClaw-model`: sendes som hint til OpenClaw (standard: `gpt-5-mini`)
- `Fallback OpenClaw-model`: bruges hvis foretrukken model ikke svarer (standard: `gpt-4.1`)

**Bemærk:** OpenClaw-modeller skal være aktiverede i brugerens OpenClaw-instans.
Integrationen sender et model-hint — det er OpenClaw der afgør den endelige routing.

### Avanceret styring
- Timeout, intervaller og tekniske OpenClaw-parametre.
- Flyttes hertil for at holde AI-udbyderssektionen ren.

## Rapportering og analyse

Rapportstrukturen er forbedret og inddelt i tre sektioner:

- **Kort resume**: beslutningsmotor, model, overordnet vurdering
- **Rum**: per-rum analyse med effektiv komfortgab og fugtighedsdata
- **Punkter**: konkrete observationer og eventuelle advarsler

Rapportkortet viser:
- aktiv beslutningsmotor og model
- fallback-motor
- rapportmotor
- seneste køretid i footeren

## Fugtighed og komfortanalyse

Fra v0.2.0 tages fugtighed med i komfortvurderingen:

- Komfortgab kan afvige fra råtemperaturdeficit afhængigt af luftfugtighed.
- Per-rum fugtighedssensor kan angives separat i rum-opsætningen.
- Tør eller fugtig luft kan påvirke anbefalinger uden at tvinge mere varme.
- AI-modellen gives eksplicit rumkontekst med effektivt komfortgab.

## Stabilitet og performance

- Koldstart-håndtering er forbedret: rumdata er tilgængeligt hurtigere efter HA-genstart.
- Vigtige AI-sensorer trimmes for store attributter så Recorder undgår 16 KB-advarslen:
  - `AI Status`
  - `AI indikator`
- Watchman er konfigureret til at ignorere arkiv- og backupmapper for at reducere falske advarsler.


- [`/haconfig/docs/openclaw_heating_stack.md`](/haconfig/docs/openclaw_heating_stack.md)

Driftsdetaljer for bridge og worker ligger her:
- [`/haconfig/tools/systemd/README_openclaw_bridge.md`](/haconfig/tools/systemd/README_openclaw_bridge.md)

## OpenClaw-flow

OpenClaw bruges nu som en rigtig beslutningsmotor og ikke kun som en chat-model.

Aktuelt flow:
1. `ai_varme_styring` bygger en struktureret heating payload.
2. Payload sendes til OpenClaw via hook-endpoint.
3. OpenClaw returnerer `runId`.
4. En lokal completion worker læser OpenClaw-sessionerne.
5. Worker finder den endelige JSON-beslutning.
6. Worker afleverer beslutningen til den lokale bridge-callback.
7. Integrationen viser beslutningen i sensorer, status og rapportkort.

## Endelig beslutningsschema

```json
{
  "factor": 1.0,
  "confidence": 95,
  "reason": "Ingen rum kræver ændring – kun små afvigelser fra måltemperatur.",
  "global": {
    "mode": "normal",
    "boost": false
  },
  "rooms": []
}
```

## Hvad integrationen eksponerer i HA

Vigtige felter og sensorer:
- `AI beslutningsmotor`
- `ai_decision_source`
- `ai_primary_engine_display`
- `ai_decision_source_display`
- `ai_openclaw_meta`
- `ai_struktureret_beslutning`
- `ai_decision_payload`
- `ai_decision_payload_openclaw`
- `ai_decision_payload_provider`
- `ai_report_payload`
- `openclaw_bridge_stats`

Rapportkortet viser også:
- beslutningsmotor
- fallback-motor
- rapportmotor
- seneste køretid i footeren

## Light og Heavy payloads

Der bruges to payload-profiler:

- `heavy`
  - rig rumkontekst
  - runtime flags
  - priser
  - bridge-/OpenClaw-metadata
  - bedst til OpenClaw

- `light`
  - kompakt styringspayload
  - bedst til hurtigere provider-kald og fallback

## Vigtige filer i integrationsmappen

- `manifest.json`
- `config_flow.py`
- `const.py`
- `coordinator.py`
- `ai_client.py`
- `sensor.py`
- `switch.py`
- `button.py`
- `number.py`
- `translations/`

## Runtime-filer udenfor integrationen

OpenClaw-runtime ligger bevidst udenfor selve integrationsmappen.
De hører til Home Assistant-hostens drift og ikke til HACS-pakken alene.

Vigtige runtime-filer:
- `/haconfig/tools/openclaw_decision_bridge.py`
- `/haconfig/tools/openclaw_session_completion_worker.py`
- `/haconfig/tools/openclaw_bridge_ctl.sh`
- `/haconfig/tools/openclaw_completion_worker_ctl.sh`
- `/haconfig/tools/openclaw_services_ensure.sh`
- `/haconfig/packages/openclaw_bridge_callback.yaml`

## Midlertidige runtime-filer

Følgende filer er drifts-/debugfiler og skal ikke behandles som kildekode:
- `/haconfig/_tmp_openclaw_bridge.log`
- `/haconfig/_tmp_openclaw_completion_worker.log`
- `/haconfig/_tmp_openclaw_completion_results.json`
- `/haconfig/_tmp_openclaw_completion_worker_state.json`
- `/haconfig/_tmp_openclaw_services_ensure.log`

## Hvad der ikke er autoritativt

Den gamle mappe `ha-ai-heating-private` er ikke den aktive integrationskode.
Den autoritative integration ligger i:
- `/haconfig/custom_components/ai_varme_styring`

## Status

Integrationens nuværende mål er:
- OpenClaw som reel primær beslutningsmotor
- valgfri fallback til Ollama eller Gemini
- klare sensorer og kort der viser hvilken motor der faktisk blev brugt
- stabil lokal drift uden npm-afhængigheder
