"""Downloadt elk leer-item (data/<slug>/learning_items.json) als ruwe html+text.

Batcht over alle cursussen waarvoor learning_items.json bestaat. Al
gedownloade lessen (zelfde bestandsnaam al aanwezig) worden overgeslagen, dus
dit script is veilig opnieuw te draaien nadat een nieuwe cursus verzameld is
— het scraapt niet opnieuw wat er al staat.
"""

from playwright.sync_api import sync_playwright
import json
import re

import config


def safe_filename(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text).strip("-")
    return text[:70]


with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(config.CDP_URL)
    context = browser.contexts[0]
    page = context.pages[0]

    slugs = [s for s in config.known_course_slugs() if config.learning_items_json(s).exists()]

    if not slugs:
        print("Geen enkele data/<slug>/learning_items.json gevonden. Draai eerst clean-links of collect-program-items.")

    for slug in slugs:
        lessons = json.loads(config.learning_items_json(slug).read_text(encoding="utf-8"))

        html_dir = config.html_dir(slug)
        text_dir = config.text_dir(slug)
        html_dir.mkdir(parents=True, exist_ok=True)
        text_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n📚 {slug}: {len(lessons)} lessen gevonden")

        for index, lesson in enumerate(lessons, start=1):
            title = lesson["title"].split("\n")[0].strip()
            url = lesson["url"]

            filename = f"{index:03d}-{safe_filename(title)}"
            html_path = html_dir / f"{filename}.html"
            text_path = text_dir / f"{filename}.txt"

            if html_path.exists() and text_path.exists():
                print(f"⏭️  {index}/{len(lessons)} — {title} (al gedownload)")
                continue

            print(f"\n📘 {index}/{len(lessons)} — {title}")
            print(url)

            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(6000)

            html = page.content()
            text = page.locator("body").inner_text()

            html_path.write_text(html, encoding="utf-8")
            text_path.write_text(text, encoding="utf-8")

            print(f"✅ opgeslagen: {filename}.txt")

    print("\n🎉 Klaar. Alle beschikbare lessen zijn gedownload.")
