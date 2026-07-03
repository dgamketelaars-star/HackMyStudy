# Project-structuur

## Mappen

| Map | Doel |
|---|---|
| `run.py` | Eén startpunt voor de hele pipeline (`python run.py --help`). |
| `scripts/` | Alle Python-scripts van de content-pipeline (scrapen, opschonen, vertalen, publiceren). |
| `data/` | Cursusdata: `courses.json` (de 5 officiële cursussen), `manifest.json` (wat de webapp toont), en per cursus een submap `data/<cursus-slug>/` met tussenresultaten. |
| `course/` | Per cursus (`course/<cursus-slug>/`) de scrape- en vertaalcontent: `html/`, `text/` (ruwe cache), `markdown/` (brontekst per les), `raw.md` (samengevoegd), `translated/` (de echte HackMyStudy-content, per module). |
| `docs/` | De publieke webapp (GitHub Pages): cursusoverzicht, modulenavigatie, reader. Alleen deze map is vanaf de gepubliceerde site bereikbaar. |
| `prompts/` | Prompts voor de LLM-herschrijfstap, bv. het persoonlijke leerprofiel. |
| `_archive/` | Oude testbestanden, duplicaten, prototype-pagina's. Bewust bewaard, niet in Git. |
| `browser-profile/` | Playwright's opgeslagen browser-sessie (cookies/login voor Coursera). **Nooit in Git.** |
| `.venv/` | Lokale Python-omgeving. **Nooit in Git.** |

### Cursus-slug

Elke cursus heeft een stabiele identifier: het laatste segment van de Coursera-URL, bv.
`microsoft-enterprise-product-management-fundamentals`. Die slug is de mapnaam onder zowel
`course/` als `data/`, en staat als `slug`-veld in `data/courses.json`.

```
course/microsoft-enterprise-product-management-fundamentals/
├── html/         (ruw, buiten Git)
├── text/         (ruw, buiten Git)
├── markdown/     (brontekst per les, in Git)
├── raw.md        (alle markdown-lessen samengevoegd, in de echte cursusvolgorde)
└── translated/   (de vertaalde content, één bestand per module: module-1.md, module-2.md, ...)

data/microsoft-enterprise-product-management-fundamentals/
├── course_links.json / .txt
└── learning_items.json   (de leer-items van deze cursus, met volgorde en modulenummer)
```

De vertaalstap werkt op **moduleniveau**, niet per losse les (zie PIPELINE.md) — vandaar
`translated/module-<n>.md` in plaats van één bestand per les.

## Scripts (`scripts/`)

| Script | Doel |
|---|---|
| `config.py` | Centrale paden en constanten, cursus-parametrisch (`config.markdown_dir(slug)` etc.) — geen eigen entry point. |
| `scraping_utils.py` | Gedeelde hulpfuncties: `clean_title`, `normalize_title`, `slugify`, `course_slug_from_url`, `guess_module_title` — geen eigen entry point. |
| `extract_content.py` | Haalt lesinhoud (reading/video) van de huidige live pagina — wordt aangeroepen door `save_current_lesson.py`. |
| `login.py` | Opent een geïsoleerde Playwright-browser (`browser-profile/`) om in te loggen op Coursera. |
| `open_my_chrome.py` | Alternatief: opent je eigen, echte Chrome-profiel om in te loggen. |
| `save_program_courses.py` | Verzamelt de 5 officiële cursussen (met slug) → `data/courses.json`. |
| `collect_program_learning_items.py` | Bezoekt alle 5 cursussen × module 1-5 en verzamelt lessen (mét modulenummer) → `data/<cursus>/learning_items.json`. De primaire manier om spoor 1 te vullen. |
| `collect_links.py` | (losse pagina) Verzamelt alle `/learn/`-links van de huidige pagina → `data/<cursus>/course_links.json`/`.txt`. |
| `clean_course_links.py` | Filtert `course_links.json` tot leer-items, voor elke cursus die dat heeft (batch) → `data/<cursus>/learning_items.json`. |
| `collect_all_links.py` | (losse pagina) Scrollt en verzamelt leerlinks → `data/<cursus>/learning_items_full.json`. |
| `download_lessons.py` | Downloadt elk leer-item als ruwe html + text, voor elke cursus met `learning_items.json` (batch, idempotent) → `course/<cursus>/html/`, `text/`. |
| `lessons_to_markdown.py` | Zet gecachte **reading**-lessen offline om naar markdown (video's niet — zie PIPELINE.md) → `course/<cursus>/markdown/`. |
| `download_course.py` | (interactief, live pagina) Loopt via de "volgende"-knop door een cursus, slaat elke les op als markdown. |
| `save_current_lesson.py` | (interactief, live pagina) Slaat alleen de huidige pagina op als één markdown-les. |
| `combine_course.py` | Voegt de markdown-lessen van elke cursus samen in de echte Coursera-volgorde (niet alfabetisch) → `course/<cursus>/raw.md`. |
| `translate_module.py` | **De echte vertaalstap**: vertaalt één module (alle lessen samen, niet los) naar de Daan-leerstijl via OpenAI → `course/<cursus>/translated/module-<n>.md`. Kost echt geld — zie PIPELINE.md. |
| `generate_module.py` | Oude proof-of-concept vertaalstap (hele cursus afgekapt op 15.000 tekens, niet module-bewust) — niet meer de aanbevolen route, zie PIPELINE.md. |
| `build_manifest.py` | Bouwt `data/manifest.json`: alle 5 cursussen + hun modules + welke al vertaald zijn. |
| `publish_docs.py` | Kopieert de manifest + vertaalde modules naar `docs/content/`, zodat de statische webapp ze kan tonen. |

Voor de volgorde waarin deze scripts elkaar opvolgen: zie [PIPELINE.md](PIPELINE.md).

## `docs/` (de webapp)

| Bestand | Doel |
|---|---|
| `index.html` + `js/app.js` | Cursusoverzicht: alle 5 cursussen als kaart, met voortgang (aantal modules vertaald). |
| `course.html` + `js/course.js` | Modulenavigatie voor één cursus (`?course=<slug>`): titel, aantal lessen, vertaald of niet. |
| `module.html` + `js/module.js` | De reader: rendert de vertaalde module-markdown, of een "nog niet vertaald"-status. Prev/next navigeert tussen modules. |
| `js/manifest.js` | Gedeelde helper om `content/manifest.json` op te halen (`loadManifest`, `findCourse`, `findModule`). |
| `content/manifest.json` | Gegenereerd door `publish_docs.py` — niet handmatig bewerken. |
| `content/<cursus-slug>/module-<n>.md` | Gepubliceerde vertaalde modules — niet handmatig bewerken. |
| `css/style.css` | Het volledige ontwerp: donker, groen accent, mobile-first met laptop-breakpoint. |
