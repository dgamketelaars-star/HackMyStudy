# HackMyStudy

HackMyStudy haalt je Microsoft AI Product Manager Professional Certificate (5 cursussen op
Coursera) op, laat een LLM elke les herschrijven naar jouw leerstijl (zie
[prompts/daan_module_prompt.md](prompts/daan_module_prompt.md)), en toont het resultaat in een
rustige, mobiele reader (`docs/`, gepubliceerd via GitHub Pages).

> **Status:** de webapp toont een cursusoverzicht (alle 5), lesnavigatie per cursus en een echte
> reader. Cursus 1 (Enterprise Product Management Fundamentals) is verzameld: 28 lessen, 26 als
> markdown-brontekst beschikbaar. Er is nog **geen enkele les daadwerkelijk vertaald** — de
> vertaalstap (`generate_module.py`) is bewust nog de oude proof-of-concept; zie
> [PIPELINE.md](PIPELINE.md#de-vertaalstap-nog-niet-af) voor de openstaande beslissing daarover.
> Cursussen 2 t/m 5 zijn nog niet verzameld.

Zie ook: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) (wat staat waar) en
[PIPELINE.md](PIPELINE.md) (hoe de stappen precies in elkaar haken, input/output per script,
bekende beperkingen).

## Vereisten

- Python 3.12+
- Google Chrome
- Een OpenAI API key (voor de herschrijf-stap)

## Installatie

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
playwright install chromium
```

Zet je OpenAI key als omgevingsvariabele (wordt automatisch opgepikt door de `openai`-library):

```bash
setx OPENAI_API_KEY "sk-..."    # Windows, permanent
```

## Chrome-sessie starten (handmatige stap)

Alle scrape-scripts verbinden met een **al draaiende, ingelogde** Chrome-sessie via het Chrome
DevTools Protocol — ze starten die sessie niet zelf. Start Chrome dus eerst apart met een
debug-poort open, bijvoorbeeld:

```bash
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug-profile"
```

Log in dat venster handmatig in op Coursera. Pas daarna kun je een scrape-commando draaien.
(`scripts/login.py` en `scripts/open_my_chrome.py` openen wél een browservenster om in te loggen,
maar zetten zelf geen debug-poort open — zie [PIPELINE.md](PIPELINE.md) voor de precieze rol van
elk script.)

## Pipeline draaien

Alle stappen zijn te vinden via één centraal startpunt:

```bash
python run.py --help
```

Voor de aanbevolen volgorde om een cursus van "nog niets" naar "in de webapp te lezen" te
krijgen: zie [PIPELINE.md](PIPELINE.md#stap-voor-stap-een-cursus-toevoegen).

## Webapp lokaal bekijken

`docs/` is een statische site (geen build-stap). Lokaal bekijken:

```bash
cd docs
python -m http.server 8000
```

en open `http://localhost:8000`. Na elke wijziging aan de content: `python run.py build-manifest`
gevolgd door `python run.py publish-docs` (kopieert alleen manifest + al-vertaalde lessen naar
`docs/`, nooit ruwe scrape-data).

## Belangrijk: wat hoort nooit in Git

- `browser-profile/` — bevat je live Coursera-sessie/cookies/wachtwoorden
- `.venv/`, `__pycache__/`, `.ruff_cache/` — lokale/gegenereerde bestanden
- `.env` — voor eventuele toekomstige secrets
- `course/*/html/`, `course/*/text/` — ruwe scrape-cache per cursus, groot en auteursrechtelijk
  gevoelig

Dit staat al in `.gitignore`. Zie [PIPELINE.md](PIPELINE.md#bestanden-die-nooit-in-git-horen)
voor de volledige lijst met uitleg.

## Development

```bash
pip install -r requirements-dev.txt
ruff check .
```

Draait ook automatisch als GitHub Action op elke push/PR (`.github/workflows/lint.yml`).
