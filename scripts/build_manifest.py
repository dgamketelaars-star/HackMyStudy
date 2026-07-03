"""Bouwt data/manifest.json: het overzicht van alle 5 cursussen en hun lessen
dat de webapp gebruikt om te tonen wat er is en wat nog niet.

Voor elke cursus in data/courses.json:
- status "available" als er een learning_items.json met lessen is;
- status "coming_soon" als die cursus nog niet verzameld is.

Voor elke les: of er al vertaalde content bestaat in course/<slug>/translated/
(zie PIPELINE.md — die map is nu leeg, de vertaalstap moet nog gebeuren).

Draai dit na elke wijziging aan de brondata; run.py publish-docs kopieert het
resultaat daarna naar docs/ zodat de (statische) webapp het kan lezen.
"""

import json

import config
from scraping_utils import slugify


def build_course_entry(course):
    slug = course["slug"]
    items_file = config.learning_items_json(slug)
    translated_dir = config.translated_dir(slug)

    if not items_file.exists():
        return {
            "slug": slug,
            "title": course["title"],
            "status": "coming_soon",
            "lessons": []
        }

    items = json.loads(items_file.read_text(encoding="utf-8"))

    lessons = []
    seen_slugs = {}
    for order, item in enumerate(items, start=1):
        title = item["title"].split("\n")[0].strip()
        lesson_slug = slugify(title) or f"les-{order}"

        # zorg voor unieke slugs als twee titels toevallig hetzelfde normaliseren
        if lesson_slug in seen_slugs:
            seen_slugs[lesson_slug] += 1
            lesson_slug = f"{lesson_slug}-{seen_slugs[lesson_slug]}"
        else:
            seen_slugs[lesson_slug] = 1

        translated_file = translated_dir / f"{lesson_slug}.md"

        lessons.append({
            "slug": lesson_slug,
            "title": title,
            "module": item.get("module"),
            "order": order,
            "translated": translated_file.exists()
        })

    return {
        "slug": slug,
        "title": course["title"],
        "status": "available",
        "lessons": lessons
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
        translated_count = sum(1 for lesson in c["lessons"] if lesson["translated"])
        print(f"{c['status']:12} {c['slug']:55} {len(c['lessons']):3} lessen, {translated_count} vertaald")
    print(f"\n✅ Opgeslagen: {config.MANIFEST_JSON}")
