"""Zet gecachte html-lessen (course/<slug>/html/) om naar markdown, offline.

Sluit een gat in de automatisering: download_lessons.py haalt html+text op
zonder browserinteractie, maar dat volstaat alleen voor "reading"-lessen
(Coursera rendert die direct in de HTML als .rc-ReadingItem). Video-lessen
tonen hun transcript pas na een klik op het "Transcript"-paneel — dat zit
niet in de gecachte HTML, en is dus met dit script niet te vertalen. Zulke
lessen worden overgeslagen (niet met loze content gevuld) en gerapporteerd.

Voor overgeslagen video-lessen: gebruik nog steeds save_current_lesson.py of
download_course.py (interactief, via de live paginasessie).

Idempotent: bestaande markdown-bestanden worden niet overschreven.
"""

from bs4 import BeautifulSoup

import config
from scraping_utils import normalize_title

CONTENT_SELECTORS = [
    (".rc-ReadingItem", "reading"),
    (".rc-CML", "reading"),
]


def clean_filename(name):
    import re
    return re.sub(r'[<>:"/\\|?*]', "", name).strip()


def extract(html_path):
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")

    title_tag = soup.select_one("title")
    title = title_tag.get_text(strip=True).replace(" | Coursera", "") if title_tag else html_path.stem

    for selector, lesson_type in CONTENT_SELECTORS:
        el = soup.select_one(selector)
        if el:
            text = el.get_text("\n", strip=True)
            if text:
                return title, lesson_type, text

    return title, None, None


def convert_course(slug):
    html_dir = config.html_dir(slug)
    markdown_dir = config.markdown_dir(slug)
    markdown_dir.mkdir(parents=True, exist_ok=True)

    existing_titles = {normalize_title(f.stem) for f in markdown_dir.glob("*.md")}

    converted, skipped, already = 0, [], 0

    for html_path in sorted(html_dir.glob("*.html")):
        title, lesson_type, text = extract(html_path)
        filename = clean_filename(title) + ".md"
        out_path = markdown_dir / filename

        if normalize_title(title) in existing_titles or out_path.exists():
            already += 1
            continue

        if not text:
            skipped.append(title)
            continue

        markdown = f"""---
title: {title}
type: {lesson_type}
source: {html_path.name}
---

# {title}

{text}
"""
        out_path.write_text(markdown, encoding="utf-8")
        existing_titles.add(normalize_title(title))
        converted += 1

    return converted, already, skipped


if __name__ == "__main__":
    slugs = sorted(
        p.name for p in config.COURSE_DIR.iterdir()
        if p.is_dir() and config.html_dir(p.name).exists()
    ) if config.COURSE_DIR.exists() else []

    if not slugs:
        print("Geen enkele course/<slug>/html/ gevonden. Draai eerst download-lessons.")

    for slug in slugs:
        converted, already, skipped = convert_course(slug)
        print(f"\n{slug}:")
        print(f"  ✅ {converted} nieuw omgezet naar markdown")
        print(f"  ⏭️  {already} al aanwezig (overgeslagen)")
        if skipped:
            print(f"  ⚠️  {len(skipped)} les(sen) hebben geen bruikbare inhoud in de cache")
            print("     (waarschijnlijk video's — transcript laadt pas na een klik op de live pagina).")
            print("     Gebruik save_current_lesson.py of download_course.py voor deze lessen:")
            for title in skipped:
                print("     -", title)
