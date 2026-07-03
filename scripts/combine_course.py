"""Voegt alle markdown-lessen van een cursus samen tot één ruw bestand.

Batcht over elke cursus die course/<slug>/markdown/ heeft. De lessen worden
gesorteerd op de echte Coursera-volgorde uit data/<slug>/learning_items.json
(gematcht op genormaliseerde titel), niet alfabetisch op bestandsnaam — de
oude versie (combine_course_1.py) sorteerde per ongeluk alfabetisch, wat de
lesvolgorde door elkaar gooide. Cursussen zonder learning_items.json (of met
lessen die niet te matchen zijn) vallen terug op alfabetisch, met een
duidelijke waarschuwing.
"""

import json

import config
from scraping_utils import normalize_title


def ordered_files(slug):
    md_dir = config.markdown_dir(slug)
    files = sorted(md_dir.glob("*.md"))

    items_file = config.learning_items_json(slug)
    if not items_file.exists():
        print(f"⚠️  {slug}: geen learning_items.json, val terug op alfabetische volgorde")
        return files

    items = json.loads(items_file.read_text(encoding="utf-8"))
    by_title = {normalize_title(f.stem): f for f in files}

    ordered = []
    used = set()
    unmatched_items = []
    for item in items:
        key = normalize_title(item["title"])
        match = by_title.get(key)
        if match:
            ordered.append(match)
            used.add(match)
        else:
            unmatched_items.append(item["title"].split("\n")[0].strip())

    # bestanden die niet aan een leer-item te koppelen waren, alsnog achteraan toevoegen
    leftover = [f for f in files if f not in used]

    if unmatched_items:
        print(f"⚠️  {slug}: {len(unmatched_items)} leer-item(s) zonder markdown-bestand (waarschijnlijk niet gescraped):")
        for title in unmatched_items:
            print("   -", title)
    if leftover:
        print(f"⚠️  {slug}: {len(leftover)} markdown-bestand(en) niet in learning_items.json, achteraan toegevoegd:")
        for f in leftover:
            print("   -", f.name)

    return ordered + leftover


def combine_course(slug):
    files = ordered_files(slug)

    parts = []
    for file in files:
        text = file.read_text(encoding="utf-8")
        parts.append(f"\n\n---\n\n# FILE: {file.name}\n\n{text}")

    config.raw_md(slug).write_text("\n".join(parts), encoding="utf-8")
    return len(files)


if __name__ == "__main__":
    slugs = sorted(
        p.name for p in config.COURSE_DIR.iterdir()
        if p.is_dir() and config.markdown_dir(p.name).exists()
    ) if config.COURSE_DIR.exists() else []

    if not slugs:
        print("Geen enkele course/<slug>/markdown/ gevonden. Draai eerst download-course of save-lesson.")

    for slug in slugs:
        count = combine_course(slug)
        print(f"✅ {slug}: {count} bestanden samengevoegd -> {config.raw_md(slug)}")
