from pathlib import Path
from playwright.sync_api import sync_playwright
from extract_content import extract_content
import re


def safe_filename(text):
    text = re.sub(r'[\\/*?:"<>|]', "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text[:80]


with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = browser.contexts[0].pages[0]

    result = extract_content(page)

    title = result["title"].replace(" | Coursera", "")
    lesson_type = result["type"]
    url = page.url
    text = result["text"]

    Path("course/markdown").mkdir(parents=True, exist_ok=True)

    filename = safe_filename(title) + ".md"
    path = Path("course/markdown") / filename

    markdown = f"""---
title: {title}
type: {lesson_type}
url: {url}
---

# {title}

{text}
"""

    path.write_text(markdown, encoding="utf-8")

    print("✅ Opgeslagen:", path)