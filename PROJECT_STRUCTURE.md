# Project-structuur

## Mappen

| Map | Doel |
|---|---|
| `run.py` | Eén startpunt voor de hele pipeline (`python run.py --help`). |
| `scripts/` | Alle Python-scripts van de content-pipeline (scrapen, opschonen, herschrijven). |
| `data/` | Kleine JSON/txt-tussenbestanden: lijsten van links en leer-items. Input/output van de scrape-stappen, geen eindproduct. |
| `course/` | Cursusinhoud. `markdown/` is het eindproduct van deze map; `html/` en `text/` zijn ruwe scrape-cache (niet in Git, zie [PIPELINE.md](PIPELINE.md)). |
| `docs/` | De publieke webapp (GitHub Pages), toont de Markdown-lessen in een mobiele reader. |
| `prompts/` | Prompts voor de LLM-herschrijfstap, bv. het persoonlijke leerprofiel. |
| `_archive/` | Oude testbestanden, duplicaten en debug-scripts. Bewust bewaard, niet in Git (zie `.gitignore`), niet actief in gebruik. |
| `browser-profile/` | Playwright's opgeslagen browser-sessie (cookies/login voor Coursera). **Nooit in Git.** |
| `.venv/` | Lokale Python-omgeving. **Nooit in Git.** |

## Scripts (`scripts/`)

| Script | Doel |
|---|---|
| `config.py` | Centrale paden en constanten (CDP-URL, data/course-locaties) — geen eigen entry point. |
| `scraping_utils.py` | Kleine gedeelde hulpfunctie (`clean_title`) — geen eigen entry point. |
| `extract_content.py` | Haalt lesinhoud (reading/video) van de huidige pagina — geen eigen entry point, wordt aangeroepen door `save_current_lesson.py`. |
| `login.py` | Opent een geïsoleerde Playwright-browser (`browser-profile/`) om in te loggen op Coursera. |
| `open_my_chrome.py` | Alternatief: opent je eigen, echte Chrome-profiel om in te loggen. |
| `collect_links.py` | Verzamelt alle `/learn/`-links op de huidige pagina → `data/course_links.json`/`.txt`. |
| `clean_course_links.py` | Filtert ruwe links tot echte leer-items (lecture/supplement/…) → `data/learning_items.json`. |
| `download_lessons.py` | Downloadt elk leer-item als ruwe html + text → `course/html/`, `course/text/`. |
| `download_course.py` | Loopt via de "volgende"-knop door een cursus en slaat elke les op als Markdown → `course/markdown/`. |
| `save_current_lesson.py` | Slaat alleen de huidige pagina op als één Markdown-les (met frontmatter) → `course/markdown/`. |
| `combine_course_1.py` | Voegt alle Markdown-lessen samen tot één bestand → `course/course_1_raw.md`. |
| `generate_module.py` | Stuurt de ruwe cursustekst + prompt naar OpenAI en slaat de herschreven versie op → `course/module_1_daan_test.md`. |
| `save_program_courses.py` | (Programma-brede pipeline) Verzamelt toegestane cursussen van het hele programma → `data/program_courses.json`. |
| `collect_program_learning_items.py` | (Programma-breed) Verzamelt leer-items voor alle programma-cursussen → `data/all_learning_items.json`. |
| `collect_all_links.py` | (Programma-breed) Scrollt en verzamelt leerlinks op de huidige pagina → `data/learning_items_full.json`. |

Voor de volgorde waarin deze scripts elkaar opvolgen: zie [PIPELINE.md](PIPELINE.md).

## `docs/` (de webapp)

| Bestand | Doel |
|---|---|
| `index.html` | Startpagina. |
| `modules/module-1.html` | Toont één module, laadt de Markdown-content via `js/module1.js`. |
| `content/module1.md` | De Markdown-tekst die getoond wordt (handmatig hierheen gekopieerd vanuit `course/`). |
| `css/style.css`, `js/app.js`, `js/module1.js` | Styling en front-end logica. `app.js` is nog een lege stub. |
