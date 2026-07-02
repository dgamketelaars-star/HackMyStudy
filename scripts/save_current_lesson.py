from playwright.sync_api import sync_playwright
from extract_content import extract_content
import re

import config


def safe_filename(text):
    text = re.sub(r'[\\/*?:"<>|]', "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text[:80]


with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(config.CDP_URL)
    page = browser.contexts[0].pages[0]

    result = extract_content(page)

    title = result["title"].replace(" | Coursera", "")
    lesson_type = result["type"]
    url = page.url
    text = result["text"]

    config.MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)

    filename = safe_filename(title) + ".md"
    path = config.MARKDOWN_DIR / filename

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