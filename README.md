# HackMyStudy

HackMyStudy haalt cursusmateriaal van Coursera op, laat een LLM dat herschrijven naar een
persoonlijke leerstijl (zie [prompts/daan_module_prompt.md](prompts/daan_module_prompt.md)), en
toont het resultaat in een lichte, mobiele Markdown-reader (`docs/`, gepubliceerd via GitHub
Pages).

> **Status:** de reader-webapp in `docs/` is nog een skelet — `docs/js/app.js` bevat op dit moment
> alleen een `console.log`. De content-pipeline (scrapen → opschonen → herschrijven) is het deel
> dat al werkt.

Zie ook: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) (wat staat waar) en
[PIPELINE.md](PIPELINE.md) (hoe de stappen precies in elkaar haken, input/output per script).

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

Voor de volledige, aanbevolen volgorde (welke output een script van het vorige nodig heeft): zie
[PIPELINE.md](PIPELINE.md).

## Belangrijk: wat hoort nooit in Git

- `browser-profile/` — bevat je live Coursera-sessie/cookies/wachtwoorden
- `.venv/`, `__pycache__/`, `.ruff_cache/` — lokale/gegenereerde bestanden
- `.env` — voor eventuele toekomstige secrets
- `course/html/`, `course/text/` — ruwe scrape-cache, groot en auteursrechtelijk gevoelig

Dit staat al in `.gitignore`. Zie [PIPELINE.md](PIPELINE.md#bestanden-die-nooit-in-git-horen)
voor de volledige lijst met uitleg.

## Development

```bash
pip install -r requirements-dev.txt
ruff check .
```

Draait ook automatisch als GitHub Action op elke push/PR (`.github/workflows/lint.yml`).
