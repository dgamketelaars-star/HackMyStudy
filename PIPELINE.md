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
11.910 output-tokens, gpt-4.1: $2/1M input, $8/1M output). De hergeneratie na de vier upgrades
hieronder (visuals + progressive terminology immersion) kostte vergelijkbaar weinig — zie de
git-commit van die run voor het exacte bedrag. `translate_module.py` print na afloop altijd het
exacte tokengebruik en de geschatte kosten per aanroep.

**Nog niet gedaan:** cursussen 2-5 en de overige modules van cursus 1 zijn nog niet vertaald — dat
is een bewuste stop, geen technische beperking (zie de opdracht: exact één module als eerste test,
voor inhoudelijke beoordeling voordat er meer vertaald wordt).

## Visuals (Mermaid + tabellen)

`prompts/daan_module_prompt.md` instrueert het model om alléén een visual toe te voegen wanneer die
de cognitieve weerstand echt verlaagt (processen, cycli, hiërarchieën, concept maps, vergelijkingen)
— nooit decoratief. Diagrammen worden als ` ```mermaid ` -codeblok in de module-markdown gezet;
vergelijkingen als gewone Markdown-tabel.

De webapp (`docs/js/visuals.js`) rendert dit: marked.js zet een ` ```mermaid `-blok om in
`<pre><code class="language-mermaid">`, wat `renderVisuals()` omzet naar het `<div class="mermaid">`
dat Mermaid zelf verwacht, waarna `mermaid.run()` het tekent (donker thema, past bij de site).
Markdown-tabellen hebben geen speciale behandeling nodig — marked.js rendert ze al als `<table>`;
`docs/css/style.css` stylet ze (horizontaal scrollbaar op mobiel, geen tabel die het scherm afbreekt).

Bewust buiten scope voor nu: echte tool-interface-"screenshots". Dat zou ofwel een betaalde
image-generation-API vergen (niet toegestaan zonder toestemming) ofwel een LLM die betrouwbaar
HTML/CSS-mockups van specifieke tools natekent (te fragiel om nu te vertrouwen). De prompt
instrueert het model expliciet om dat niet te proberen.

## Progressive English terminology immersion

`data/term_familiarity.json` is de cursusoverstijgende ledger: per vakterm (Engelse term als key)
staat de Nederlandse vertaling, de huidige status (`nieuw` / `in_opbouw` / `bekend`), hoe vaak hij
al gebruikt is, en in welke module(s). Elke fase-2-aanroep in `translate_module.py` krijgt deze
ledger als tekst mee in de prompt, en levert zelf een `===TERMEN===`-blok terug met welke termen
gebruikt zijn en in welke status — `parse_and_strip_terms()` haalt dat blok eruit (de lezer ziet
het nooit), `apply_term_updates()` verwerkt het in de ledger, die na de hele module-run wordt
opgeslagen.

Bewust géén mechanische regel ("na 3 keer altijd Engels"): de prompt instrueert het model om zelf
te beoordelen of de overgang hier natuurlijk aanvoelt, gebaseerd op complexiteit/belang van de term
— expliciet gevraagd in de opdracht. De ledger is de *herinnering*, niet de beslisser.

Omdat de ledger cursusoverstijgend is (niet per cursus, laat staan per module), bouwt elke nieuw
vertaalde module voort op wat eerder al écht gegenereerd is — niet op wat toevallig al bestond vóór
deze upgrade. Cursus 1 module 1 had vóór de hergeneratie nul Engelse vaktermen; na de hergeneratie
staat de ledger aan het begin van zijn opbouw, en elke volgende module (2-5, of cursus 2-5) bouwt
daarop voort.

## Luistermodus (audio)

Browser-native Web Speech API (`SpeechSynthesis`), bewust gekozen boven een betaalde TTS-dienst:
gratis, werkt in vrijwel elke moderne mobiele en desktopbrowser, vereist geen server (dus compatibel
met GitHub Pages als statische site), stuurt niets naar een nieuwe derde partij, en heeft geen
onderhoud nodig. Zie "Bekende beperkingen" hieronder voor de reële nadelen van deze keuze.

`docs/js/audio.js` bevat de speech-preparation-laag (`prepareForSpeech()`): verwijdert
TOOLVERKENNING-markers (de inhoud eromheen blijft gewoon staan), vervangt Mermaid-blokken en
tabellen door een korte gesproken verwijzing ("Zie het schema/de tabel in de tekst" — die worden
niet letterlijk voorgelezen), en strip alle Markdown-opmaaktekens. Geverifieerd tegen de echte
module-1-tekst: geen `===`, `##`, `**`, code-fences of tabel-pipes overleven het, en de tekst blijft
inhoudelijk vrijwel compleet (~4% korter, puur opmaak-overhead).

De schone tekst wordt in zinsgerichte stukken van max ~220 tekens geknipt (`splitIntoSpeechChunks`)
en sequentieel afgespeeld via `SpeechSynthesisUtterance`. Bediening: play/pause, snelheid
(0,75×-2×), "↺15" en automatisch onthouden waar je gebleven bent (`localStorage`, per
cursus+module).

**Bekende beperkingen (eerlijk, niet verzwegen):**
- **"↺15 seconden" is een schatting**, geen frame-accurate terugspoelen — de Web Speech API geeft
  geen echte afspeelpositie, alleen `onboundary`-events. De schatting gebruikt een vaste
  tekens-per-seconde-aanname (gecorrigeerd voor de ingestelde snelheid).
- **Stemkwaliteit en -beschikbaarheid voor Nederlands verschilt per apparaat/besturingssysteem**
  (iOS gebruikt Siri-stemmen, Android de Google-TTS-stemmen, sommige Linux-browsers hebben geen
  Nederlandse stem). Zonder Nederlandse stem valt de browser terug op zijn standaardstem.
- Sommige browsers pauzeren `speechSynthesis` als het tabblad lang op de achtergrond staat — een
  bekende browser-eigenaardigheid, niet iets wat vanuit JavaScript op te lossen is.
- Niet getest op een echt mobiel toestel (alleen headless Chromium) — zie "Wat jij nu moet testen"
  in het eindrapport.

## Interactief vragen

De vertaalde tekst stelt regelmatig een directe vraag ("Snap je waarom...?") zonder dat de lezer
daar iets mee kon — dat is nu opgelost met een altijd-beschikbaar vragenpaneel tijdens het lezen
(`docs/js/qa.js`): een zwevende knop opent een paneel met drie snelle acties (leg verder uit / geef
een praktijkvoorbeeld / leg visueel uit) plus een vrij tekstveld.

**Context die wordt meegestuurd:** cursustitel, moduletitel, en — via een `IntersectionObserver` op
de `<h2>`-koppen — alleen de tekst van het onderdeel waar de lezer waarschijnlijk nu leest (niet de
hele module: dat zou nodeloos veel tokens kosten voor een vraag die meestal over het huidige
onderdeel gaat), plus de laatste paar berichten van het gesprek voor vervolgvragen.

**Waarom dit niet zomaar naar OpenAI belt vanuit de browser:** `docs/` is een statische GitHub
Pages-site zonder server — een API-key in het gepubliceerde JavaScript zou voor iedereen die de
site bezoekt uitleesbaar zijn. Dat probleem was al gedocumenteerd vóór deze upgrade en blijft
onveranderd waar.

**Wat nu wél werkt, zonder nieuw account:** `scripts/qa_server.py` is een lokale
(127.0.0.1-only, dus nooit vanaf het netwerk bereikbaar) server die dezelfde `OPENAI_API_KEY`
hergebruikt als de vertaalpipeline. Draai je deze terwijl je lokaal leest, dan werkt het
vragenpaneel volledig — geverifieerd met een echte aanroep (zie eindrapport). De webapp probeert
dit endpoint automatisch (met een timeout van 1,2s) en toont een eerlijke melding als de server niet
draait, in plaats van een nep-antwoord.

**Wat nog een echte keuze van jou vereist (niet zelf gedaan — nieuw account + credentials):**
lezen op je telefoon, onderweg, vereist een gehoste backend (de lokale server is dan niet
bereikbaar). `deploy/cloudflare-worker-qa.js` is klaar om te deployen zodra je dat wilt — zie de
instructies bovenin dat bestand. Dit is bewust niet zelf aangemaakt/geactiveerd.

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
