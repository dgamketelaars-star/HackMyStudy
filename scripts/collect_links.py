from playwright.sync_api import sync_playwright
import json

import config
from scraping_utils import course_slug_from_url

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(config.CDP_URL)
    page = browser.contexts[0].pages[0]

    page.wait_for_timeout(3000)

    slug = course_slug_from_url(page.url)
    if not slug:
        raise SystemExit(
            f"Kan geen cursus-slug herkennen in de huidige pagina-URL: {page.url}\n"
            "Zorg dat de open pagina een coursera.org/learn/<cursus>/... URL is."
        )

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

    config.course_data_dir(slug).mkdir(parents=True, exist_ok=True)

    with open(config.course_links_json(slug), "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    with open(config.course_links_txt(slug), "w", encoding="utf-8") as f:
        for item in cleaned:
            f.write(f"{item['title']}\n{item['url']}\n\n")

    print(f"✅ {len(cleaned)} links opgeslagen voor '{slug}'")
    print(f"✅ {config.course_links_json(slug)}")
    print(f"✅ {config.course_links_txt(slug)}")