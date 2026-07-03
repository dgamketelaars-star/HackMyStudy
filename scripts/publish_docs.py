"""Publiceert de manifest + vertaalde modules naar docs/, zodat de (statische,
via GitHub Pages gehoste) webapp ze kan tonen.

docs/ is de enige map die GitHub Pages serveert — content in data/ of course/
is daar niet vanaf bereikbaar. Dit script kopieert dus welbewust:
- data/manifest.json                   -> docs/content/manifest.json
- course/<slug>/translated/module-N.md -> docs/content/<slug>/module-N.md

Bevat geen ruwe scrape-data (html/text) en geen browser-/sessiebestanden —
alleen het manifest en al-vertaalde modulemarkdown.
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

        translated_modules = [m for m in course["modules"] if m["translated"]]
        if not translated_modules:
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)
        for module in translated_modules:
            filename = f"module-{module['number']}.md"
            shutil.copyfile(src_dir / filename, dest_dir / filename)
            published += 1

    return published


if __name__ == "__main__":
    count = publish()
    print(f"✅ manifest gepubliceerd naar {config.DOCS_MANIFEST_JSON}")
    print(f"✅ {count} vertaalde module(s) gepubliceerd naar docs/content/")
