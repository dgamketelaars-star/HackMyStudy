# HackMyStudy

HackMyStudy haalt je Microsoft AI Product Manager Professional Certificate (5 cursussen op
Coursera) op, laat een LLM elke les herschrijven naar jouw leerstijl (zie
[prompts/daan_module_prompt.md](prompts/daan_module_prompt.md)), en toont het resultaat in een
rustige, mobiele reader (`docs/`, gepubliceerd via GitHub Pages).

> **Status:** de webapp toont een cursusoverzicht (alle 5), modulenavigatie per cursus en een
> echte reader met visuals, luistermodus en een interactief vragenpaneel. Alle 5 cursussen zijn
> verzameld met echte modulegrenzen (`data/<slug>/learning_items.json`). Cursus 1 heeft daarnaast
> markdown-brontekst voor module 1 (20/20 lessen) en **module 1 is daadwerkelijk vertaald** naar
> de Daan-leerstijl, inclusief visuals en progressive terminology immersion (zie
> [PIPELINE.md](PIPELINE.md#de-vertaalstap)) — te lezen in de webapp. De overige modules van
> cursus 1 en cursussen 2-5 zijn bewust nog niet vertaald.

## Wat de reader kan

- **Visuals waar ze helpen** — Mermaid-diagrammen voor processen/cycli/hiërarchieën, tabellen voor
  vergelijkingen. Geen decoratieve plaatjes; de vertaalpipeline beslist per onderwerp of een visual
  echt iets toevoegt.
- **Luistermodus** — module hardop laten voorlezen (browser-eigen, geen server nodig): play/pause,
  ↺15s, snelheid, onthoudt waar je gebleven bent.
- **Interactief vragen stellen** — een vragenpaneel dat altijd beschikbaar is tijdens het lezen,
  met snelle acties en een vrij tekstveld. Vereist lokaal `python scripts/qa_server.py` (zie
  [PIPELINE.md](PIPELINE.md#interactief-vragen)) — zonder die server toont het paneel een eerlijke
  melding in plaats van een nep-antwoord.
- **Progressive English terminology immersion** — vaktermen schuiven geleidelijk van Nederlands
  naar Engels naarmate je ze vaker tegenkomt, cursusoverstijgend bijgehouden.

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
gevolgd door `python run.py publish-docs` (kopieert alleen manifest + al-vertaalde modules naar
`docs/`, nooit ruwe scrape-data).

## Interactief vragen lokaal gebruiken

Het vragenpaneel in de reader heeft een backend nodig die je `OPENAI_API_KEY` gebruikt. Draai
lokaal, in een los terminalvenster:

```bash
python scripts/qa_server.py
```

Dit start een server op `http://127.0.0.1:8765` — alleen bereikbaar vanaf je eigen machine, geen
nieuw account nodig. Laat hem draaien terwijl je de webapp (lokaal of de gepubliceerde
GitHub Pages-site) open hebt; het vragenpaneel vindt hem vanzelf. Voor gebruik onderweg (vanaf je
telefoon, zonder dat je laptop aanstaat) is een gehoste variant nodig — zie
[PIPELINE.md](PIPELINE.md#interactief-vragen) voor de voorbereide (niet-geactiveerde) optie.

## Deployment (GitHub Pages)

De webapp is bedoeld voor persoonlijk gebruik (bv. vanaf je telefoon), niet als publieke
productlancering. Hosting: **GitHub Pages, "Deploy from a branch", bron `/docs` op de
`master`-branch** — geen build-stap, geen GitHub Actions-workflow nodig, want `docs/` is al
kant-en-klare statische HTML/CSS/JS.

Instellen (eenmalig, in de GitHub-webinterface): repo → **Settings → Pages** → Source: *Deploy
from a branch* → Branch: `master`, map: `/docs` → Save. GitHub bouwt de site vervolgens bij elke
push naar `master` opnieuw.

`docs/.nojekyll` staat erbij zodat GitHub's standaard Jekyll-verwerking wordt overgeslagen — anders
zou GitHub Pages proberen de `.md`-bestanden onder `docs/content/` als Jekyll-pagina's te
behandelen in plaats van ze als platte tekst te serveren voor de `fetch()`-aanroepen in de webapp.

**Hoe nieuwe vertaalde modules online komen:** de vertaalpipeline blijft volledig lokaal (scrapen,
OpenAI-aanroepen). Zodra een nieuwe module lokaal vertaald en gepubliceerd is
(`run.py build-manifest` + `run.py publish-docs`), commit en push je de wijzigingen in `docs/` —
GitHub Pages herbouwt daarna automatisch. Er gaat nooit een OpenAI-aanroep of API-key naar de
browser of naar GitHub Pages zelf; alleen de al-vertaalde platte markdown-bestanden.

Alle links/paden in `docs/` zijn relatief (geen absolute `/pad`-verwijzingen), dus de site werkt
zowel lokaal (`http://localhost:8000/index.html`) als onder het GitHub Pages-subpad
(`https://<gebruiker>.github.io/<repo-naam>/index.html`) zonder aanpassingen. Cursus-/module-URL's
gebruiken query-parameters (`course.html?course=...`, `module.html?course=...&module=...`), geen
client-side routing — directe navigatie (bookmark, gedeelde link, homescreen-icoon) laadt dus
altijd het juiste, bestaande HTML-bestand, zonder 404's of speciale server-configuratie.

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
