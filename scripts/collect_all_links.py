from playwright.sync_api import sync_playwright
import json

import config
from scraping_utils import clean_title, course_slug_from_url

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(config.CDP_URL)
    page = browser.contexts[0].pages[0]

    print("URL:", page.url)
    print("Titel:", page.title())

    slug = course_slug_from_url(page.url)
    if not slug:
        raise SystemExit(f"Kan geen cursus-slug herkennen in: {page.url}")

    OUTPUT = config.course_data_dir(slug) / "learning_items_full.json"
    config.course_data_dir(slug).mkdir(parents=True, exist_ok=True)

    seen = {}

    # Probeer meerdere keren te scrollen in de pagina/zijbalk
    for i in range(40):
        items = page.evaluate("""
        () => {
            return [...document.querySelectorAll("a[href*='/learn/']")]
                .map(a => ({
                    title: a.innerText,
                    url: a.href
                }))
                .filter(x => x.title && x.url)
        }
        """)

        for item in items:
            url = item["url"]
            title = clean_title(item["title"])
            if url not in seen:
                seen[url] = {
                    "title": title,
                    "url": url
                }

        print(f"Scroll {i+1}: {len(seen)} unieke links")

        # scroll hoofdvenster
        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(700)

        # scroll extra in alle scrollbare containers
        page.evaluate("""
        () => {
            [...document.querySelectorAll("div")]
                .filter(el => el.scrollHeight > el.clientHeight + 100)
                .forEach(el => el.scrollTop = el.scrollTop + 800)
        }
        """)
        page.wait_for_timeout(700)

    all_items = list(seen.values())

    # Alleen kennis-items bewaren
    filtered = []
    for item in all_items:
        url = item["url"]
        title = item["title"]

        if "/lecture/" in url or "/supplement/" in url:
            filtered.append(item)

    OUTPUT.write_text(
        json.dumps(filtered, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print()
    print("✅ Totaal gevonden:", len(all_items))
    print("✅ Relevante lessen:", len(filtered))
    print("✅ Opgeslagen:", OUTPUT)