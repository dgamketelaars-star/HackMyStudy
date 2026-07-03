"""Publiceert de manifest + vertaalde lessen naar docs/, zodat de (statische,
via GitHub Pages gehoste) webapp ze kan tonen.

docs/ is de enige map die GitHub Pages serveert — content in data/ of course/
is daar niet vanaf bereikbaar. Dit script kopieert dus welbewust:
- data/manifest.json          -> docs/content/manifest.json
- course/<slug>/translated/*  -> docs/content/<slug>/*

Bevat geen ruwe scrape-data (html/text) en geen browser-/sessiebestanden —
alleen het manifest en al-vertaalde lesmarkdown.
"""

import json
import shutil

import config


def publish():
    if not config.MANIFEST_JSON.exists():
        raise SystemExit(f"{config.MANIFEST_JSON} bestaat niet. Draai eerst build_manifest.py.")

    config.DOCS_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config.MANIFEST_JSON, config.DOCS_MANIFEST_JSON)

    manifest = json.loads(config.MANIFEST_JSON.read_text(encoding="utf-8"))

    published = 0
    for course in manifest["courses"]:
        slug = course["slug"]
        src_dir = config.translated_dir(slug)
        dest_dir = config.DOCS_CONTENT_DIR / slug

        translated_lessons = [l for l in course["lessons"] if l["translated"]]
        if not translated_lessons:
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)
        for lesson in translated_lessons:
            src = src_dir / f"{lesson['slug']}.md"
            dest = dest_dir / f"{lesson['slug']}.md"
            shutil.copyfile(src, dest)
            published += 1

    return published


if __name__ == "__main__":
    count = publish()
    print(f"✅ manifest gepubliceerd naar {config.DOCS_MANIFEST_JSON}")
    print(f"✅ {count} vertaalde les(sen) gepubliceerd naar docs/content/")
