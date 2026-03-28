# AI Varme Styring

`AI Varme Styring` er en custom integration til Home Assistant, som styrer varmepumper og radiatorer rum-for-rum med prisbevidst logik, presence-eco og valgfrit PID-lag.

## Note

Projektet er som udgangspunkt lavet til min egen Home Assistant-installation.
Der er ingen garanti for løbende videreudvikling eller bred kompatibilitet.

## Hvad den gør

- Styrer varme pr. rum med egne sensorer, setpoints og enheder.
- Understøtter både varmepumpe og radiator i samme rum.
- Bruger AI-provider til beslutningsfaktor:
  - Ollama
  - Gemini
- Har prisbevidst drift med elpris og alternativ varmekilde (gas eller fjernvarme).
- Har Presence-Eco med tidsvinduer (away/return), så den sænker måltemperatur når huset er tomt.
- Har valgfrit PID-lag ovenpå den normale styring, som kan toggles til/fra.
- Genererer status og rapport-sensorer til dashboard.

## Entiteter integrationen opretter

- Switches:
  - Aktiv styring
  - Presence-Eco aktiv
  - PID-lag aktiv
- Number:
  - Global AI-mål
  - Eco AI-mål
- Sensorer:
  - AI Status
  - Billigste varmekilde
  - Største underskud
  - PID-lag status
  - AI Rapport

## Opsætning

1. Installer integrationen som custom component.
2. Tilføj integrationen i Home Assistant.
3. Vælg AI-provider og globale sensorer.
4. Tilføj de rum, der skal styres (kun valgte rum styres).
5. Finjustér tærskler og aktiver evt. Presence-Eco og PID-lag.

## Status

Første offentlige release: `v0.1.0`.

## Standalone migration

Integrationen er designet til at kunne køre uden legacy varmepumpe-automations.
Se migration-guiden:

- `MIGRATION_STANDALONE.md`
