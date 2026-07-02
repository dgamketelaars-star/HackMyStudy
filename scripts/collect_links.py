from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import json

BASE_URL = "https://www.coursera.org"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = browser.contexts[0].pages[0]

    page.wait_for_timeout(3000)

    links = page.locator("a").evaluate_all("""
        elements => elements.map(a => ({
            text: a.innerText.trim(),
            href: a.href
        }))
    """)

    cleaned = []
    seen = set()

    for link in links:
        text = link["text"]
        href = link["href"]

        if not text or not href:
            continue

        if "coursera.org/learn/" not in href:
            continue

        key = (text, href)
        if key in seen:
            continue

        seen.add(key)
        cleaned.append({
            "title": text,
            "url": href
        })

    with open("data/course_links.json", "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    with open("data/course_links.txt", "w", encoding="utf-8") as f:
        for item in cleaned:
            f.write(f"{item['title']}\n{item['url']}\n\n")

    print(f"✅ {len(cleaned)} links opgeslagen")
    print("✅ data/course_links.json")
    print("✅ data/course_links.txt")