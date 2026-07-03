"""Vertaalt één module van één cursus naar de Daan-leerstijl (spoor 1, per-module).

Gebruik:
    python scripts/translate_module.py --course <slug> --module <nummer> [--dry-run]

Werkwijze (module-aware, geen per-les vertaling):
1. Laad de lessen van de gekozen module uit data/<slug>/learning_items.json,
   in de echte, verzamelde Coursera-volgorde (niet alfabetisch).
2. Match elke les aan zijn markdown-brontekst (course/<slug>/markdown/) en
   maak die schoon: video-lessen zijn soms gescrapet met de hele
   pagina-chrome (zijbalkmenu, transcript-knoppen, tijdstempels) er nog
   omheen — die ruis wordt verwijderd zodat alleen de echte inhoud naar het
   model gaat.
3. Print een pre-flight rapport (cursus, module, dekking, tokens). Bij te
   weinig dekking (<90%) stopt het script VOOR de eerste OpenAI-aanroep.
4. Fase 1 (1 aanroep, compact): het model krijgt per les alleen de titel +
   een korte inhoudspreview (niet de volledige tekst) en bepaalt zelf de
   leerstructuur — de eerste helft van prompts/daan_module_prompt.md
   ("Bepaal eerst de beste leerstructuur") — en wijst elk onderdeel expliciet
   bronlessen toe (welke lesnummers).
5. Fase 2 (N aanroepen, één per onderdeel): elk onderdeel krijgt de VOLLEDIGE
   tekst van precies de lessen die fase 1 eraan toewees, plus de complete
   outline (alleen titels, compact) als context voor verwijzingen naar
   eerdere/latere onderdelen. Als een onderdeel te veel bronlessen heeft om
   in één aanroep te passen, wordt het automatisch in kleinere stukken
   geschreven en samengevoegd (module-aware chunking, geen per-les vertaling
   — de indeling zelf blijft die van fase 1's outline).
6. De onderdelen worden samengevoegd tot één module-markdown-bestand.

Waarom niet gewoon de hele module in één aanroep? Dat was het eerste ontwerp
(zie git-historie), maar het account waarmee dit draait heeft een OpenAI
rate limit van 30.000 tokens/minuut voor gpt-4.1 — ruim onder de ~51.000
tokens die de volledige module + prompt vergde. Dat werd pas zichtbaar bij
de eerste echte aanroep (RateLimitError, vóór enige generatie — geen kosten
gemaakt) en is hierna opgelost door elke aanroep klein genoeg te maken,
niet door de leerstrategie te versimpelen tot per-les vertaling.

De prompt zelf (prompts/daan_module_prompt.md) wordt ongewijzigd gebruikt als
system-instructie in alle aanroepen.
"""

import argparse
import json
import re
import sys
import time

from openai import OpenAI, RateLimitError

import config
from scraping_utils import normalize_title, guess_module_title

MODEL = "gpt-4.1"
MIN_COVERAGE = 0.9  # onder deze dekking stopt het script vóór de OpenAI-aanroep
SAFE_INPUT_TOKENS = 20000  # ruime marge onder de 30.000 TPM-limiet van dit account
PREVIEW_CHARS = 500  # lengte van de les-preview die fase 1 te zien krijgt
CALL_PAUSE_SECONDS = 3  # kleine pauze tussen aanroepen, voorkomt TPM-opeenstapeling

TRAILING_FOOTER = re.compile(r"\nTranscriptie\nOpmerkingen\nBestanden\s*$")
LABEL_LINE = re.compile(r"^Speel video af vanaf[^\n]*\n", re.MULTILINE)
BARE_TIMESTAMP = re.compile(r"^\d+:\d+$", re.MULTILINE)
INSTRUCTION_HEADER = re.compile(r"Interactief transcript.*?(?=Speel video af vanaf)", re.DOTALL)

_tiktoken_enc = None


def count_tokens(text):
    global _tiktoken_enc
    if _tiktoken_enc is None:
        import tiktoken
        _tiktoken_enc = tiktoken.get_encoding("cl100k_base")
    return len(_tiktoken_enc.encode(text))


def clean_lesson_body(text, title):
    """Verwijdert Coursera-UI-ruis uit een gescrapete lespagina. Lessen zonder
    de video-transcript-marker ('Interactief transcript') worden alleen van
    eventuele YAML-frontmatter ontdaan, verder ongewijzigd."""
    marker = text.find("Interactief transcript")
    if marker == -1:
        if text.startswith("---"):
            end = text.find("---", 3)
            if end != -1:
                text = text[end + 3:]
        return text.strip()

    tail = text[marker:]
    tail = INSTRUCTION_HEADER.sub("", tail, count=1)
    tail = LABEL_LINE.sub("", tail)
    lines = [l for l in tail.split("\n") if not BARE_TIMESTAMP.match(l.strip())]
    tail = "\n".join(lines)
    tail = TRAILING_FOOTER.sub("", tail)
    tail = tail.replace("​", "").replace("\xa0", " ")
    tail = re.sub(r"[ \t]+", " ", tail)
    tail = re.sub(r"\n{2,}", "\n", tail).strip()
    return f"{title}\n\n{tail}"


def load_module_items(slug, module_number):
    items = json.loads(config.learning_items_json(slug).read_text(encoding="utf-8"))
    return [it for it in items if it.get("module") == module_number]


def match_and_clean(items, markdown_dir):
    md_norm = {normalize_title(f.stem): f for f in markdown_dir.glob("*.md")}
    matched, missing = [], []
    for item in items:
        title = item["title"].split("\n")[0].strip()
        f = md_norm.get(normalize_title(item["title"]))
        if f:
            cleaned = clean_lesson_body(f.read_text(encoding="utf-8"), title)
            matched.append({"title": title, "url": item["url"], "text": cleaned})
        else:
            missing.append(title)
    return matched, missing


def call_openai(client, prompt_text, user_text, usage_log, label, max_retries=4):
    """Wrapper met retry/backoff voor transiente rate-limit-fouten."""
    for attempt in range(1, max_retries + 1):
        try:
            response = client.responses.create(
                model=MODEL,
                input=[
                    {"role": "system", "content": prompt_text},
                    {"role": "user", "content": user_text},
                ],
            )
            usage_log.append((label, response.usage))
            time.sleep(CALL_PAUSE_SECONDS)
            return response.output_text
        except RateLimitError as e:
            if attempt == max_retries:
                raise
            wait = 20 * attempt
            print(f"   ⏳ rate limit geraakt (poging {attempt}/{max_retries}), {wait}s wachten... ({e})")
            time.sleep(wait)


def build_lesson_previews(lessons):
    lines = []
    for i, lesson in enumerate(lessons, 1):
        preview = lesson["text"][:PREVIEW_CHARS].replace("\n", " ")
        lines.append(f"Les {i}: {lesson['title']}\nPreview: {preview}...")
    return "\n\n".join(lines)


def parse_outline(text, total_lessons):
    """Parseert de fase-1-outline. Verwacht per onderdeel een titel, beschrijving
    en een 'Bronlessen: 1, 3, 5'-regel met lesnummers."""
    sections = []
    for block in re.split(r"^### Onderdeel:\s*", text, flags=re.MULTILINE)[1:]:
        lines = block.strip().split("\n")
        title = lines[0].strip()
        body_lines = lines[1:]
        source_lessons = []
        description_lines = []
        for line in body_lines:
            m = re.match(r"Bronlessen:\s*(.+)", line.strip(), re.IGNORECASE)
            if m:
                source_lessons = [int(n) for n in re.findall(r"\d+", m.group(1))]
            else:
                description_lines.append(line)
        description = "\n".join(description_lines).strip()
        source_lessons = [n for n in source_lessons if 1 <= n <= total_lessons]
        sections.append({"title": title, "description": description, "source_lessons": source_lessons})
    return sections


def phase1_outline(client, prompt_text, lessons, module_title, usage_log):
    previews = build_lesson_previews(lessons)
    wrapper = f"""Hieronder staan de titels en korte previews van alle lessen in module
"{module_title}", in de originele Coursera-volgorde. Je ziet nog niet de
volledige lesteksten — dat komt in een latere stap; nu gaat het alleen om de
structuur.

Voer ALLEEN de eerste fase van je instructies uit ("Bepaal eerst de beste
leerstructuur"): bepaal op basis van de titels en previews de beste leerroute
voor deze lezer, en groepeer onderwerpen die logisch bij elkaar horen.

Geef een indeling van 4 tot 8 samenhangende onderdelen waarin je deze module
zou uitleggen, in de volgorde waarin je ze zou behandelen. Elk bronles-nummer
(Les 1 t/m Les {len(lessons)}) moet in precies één onderdeel voorkomen — laat
niets weg.

Antwoord EXACT in dit format (platte tekst, geen JSON, geen andere tekst
ervoor of erna):

### Onderdeel: <titel>
Bronlessen: <lesnummers, komma-gescheiden, bv. 1, 2, 5>
<beschrijving, 2-4 zinnen: wat behandelt dit onderdeel en waarom in deze volgorde>

### Onderdeel: <titel>
Bronlessen: <lesnummers>
<beschrijving>

LESSEN:
{previews}
"""
    text = call_openai(client, prompt_text, wrapper, usage_log, "fase1-outline")
    return parse_outline(text, len(lessons))


def format_outline_summary(outline):
    return "\n".join(f"{i + 1}. {s['title']}" for i, s in enumerate(outline))


def write_section_body(client, prompt_text, lessons, outline, section_index, module_title, usage_log, part_label=""):
    section = outline[section_index]
    lesson_subset = [lessons[n - 1] for n in section["source_lessons"]] if section["source_lessons"] else []
    source_text = "\n\n---\n\n".join(f"### {l['title']}\n\n{l['text']}" for l in lesson_subset)
    outline_summary = format_outline_summary(outline)

    part_note = f" (deel {part_label})" if part_label else ""
    wrapper = f"""Je hebt module "{module_title}" geanalyseerd en de volgende leerroute bepaald:

{outline_summary}

Schrijf nu VOLLEDIG onderdeel {section_index + 1} van {len(outline)}: "{section['title']}"{part_note}.
Beschrijving van dit onderdeel: {section['description']}

Verwijs waar nuttig naar eerdere of latere onderdelen (zie de lijst hierboven),
zodat de samenhang van de hele module voelbaar blijft — dit onderdeel staat
niet op zichzelf. Gebruik uitsluitend kennis uit de bronlessen hieronder:
verzin geen feiten, tools of oefeningen die niet in de bron staan. Begin je
antwoord direct met de inhoud (geen titel-heading — die voeg ik zelf toe).

BRONLESSEN VOOR DIT ONDERDEEL:
{source_text}
"""
    label = f"fase2-onderdeel-{section_index + 1}" + (f"-{part_label}" if part_label else "")
    return call_openai(client, prompt_text, wrapper, usage_log, label)


def write_section_chunked(client, prompt_text, lessons, outline, section_index, module_title, usage_log):
    """Schrijft één outline-onderdeel. Als de bronlessen van dit onderdeel te
    groot zijn voor één veilige aanroep, wordt het onderdeel in kleinere
    lesnummer-batches opgeknipt en de resultaten samengevoegd — de indeling
    blijft die van fase 1, dit is geen aparte per-les vertaling."""
    section = outline[section_index]
    lesson_ids = section["source_lessons"]
    if not lesson_ids:
        return f"*(Geen bronlessen toegewezen aan dit onderdeel — overgeslagen.)*"

    prompt_tokens = count_tokens(prompt_text)

    def subset_tokens(ids):
        return sum(count_tokens(lessons[n - 1]["text"]) for n in ids) + prompt_tokens + 800

    if subset_tokens(lesson_ids) <= SAFE_INPUT_TOKENS:
        return write_section_body(client, prompt_text, lessons, outline, section_index, module_title, usage_log)

    # te groot: splits in de helft, herhaal recursief
    mid = len(lesson_ids) // 2
    batches = [lesson_ids[:mid], lesson_ids[mid:]]
    bodies = []
    for i, batch in enumerate(batches, 1):
        sub_section = dict(section)
        sub_section["source_lessons"] = batch
        sub_outline = list(outline)
        sub_outline[section_index] = sub_section
        label = f"{i}/{len(batches)}"
        print(f"      onderdeel te groot, deel {label} (lessen {batch}) ...")
        bodies.append(write_section_body(client, prompt_text, lessons, sub_outline, section_index, module_title, usage_log, part_label=label))
    return "\n\n".join(bodies)


def main():
    parser = argparse.ArgumentParser(description="Vertaal één module naar de Daan-leerstijl.")
    parser.add_argument("--course", required=True, help="cursus-slug, bv. microsoft-enterprise-product-management-fundamentals")
    parser.add_argument("--module", required=True, type=int, help="modulenummer, bv. 1")
    parser.add_argument("--dry-run", action="store_true", help="alleen het pre-flight-rapport tonen, geen OpenAI-aanroepen")
    args = parser.parse_args()

    slug = args.course
    module_number = args.module

    if not config.learning_items_json(slug).exists():
        raise SystemExit(f"Geen data/{slug}/learning_items.json gevonden.")

    prompt_text = config.DAAN_PROMPT_MD.read_text(encoding="utf-8")
    items = load_module_items(slug, module_number)

    if not items:
        raise SystemExit(f"Geen items met module={module_number} gevonden voor {slug}.")

    matched, missing = match_and_clean(items, config.markdown_dir(slug))
    module_title = guess_module_title(config.markdown_dir(slug), module_number) or f"Module {module_number}"

    tokens_source = sum(count_tokens(l["text"]) for l in matched)
    tokens_prompt = count_tokens(prompt_text)

    print("===== PRE-FLIGHT CHECK =====")
    print(f"Cursus:              {slug}")
    print(f"Module:               {module_number} — {module_title}")
    print(f"Items in module:      {len(items)}")
    print(f"Items met content:    {len(matched)}")
    print(f"Items ZONDER content: {len(missing)}")
    for m in missing:
        print("   -", m)
    print("Lesvolgorde (zoals verzameld, niet alfabetisch):")
    for i, lesson in enumerate(matched, 1):
        print(f"   {i}. {lesson['title']}")
    print(f"Tokens brontekst (hele module): {tokens_source}")
    print(f"Tokens systeemprompt:           {tokens_prompt}")
    print(f"Veilige input-limiet per aanroep: {SAFE_INPUT_TOKENS} (account-TPM-limiet: 30.000/min)")

    coverage = len(matched) / len(items) if items else 0
    print(f"\nDekking: {len(matched)}/{len(items)} = {coverage:.0%}")

    if coverage < MIN_COVERAGE:
        print(f"\n❌ STOP: dekking ({coverage:.0%}) onder de {MIN_COVERAGE:.0%}-drempel voor een")
        print("   betrouwbare volledige-modultest. Geen OpenAI-aanroep gedaan.")
        print("   Ontbrekende content hierboven; vul aan met save_current_lesson.py of")
        print("   download_course.py voor deze specifieke lessen, of kies een andere module.")
        sys.exit(1)

    if missing:
        print(f"\n⚠️  Dekking is {coverage:.0%} (>= {MIN_COVERAGE:.0%}), doorgaan met de {len(missing)} ontbrekende")
        print("   item(s) hierboven genoteerd — niet verzonnen, gewoon afwezig in de input.")

    if args.dry_run:
        print("\n(--dry-run: geen OpenAI-aanroepen gedaan)")
        return

    client = OpenAI()
    usage_log = []

    print("\n===== FASE 1: structuur bepalen (1 compacte OpenAI-aanroep) =====")
    outline = phase1_outline(client, prompt_text, matched, module_title, usage_log)

    if not outline:
        print("❌ STOP: kon geen outline parsen uit de fase-1-respons.")
        sys.exit(1)

    covered = {n for s in outline for n in s["source_lessons"]}
    all_ids = set(range(1, len(matched) + 1))
    unassigned = sorted(all_ids - covered)

    print(f"Outline: {len(outline)} onderdelen")
    for s in outline:
        print(f"   - {s['title']}  (bronlessen: {s['source_lessons']})")
    if unassigned:
        print(f"⚠️  Lessen die het model aan geen enkel onderdeel toewees: {unassigned}")
        print("   Deze worden als los onderdeel toegevoegd zodat er niets verloren gaat.")
        outline.append({
            "title": "Overige onderwerpen",
            "description": "Lessen die niet expliciet in een onderdeel hierboven ondergebracht waren.",
            "source_lessons": unassigned,
        })

    print(f"\n===== FASE 2: onderdelen schrijven (max {len(outline)} aanroepen, meer bij automatisch opsplitsen) =====")
    section_bodies = []
    for i in range(len(outline)):
        print(f"   [{i + 1}/{len(outline)}] {outline[i]['title']} ...")
        body = write_section_chunked(client, prompt_text, matched, outline, i, module_title, usage_log)
        section_bodies.append(body)

    final_md = f"# {module_title}\n\n"
    for section, body in zip(outline, section_bodies):
        final_md += f"## {section['title']}\n\n{body.strip()}\n\n"

    out_dir = config.translated_dir(slug)
    out_dir.mkdir(parents=True, exist_ok=True)
    module_slug = f"module-{module_number}"
    out_path = out_dir / f"{module_slug}.md"
    out_path.write_text(final_md.strip() + "\n", encoding="utf-8")

    total_input = sum(u.input_tokens for _, u in usage_log)
    total_output = sum(u.output_tokens for _, u in usage_log)
    print("\n===== KLAAR =====")
    print(f"Opgeslagen: {out_path}")
    print(f"Aantal OpenAI-aanroepen: {len(usage_log)}")
    for label, usage in usage_log:
        print(f"   {label}: input={usage.input_tokens}, output={usage.output_tokens}")
    print(f"Totaal input tokens:  {total_input}")
    print(f"Totaal output tokens: {total_output}")
    # gpt-4.1 prijzen: $2.00 / 1M input, $8.00 / 1M output (OpenAI, april 2025)
    cost = (total_input / 1_000_000) * 2.00 + (total_output / 1_000_000) * 8.00
    print(f"Geschatte kosten (gpt-4.1: $2/1M input, $8/1M output): ${cost:.4f}")


if __name__ == "__main__":
    main()
