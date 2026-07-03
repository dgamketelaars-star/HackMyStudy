# Pipeline

HackMyStudy verwerkt 5 Coursera-cursussen (het Microsoft AI Product Manager Professional
Certificate). Elke cursus heeft een stabiele **slug** (zie
[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md#cursus-slug)) en eigen data onder `course/<slug>/` en
`data/<slug>/`.

## Vereiste vooraf: Chrome-sessie met debug-poort

Alle scrape-scripts verbinden via `connect_over_cdp` met een **al draaiende** Chrome-sessie op
`http://127.0.0.1:9222` (zie `scripts/config.py`). Niets in dit project start die sessie
automatisch — je start Chrome zelf, buiten het project om, met een debug-poort open, en logt
handmatig in op Coursera. Zie [README.md](README.md#chrome-sessie-starten-handmatige-stap) voor
een voorbeeldcommando.

`scripts/login.py` en `scripts/open_my_chrome.py` zijn losse, alternatieve manieren om een
browservenster te openen en in te loggen — ze zetten zelf **geen** debug-poort open.

## Stap voor stap: een cursus toevoegen

```
1. python run.py collect-program-courses
   Eenmalig (of opnieuw als Coursera het programma wijzigt).
   Output: data/courses.json — de 5 cursussen met slug/titel/URL.

2. python run.py collect-program-items
   Bezoekt automatisch alle 5 cursussen x module 1-5 in de al-open sessie.
   Output: data/<slug>/learning_items.json per cursus (met modulenummer).

3. python run.py download-lessons
   Batcht over elke cursus met learning_items.json. Idempotent: slaat
   lessen over die al gedownload zijn.
   Output: course/<slug>/html/, course/<slug>/text/

4. python run.py lessons-to-markdown
   Zet "reading"-lessen offline om naar markdown. Video-lessen worden
   overgeslagen en met naam gerapporteerd (zie hieronder waarom).
   Output: course/<slug>/markdown/

5. (voor de overgeslagen video-lessen, per stuk, interactief:)
   python run.py download-course      -- loopt een hele cursus door
   python run.py save-lesson          -- slaat alleen de huidige les op

6. python run.py combine
   Voegt markdown-lessen samen in de echte Coursera-volgorde (gematcht
   tegen learning_items.json — niet alfabetisch).
   Output: course/<slug>/raw.md

7. (vertaalstap — nog niet definitief, zie hieronder)

8. python run.py build-manifest
   Output: data/manifest.json — wat de webapp laat zien.

9. python run.py publish-docs
   Kopieert manifest + vertaalde lessen naar docs/content/.
```

Stap 1-2 zijn maar één keer nodig per keer dat je alle 5 cursussen wilt verzamelen; stap 3-6
kun je per cursus of in bulk draaien; stap 8-9 draai je opnieuw zodra er nieuwe vertaalde content
is.

## Waarom lessons-to-markdown niet alles kan omzetten

Bij het bouwen van dit script bleek (geverifieerd tegen de echte gescrapete HTML van cursus 1):
Coursera rendert **reading**-lessen server-side — de tekst staat gewoon in de HTML
(`.rc-ReadingItem`). **Video**-lessen tonen hun transcript pas nadat je op het
"Transcript"-paneel klikt; dat gebeurt clientside en zit dus niet in een simpele HTML-download.
De eerdere aanname dat de ruwe `course/<slug>/text/`-cache (van `download_lessons.py`) bruikbare
lesinhoud zou bevatten, klopte niet — die cache bevat voor video's alleen het zijbalk-menu, geen
transcript.

Voor cursus 1 (26 van de 28 lessen als markdown) is dit gat al gedicht via de interactieve
`download_course.py`/`save_current_lesson.py` — die scripts draaien live en konden dus wél de
volledige inhoud pakken. De 2 nog ontbrekende lessen ("Het vaststellen van een
productontwikkelingsproces voor SynergyHR" en "Het kruispunt van de sprintplanning…") zijn
beoordeelde opdrachten/rollenspellen, geen reading of video — waarschijnlijk moet je die met
`save_current_lesson.py` los oppakken.

**Voor cursussen 2-5 betekent dit:** de volledig automatische route (stap 3-4 hierboven) werkt
voor reading-lessen, maar video-lessen moet je nog steeds interactief doorlopen (stap 5). Niet
"zo min mogelijk handmatige tussenstappen" als gehoopt — een eerlijke beperking, geen giswerk.

## De vertaalstap: nog niet af

`scripts/generate_module.py` is nog de oorspronkelijke proof-of-concept: de eerste 15.000 tekens
van de **hele cursus** (niet één module) naar de prompt, als eenmalige test. Dat is bewust
ongewijzigd gelaten — de prompt en vertaalstrategie zijn kernfunctionaliteit
([prompts/daan_module_prompt.md](prompts/daan_module_prompt.md)) en worden niet stilzwijgend
aangepast.

Er is een echte granulariteits-vraag die eerst beantwoord moet worden voordat dit de definitieve
vertaalstap wordt:

- De prompt is geschreven voor **één module** ("Lees de volledige module... Bepaal eerst de beste
  leerstructuur voor deze module") — dus met samenhang over meerdere lessen heen.
- Voor cursus 1 is er geen betrouwbare modulegrens per les (single-page pipeline scrapete zonder
  modulecontext). Cursussen die via `collect_program_learning_items.py` verzameld worden, krijgen
  dat wél (het `module`-veld in `learning_items.json`).
- Een hele cursus (5 modules, ~250 KB tekst) in één keer naar het model sturen past niet goed bij
  de prompt's opzet en wordt duur; per losse les vertalen is goedkoper maar mist de
  module-brede samenhang die de prompt juist vraagt.

Dit is een productbeslissing met echte kostenimpact (OpenAI-aanroepen over 26+ lessen x 5
cursussen), dus geen gok — zie de vraag die hierover apart gesteld is.

## Chat / vragenpaneel — voorstel, niet geïmplementeerd

Vraag: kan een chatbot die vragen beantwoordt over de lesinhoud, veilig binnen de huidige
architectuur? **Niet zonder een architectuurkeuze te maken** — hieronder waarom, en de opties.

`docs/` is een statische site op GitHub Pages: platte bestanden, geen server, geen manier om een
geheim (de OpenAI API key) te verbergen. Een "vraag het de AI"-knop die rechtstreeks vanuit de
browser naar OpenAI belt, zou die key in het gepubliceerde JavaScript moeten meesturen — dan kan
iedereen die de site bezoekt de key uitlezen en op jouw kosten gebruiken. Dat is een reëel
security/kostenrisico, geen theoretisch probleem.

Opties (geen van alle nu geïmplementeerd):

1. **Kleine backend/proxy** (bv. een gratis Cloudflare Worker of Vercel-functie) die de key
   serverside bewaart en de vraag doorstuurt naar OpenAI. Meest flexibel, maar wel nieuwe
   infrastructuur om te beheren/hosten — een echte architectuurstap.
2. **Alleen lokaal draaien**: de chat werkt alleen als je HackMyStudy lokaal serveert (niet via
   de gepubliceerde GitHub Pages-URL) met de key in je eigen omgevingsvariabele. Geen nieuwe
   infrastructuur, maar de chat is dan niet overal beschikbaar waar je ook leest (bv. niet op je
   telefoon onderweg, tenzij je zelf iets host).
3. **Uitstellen tot na spoor 1**: eerst de content-flow en vertaling afronden, chat als los
   vervolgtraject met een bewuste keuze tussen optie 1 en 2.

Dit valt buiten wat ik zonder jouw akkoord zou moeten beslissen — het is precies het soort
architectuurkeuze (nieuwe infrastructuur, of een bewuste beperking) waar de opdracht om vraagt
niet te gokken.

## Bestanden die tijdelijk/cache zijn

| Bestand(en) | Waarom tijdelijk |
|---|---|
| `data/<slug>/*.json` | Tussenresultaten van de scrape-stappen, altijd opnieuw te genereren. |
| `course/<slug>/html/`, `course/<slug>/text/` | Ruwe scrape-cache. |
| `course/<slug>/raw.md` | Gegenereerd door `combine_course.py`, geen bron-bestand. |
| `data/manifest.json`, `docs/content/manifest.json` | Gegenereerd door `build_manifest.py`/`publish_docs.py`. |
| `_archive/` | Oude testbestanden, duplicaten, prototype-pagina's. Bewaard maar niet actief. |

## Bestanden die nooit in Git horen

| Bestand(en) | Waarom |
|---|---|
| `browser-profile/` | Live Coursera-sessie: cookies, `Login Data`, `History`. |
| `.venv/` | Lokale Python-omgeving, machine-specifiek. |
| `.env` | Voor toekomstige secrets/API-keys. |
| `__pycache__/`, `*.pyc`, `.ruff_cache/` | Gegenereerde bytecode/lint-cache. |
| `course/*/html/`, `course/*/text/` | Groot en mogelijk auteursrechtelijk gevoelig (ruwe Coursera-content). |
| `_archive/` | Bewust buiten Git gehouden — oude/afgekeurde bestanden horen niet in de geschiedenis. |

Vastgelegd in `.gitignore` (let op: het patroon is `course/*/html/` — met een wildcard voor de
cursus-slug, niet `course/html/`).
