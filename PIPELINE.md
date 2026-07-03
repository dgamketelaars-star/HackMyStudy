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
   tegen learning_items.json — niet alfabetisch). Dit bestand is vooral
   nuttig als overzicht; de vertaalstap (7) leest de lessen los in.
   Output: course/<slug>/raw.md

7. python run.py translate-module -- --course <slug> --module <n> [--dry-run]
   Vertaalt ÉÉN module naar de Daan-leerstijl via OpenAI — zie
   "De vertaalstap" hieronder voor hoe dit werkt en waarom. Kost echt geld
   (klein bedrag, zie hieronder); --dry-run laat alleen het pre-flight-
   rapport zien zonder aan te roepen.
   Output: course/<slug>/translated/module-<n>.md

8. python run.py build-manifest
   Output: data/manifest.json — wat de webapp laat zien, nu op moduleniveau.

9. python run.py publish-docs
   Kopieert manifest + vertaalde modules naar docs/content/.
```

Stap 1-2 zijn maar één keer nodig per keer dat je alle 5 cursussen wilt verzamelen; stap 3-6
kun je per cursus of in bulk draaien; stap 7 draai je bewust per module (zie hieronder — geen
batchvertaling); stap 8-9 draai je opnieuw zodra er nieuwe vertaalde content is.

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

## De vertaalstap

`scripts/translate_module.py` is de echte vertaalstap: **per module**, niet per losse les — dat
is een bewuste productkeuze (niet de standaard "vat elke les apart samen"-aanpak), omdat de
prompt om samenhang over lessen heen vraagt ("Lees de volledige module... Bepaal eerst de beste
leerstructuur"). `scripts/generate_module.py` blijft bestaan als de oorspronkelijke
proof-of-concept (eerste 15.000 tekens van een hele cursus, niet module-bewust) maar is niet meer
de aanbevolen route.

De prompt zelf ([prompts/daan_module_prompt.md](prompts/daan_module_prompt.md)) wordt in élke
OpenAI-aanroep ongewijzigd als system-instructie gebruikt — er wordt nooit stilzwijgend aan de
leerstrategie gesleuteld.

**Werkwijze (module-aware, geen per-les vertaling):**

1. **Pre-flight check** (altijd, ook bij `--dry-run`): welke cursus/module, hoeveel lessen erin
   zitten, welke daarvan content hebben, welke ontbreken, de lesvolgorde, en het geschatte
   tokengebruik. Onder 90% dekking stopt het script vóór de eerste aanroep.
2. **Video-content opschonen.** Lessen die via `download_course.py`/`save_current_lesson.py`
   gescraped zijn, bevatten voor video's soms de hele pagina (zijbalkmenu, transcript-knoppen,
   tijdstempels) omdat de specifieke content-selector niet matchte en op de volledige paginatekst
   is teruggevallen. Ongefilterd zou dat niet alleen tokens verspillen, maar het model ook de
   titels van *andere* modules laten zien alsof die bij de huidige module horen. Een regex-cleaner
   isoleert het echte transcript (gevonden en geverifieerd tegen alle 9 video-lessen van module 1
   van cursus 1).
3. **Fase 1 — structuur bepalen** (1 compacte aanroep): het model krijgt per les alleen de titel +
   een korte preview (niet de volledige tekst) en voert het eerste deel van de prompt uit
   ("Bepaal eerst de beste leerstructuur"): het bedenkt 4-8 samenhangende onderdelen en wijst elke
   bronles expliciet aan een onderdeel toe.
4. **Fase 2 — onderdelen schrijven** (één aanroep per onderdeel): elk onderdeel krijgt de
   volledige tekst van precies de lessen die fase 1 eraan toewees, plus de complete outline (titels
   only) zodat het naar eerdere/latere onderdelen kan verwijzen. Is een onderdeel te groot voor één
   veilige aanroep, dan wordt het automatisch in kleinere lesnummer-batches opgesplitst en
   samengevoegd — de indeling blijft die van fase 1, dit is nog steeds geen per-les vertaling.
5. De onderdelen worden samengevoegd tot één module-markdown-bestand:
   `course/<slug>/translated/module-<n>.md`.

**Waarom niet gewoon de hele module in één aanroep?** Dat was het eerste ontwerp. Bij de eerste
echte aanroep (module 1, cursus 1, ~50.000 tokens brontekst + prompt) gaf OpenAI meteen een
`RateLimitError`: dit account heeft een limiet van **30.000 tokens/minuut** voor gpt-4.1 — ver
onder wat één aanroep met de hele module nodig had. Er was op dat moment nog niets gegenereerd,
dus geen kosten. Het ontwerp is daarna herzien naar de fase-1/fase-2-aanpak hierboven, waarbij elke
aanroep ruim onder een veilige 20.000-token-grens blijft.

**Kosten:** de eerste echte run (module 1, cursus 1: 20 lessen, 5 aanroepen — 1 outline + 4
onderdelen, geen enkel onderdeel hoefde verder opgesplitst) kostte **$0,19** (46.181 input- +
11.910 output-tokens, gpt-4.1: $2/1M input, $8/1M output). `translate_module.py` print na afloop
altijd het exacte tokengebruik en de geschatte kosten per aanroep.

**Nog niet gedaan:** cursussen 2-5 en de overige modules van cursus 1 zijn nog niet vertaald — dat
is een bewuste stop, geen technische beperking (zie de opdracht: exact één module als eerste test,
voor inhoudelijke beoordeling voordat er meer vertaald wordt).

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

`course/<slug>/translated/*.md` is **geen** tijdelijk bestand — dat is de daadwerkelijke
HackMyStudy-content (het resultaat van de OpenAI-vertaalstap) en hoort dus wél in Git, net als
`course/<slug>/markdown/` (de brontekst).

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
