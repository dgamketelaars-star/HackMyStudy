from playwright.sync_api import sync_playwright
import json

import config

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(config.CDP_URL)
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

    with open(config.COURSE_LINKS_JSON, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    with open(config.COURSE_LINKS_TXT, "w", encoding="utf-8") as f:
        for item in cleaned:
            f.write(f"{item['title']}\n{item['url']}\n\n")

    print(f"✅ {len(cleaned)} links opgeslagen")
    print(f"✅ {config.COURSE_LINKS_JSON}")
    print(f"✅ {config.COURSE_LINKS_TXT}")