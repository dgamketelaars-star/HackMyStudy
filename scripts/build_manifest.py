"""Bouwt data/manifest.json: het overzicht van alle 5 cursussen en hun
modules dat de webapp gebruikt om te tonen wat er is en wat nog niet.

De vertaalstap werkt op moduleniveau (spoor 1, per-module — zie
translate_module.py en PIPELINE.md), dus de webapp navigeert ook op
moduleniveau: cursus -> module -> lezen. Niet cursus -> losse les.

Voor elke cursus in data/courses.json:
- status "available" als er een learning_items.json met lessen is;
- status "coming_soon" als die cursus nog niet verzameld is.

Voor elke module: hoeveel lessen erin zitten en of er al een vertaalde
versie bestaat in course/<slug>/translated/module-<N>.md.

Draai dit na elke wijziging aan de brondata; run.py publish-docs kopieert het
resultaat daarna naar docs/ zodat de (statische) webapp het kan lezen.
"""

import json
from collections import defaultdict

import config
from scraping_utils import guess_module_title


def build_course_entry(course):
    slug = course["slug"]
    items_file = config.learning_items_json(slug)

    if not items_file.exists():
        return {
            "slug": slug,
            "title": course["title"],
            "status": "coming_soon",
            "modules": []
        }

    items = json.loads(items_file.read_text(encoding="utf-8"))
    markdown_dir = config.markdown_dir(slug)
    translated_dir = config.translated_dir(slug)

    lessons_by_module = defaultdict(list)
    for item in items:
        module_number = item.get("module")
        if module_number is not None:
            lessons_by_module[module_number].append(item)

    modules = []
    for module_number in sorted(lessons_by_module):
        lesson_count = len(lessons_by_module[module_number])
        title = guess_module_title(markdown_dir, module_number) or f"Module {module_number}"
        translated_file = translated_dir / f"module-{module_number}.md"

        modules.append({
            "number": module_number,
            "title": title,
            "lesson_count": lesson_count,
            "translated": translated_file.exists()
        })

    return {
        "slug": slug,
        "title": course["title"],
        "status": "available",
        "modules": modules
    }


def build_manifest():
    courses = config.load_courses()
    manifest = {
        "courses": [build_course_entry(c) for c in courses]
    }
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.MANIFEST_JSON.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    manifest = build_manifest()
    for c in manifest["courses"]:
        translated_count = sum(1 for m in c["modules"] if m["translated"])
        print(f"{c['status']:12} {c['slug']:55} {len(c['modules']):2} modules, {translated_count} vertaald")
    print(f"\n✅ Opgeslagen: {config.MANIFEST_JSON}")
