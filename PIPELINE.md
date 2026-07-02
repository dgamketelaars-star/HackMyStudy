# Pipeline

Er zijn twee, onafhankelijke pipelines. Beide beginnen bij een handmatig ingelogde Chrome-sessie.

## Vereiste vooraf: Chrome-sessie met debug-poort

Alle scrape-scripts verbinden via `connect_over_cdp` met een **al draaiende** Chrome-sessie op
`http://127.0.0.1:9222` (zie `scripts/config.py`). Niets in dit project start die sessie
automatisch — je start Chrome zelf, buiten het project om, met een debug-poort open, en logt
handmatig in op Coursera. Zie [README.md](README.md#chrome-sessie-starten-handmatige-stap) voor
een voorbeeldcommando.

`scripts/login.py` en `scripts/open_my_chrome.py` zijn losse, alternatieve manieren om een
browservenster te openen en in te loggen — ze zetten zelf **geen** debug-poort open, dus ze zijn
geen vervanging voor de stap hierboven.

## Pipeline 1: één cursus

```
1. python run.py collect-links
   scripts/collect_links.py
   Input:  de huidige, open Coursera-pagina (browser-sessie)
   Output: data/course_links.json, data/course_links.txt

2. python run.py clean-links
   scripts/clean_course_links.py
   Input:  data/course_links.json
   Output: data/learning_items.json
   (filtert op /supplement/, /lecture/, /coach/, /discussionPrompt/, /assignment-submission/)

3a. python run.py download-lessons                OF   3b. python run.py download-course
    scripts/download_lessons.py                        scripts/download_course.py
    Input:  data/learning_items.json                   Input: de huidige, open pagina
    Output: course/html/*.html, course/text/*.txt       Output: course/markdown/*.md (met frontmatter)
    (batch, van te voren verzamelde links)               (interactief, klikt zelf "volgende")

4. python run.py combine
   scripts/combine_course_1.py
   Input:  course/markdown/*.md
   Output: course/course_1_raw.md

5. python run.py generate-module
   scripts/generate_module.py
   Input:  prompts/daan_module_prompt.md + course/course_1_raw.md
   Output: course/module_1_daan_test.md   (via OpenAI, model gpt-4.1)
```

**Let op — twee onafhankelijke manieren om lesinhoud te verzamelen:** stap 3a (html/text-cache)
en stap 3b (markdown, interactief) zijn **niet met elkaar verbonden**. Er is geen script dat
`course/html/`/`course/text/` omzet naar `course/markdown/` — als je beide varianten gebruikt,
scrape je de site in feite twee keer. `course/markdown/` is wat stap 4/5 nodig hebben.

**Bekend aandachtspunt (bewust niet opgelost in deze opschoning):** `download_course.py` haalt
lesinhoud op met zijn eigen, inline `page.evaluate`, terwijl `save_current_lesson.py` daarvoor
de nettere, type-tagged `extract_content.py` gebruikt. Ze leveren net andere output (platte tekst
vs. Markdown-met-frontmatter). Samenvoegen zou dat gedrag veranderen, dus dat is bewust niet
gedaan — een aparte, expliciete beslissing waard als dit ooit wordt opgepakt.

## Pipeline 2: heel programma (meerdere cursussen)

```
1. python run.py collect-program-courses
   scripts/save_program_courses.py
   Input:  de huidige, open programma-overzichtspagina
   Output: data/program_courses.json  (gefilterd op een vaste lijst toegestane cursus-slugs)

2. python run.py collect-program-items
   scripts/collect_program_learning_items.py
   Input:  data/program_courses.json
   Output: data/all_learning_items.json
   (bezoekt zelf elke cursus × module 1-5 en scrollt de leer-items bij elkaar)
```

Er is (nog) geen vervolgstap die `data/all_learning_items.json` downloadt zoals pipeline 1 dat
voor `data/learning_items.json` doet — dat zou de logische volgende stap zijn als deze
programma-brede route verder uitgebouwd wordt.

`scripts/collect_all_links.py` (`python run.py collect-all-links`) is een losstaand hulpscript dat
op de huidige pagina scrolt en linkt verzamelt naar `data/learning_items_full.json` — bruikbaar
als losse verkenningsstap, hangt niet vast aan stap 1 of 2 hierboven.

## Bestanden die tijdelijk/cache zijn

| Bestand(en) | Waarom tijdelijk |
|---|---|
| `data/*.json`, `data/*.txt` | Tussenresultaten van de scrape-stappen, altijd opnieuw te genereren. |
| `course/html/`, `course/text/` | Ruwe scrape-cache van pipeline 1, stap 3a. |
| `course/course_1_raw.md` | Gegenereerd door `combine_course_1.py`, geen bron-bestand. |
| `_archive/` | Oude testbestanden en duplicaten, bewaard maar niet actief. |

## Bestanden die nooit in Git horen

| Bestand(en) | Waarom |
|---|---|
| `browser-profile/` | Live Coursera-sessie: cookies, `Login Data`, `History`. |
| `.venv/` | Lokale Python-omgeving, machine-specifiek. |
| `.env` | Voor toekomstige secrets/API-keys. |
| `__pycache__/`, `*.pyc`, `.ruff_cache/` | Gegenereerde bytecode/lint-cache. |
| `course/html/`, `course/text/` | Groot en mogelijk auteursrechtelijk gevoelig (ruwe Coursera-content). |
| `_archive/` | Bewust buiten Git gehouden — oude/afgekeurde bestanden horen niet in de geschiedenis. |

Vastgelegd in `.gitignore`.
