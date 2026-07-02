from playwright.sync_api import sync_playwright
from pathlib import Path
import json
import re

INPUT_FILE = Path("data/learning_items.json")
OUTPUT_DIR = Path("course")
TEXT_DIR = OUTPUT_DIR / "text"
HTML_DIR = OUTPUT_DIR / "html"

TEXT_DIR.mkdir(parents=True, exist_ok=True)
HTML_DIR.mkdir(parents=True, exist_ok=True)


def safe_filename(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text).strip("-")
    return text[:70]


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    lessons = json.load(f)

print(f"📚 {len(lessons)} lessen gevonden")

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    context = browser.contexts[0]
    page = context.pages[0]

    for index, lesson in enumerate(lessons, start=1):
        title = lesson["title"].split("\n")[0].strip()
        url = lesson["url"]

        filename = f"{index:03d}-{safe_filename(title)}"

        print(f"\n📘 {index}/{len(lessons)} — {title}")
        print(url)

        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(6000)

        html = page.content()
        text = page.locator("body").inner_text()

        (HTML_DIR / f"{filename}.html").write_text(html, encoding="utf-8")
        (TEXT_DIR / f"{filename}.txt").write_text(text, encoding="utf-8")

        print(f"✅ opgeslagen: {filename}.txt")

print("\n🎉 Klaar. Alle lessen zijn gedownload.")