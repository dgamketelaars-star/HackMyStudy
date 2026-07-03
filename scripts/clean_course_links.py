"""Filtert data/<slug>/course_links.json tot echte leer-items.

Draait over alle cursussen waarvoor course_links.json bestaat (batch) — geen
argumenten nodig. Zie PIPELINE.md voor waar dit script in de pipeline past.
"""

import json

import config

LEARNING_TYPES = [
    "/supplement/",
    "/lecture/",
    "/coach/",
    "/discussionPrompt/",
    "/assignment-submission/",
]


def clean_course(slug):
    links = json.loads(config.course_links_json(slug).read_text(encoding="utf-8"))

    cleaned = []
    for item in links:
        url = item["url"]
        title = item["title"].strip()

        if any(t in url for t in LEARNING_TYPES):
            cleaned.append({
                "title": title,
                "url": url
            })

    config.learning_items_json(slug).write_text(
        json.dumps(cleaned, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return cleaned


if __name__ == "__main__":
    slugs = [s for s in config.known_course_slugs() if config.course_links_json(s).exists()]

    if not slugs:
        print("Geen enkele data/<slug>/course_links.json gevonden. Draai eerst collect-links.")

    for slug in slugs:
        cleaned = clean_course(slug)
        print(f"✅ {slug}: {len(cleaned)} leer-items")
