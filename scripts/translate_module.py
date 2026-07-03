"""Vertaalt één module van één cursus naar de Daan-leerstijl (spoor 1, per-module).

Gebruik:
    python scripts/translate_module.py --course <slug> --module <nummer>

Werkwijze (module-aware, geen per-les vertaling):
1. Laad de lessen van de gekozen module uit data/<slug>/learning_items.json,
   in de echte, verzamelde Coursera-volgorde (niet alfabetisch).
2. Match elke les aan zijn markdown-brontekst (course/<slug>/markdown/) en
   maak die schoon: Coursera scrapet video-lessen soms met de hele
   pagina-chrome (zijbalkmenu, transcript-knoppen, tijdstempels) er nog
   omheen — die ruis wordt hier verwijderd zodat alleen de echte inhoud naar
   het model gaat.
3. Print een pre-flight rapport: welke cursus/module, hoeveel lessen, welke
   content ontbreekt, hoeveel tokens er naar het model gaan. Bij te weinig
   dekking (<90%) stopt het script VOOR de OpenAI-aanroep.
4. Fase 1 (1 aanroep): het model leest de VOLLEDIGE module en bepaalt zelf de
   leerstructuur — dit is letterlijk de eerste helft van
   prompts/daan_module_prompt.md ("Bepaal eerst de beste leerstructuur"),
   nu als los, herbruikbaar tussenresultaat.
5. Fase 2 (N aanroepen, één per onderdeel uit de outline): elk onderdeel
   wordt geschreven met de VOLLEDIGE module-inhoud + de hele outline als
   context, zodat elk onderdeel weet wat ervoor en erna komt. Dit is nodig
   omdat de module (~50k tokens brontekst) een output kan opleveren die
   groter is dan de outputlimiet van één modelaanroep — zie PIPELINE.md.
   Dit is GEEN per-les vertaling: de indeling in onderdelen wordt door het
   model zelf bepaald op basis van de hele module, niet door de originele
   Coursera-lesgrenzen.
6. De onderdelen worden samengevoegd tot één module-markdown-bestand.

De prompt zelf (prompts/daan_module_prompt.md) wordt ongewijzigd gebruikt als
system-instructie in zowel fase 1 als fase 2.
"""

import argparse
import json
import re
import sys

from openai import OpenAI

import config
from scraping_utils import normalize_title

MODEL = "gpt-4.1"
MIN_COVERAGE = 0.9  # onder deze dekking stopt het script vóór de OpenAI-aanroep

TRAILING_FOOTER = re.compile(r"\nTranscriptie\nOpmerkingen\nBestanden\s*$")
LABEL_LINE = re.compile(r"^Speel video af vanaf[^\n]*\n", re.MULTILINE)
BARE_TIMESTAMP = re.compile(r"^\d+:\d+$", re.MULTILINE)
INSTRUCTION_HEADER = re.compile(r"Interactief transcript.*?(?=Speel video af vanaf)", re.DOTALL)
MODULE_TITLE_PATTERN = re.compile(r"Module (\d)\n([^\n]+)\n")


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


def guess_module_title(slug, module_number):
    """Zoekt de echte moduletitel in het zijbalkmenu dat in sommige (video-)
    scrapes is meegekomen. Valt terug op 'Module N' als niets gevonden wordt."""
    for f in config.markdown_dir(slug).glob("*.md"):
        text = f.read_text(encoding="utf-8")
        for match in MODULE_TITLE_PATTERN.finditer(text):
            if int(match.group(1)) == module_number:
                return match.group(2).strip()
    return f"Module {module_number}"


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


def build_module_source(lessons):
    parts = [f"## Les {i}: {l['title']}\n\n{l['text']}" for i, l in enumerate(lessons, 1)]
    return "\n\n---\n\n".join(parts)


def parse_outline(text):
    sections = []
    for block in re.split(r"^### Onderdeel:\s*", text, flags=re.MULTILINE)[1:]:
        lines = block.strip().split("\n", 1)
        title = lines[0].strip()
        description = lines[1].strip() if len(lines) > 1 else ""
        sections.append({"title": title, "description": description})
    return sections


def phase1_outline(client, prompt_text, source_text, module_title, usage_log):
    wrapper = f"""Hieronder staat de VOLLEDIGE inhoud van module "{module_title}", in de
originele Coursera-volgorde, les voor les.

Voer ALLEEN de eerste fase van je instructies uit ("Bepaal eerst de beste
leerstructuur"): lees de hele module, bepaal de beste leerroute voor deze
lezer, en groepeer onderwerpen die logisch bij elkaar horen.

Geef nu NOG GEEN volledige lestekst terug. Geef een genummerde indeling van
4 tot 8 samenhangende onderdelen waarin je deze module zou uitleggen, in de
volgorde waarin je ze zou behandelen. Voor elk onderdeel: een titel, en een
korte beschrijving (2-4 zinnen) van wat het behandelt en welke bronlessen
erin verwerkt worden.

Antwoord EXACT in dit format (platte tekst, geen JSON, geen andere tekst
ervoor of erna):

### Onderdeel: <titel>
<beschrijving>

### Onderdeel: <titel>
<beschrijving>

MODULE-INHOUD:
{source_text}
"""
    response = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": prompt_text},
            {"role": "user", "content": wrapper},
        ],
    )
    usage_log.append(("fase1-outline", response.usage))
    return response.output_text


def phase2_write_section(client, prompt_text, source_text, outline, section_index, module_title, usage_log):
    outline_text = "\n".join(f"{i + 1}. {s['title']}: {s['description']}" for i, s in enumerate(outline))
    section = outline[section_index]
    wrapper = f"""Je hebt module "{module_title}" al gelezen en de volgende leerroute bepaald:

{outline_text}

Schrijf nu VOLLEDIG onderdeel {section_index + 1} van {len(outline)}: "{section['title']}".
Beschrijving van dit onderdeel: {section['description']}

Verwijs waar nuttig naar eerdere of latere onderdelen, zodat de samenhang van
de hele module voelbaar blijft — dit onderdeel staat niet op zichzelf. Gebruik
uitsluitend kennis uit de bronlessen hieronder: verzin geen feiten, tools of
oefeningen die niet in de bron staan. Begin je antwoord direct met de inhoud
(geen titel-heading — die voeg ik zelf toe).

VOLLEDIGE MODULE-INHOUD (voor context, ook al schrijf je nu maar dit onderdeel):
{source_text}
"""
    response = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": prompt_text},
            {"role": "user", "content": wrapper},
        ],
    )
    usage_log.append((f"fase2-onderdeel-{section_index + 1}", response.usage))
    return response.output_text


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
    module_title = guess_module_title(slug, module_number)
    source_text = build_module_source(matched)

    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    tokens_source = len(enc.encode(source_text))
    tokens_prompt = len(enc.encode(prompt_text))

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
    print(f"Tokens brontekst (module): {tokens_source}")
    print(f"Tokens systeemprompt:      {tokens_prompt}")
    print(f"Geschat input per fase-2-aanroep: ~{tokens_source + tokens_prompt + 500}")

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

    print("\n===== FASE 1: structuur bepalen (1 OpenAI-aanroep) =====")
    outline_text = phase1_outline(client, prompt_text, source_text, module_title, usage_log)
    outline = parse_outline(outline_text)

    if not outline:
        print("❌ STOP: kon geen outline parsen uit de fase-1-respons. Ruwe respons:")
        print(outline_text[:2000])
        sys.exit(1)

    print(f"Outline: {len(outline)} onderdelen")
    for s in outline:
        print(f"   - {s['title']}")

    print(f"\n===== FASE 2: onderdelen schrijven ({len(outline)} OpenAI-aanroepen) =====")
    section_bodies = []
    for i in range(len(outline)):
        print(f"   [{i + 1}/{len(outline)}] {outline[i]['title']} ...")
        body = phase2_write_section(client, prompt_text, source_text, outline, i, module_title, usage_log)
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
