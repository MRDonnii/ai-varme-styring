# AI Varme Styring

![AI Varme Styring logo](custom_components/ai_varme_styring/logo.png)

Lokal Home Assistant-integration til AI-baseret varmestyring med OpenClaw som primær beslutningsmotor og valgfri fallback til Ollama eller Gemini.

## Hvad integrationen gør

- AI-baseret varmebeslutning med room-first logik
- OpenClaw som primær beslutningsmotor med fallback-modelvalg
- Valgfri fallback til Ollama eller Gemini ved fejl eller timeout
- Fugtighedsbevidst komfortanalyse pr. rum
- Strukturerede rapporter og statusfelter til dashboard og fejlfinding
- Lokal drift med fokus på stabilitet og sikre standardvalg

## Installation via HACS

1. Åbn HACS i Home Assistant
2. Vælg `Custom repositories`
3. Tilføj `https://github.com/MRDonnii/ai-varme-styring`
4. Vælg typen `Integration`
5. Installer **AI Varme Styring**
6. Genstart Home Assistant

## Konfiguration

Integrationen understøtter flere beslutningsmotorer:

- `OpenClaw`
- `Ollama`
- `Gemini`

Du kan blandt andet konfigurere:

- primær beslutningsmotor
- fallback-motor
- rapportmotor
- foretrukken OpenClaw-model
- fallback OpenClaw-model
- payload-profil (`light` eller `heavy`)

## OpenClaw i praksis

Når OpenClaw bruges, sender integrationen en struktureret payload med rumdata, komfortgap, temperaturer og relevante driftsoplysninger. OpenClaw returnerer en beslutning, som bagefter vises i Home Assistant som status, sensorattributter og rapportdata.

Beslutningsflowet er designet til at være robust:

- hurtige standardvalg ved fejl
- fallback når primær motor ikke svarer
- gyldig JSON-beslutning med bounds og sikkerhedsregler
- tydelig visning af hvilken motor og model der faktisk blev brugt

## Rapportering

Rapportvisningen er bygget til at kunne bruges direkte i Home Assistant:

- kort resume med aktiv motor og model
- rumsektion med komfortanalyse
- punkter med observationer og advarsler
- tydelig angivelse af seneste køretid

## Vigtige filer

- `custom_components/ai_varme_styring/manifest.json`
- `custom_components/ai_varme_styring/config_flow.py`
- `custom_components/ai_varme_styring/coordinator.py`
- `custom_components/ai_varme_styring/ai_client.py`
- `custom_components/ai_varme_styring/sensor.py`
- `custom_components/ai_varme_styring/README.md`

## HACS metadata

Repoet er sat op til HACS med:

- root `hacs.json`
- integration `custom_components/ai_varme_styring/hacs.json`
- `render_readme: true`

## Bemærk

Hvis GitHub, HACS eller Home Assistant viser forskellige versionsnumre, skyldes det typisk cache eller forskellen mellem `tags`, `releases` og den installerede lokale version. Den version, HACS normalt skal bruge, findes under GitHub Releases.
