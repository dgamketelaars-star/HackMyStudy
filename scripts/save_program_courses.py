from playwright.sync_api import sync_playwright
import json

import config
from scraping_utils import course_slug_from_url

ALLOWED = [
    "microsoft-enterprise-product-management-fundamentals",
    "microsoft-market-research-and-competitive-analysis",
    "microsoft-product-strategy-and-roadmapping",
    "microsoft-product-design-and-ux-ui-fundamentals",
    "microsoft-product-launch-and-post-launch-management",
]

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(config.CDP_URL)
    page = browser.contexts[0].pages[0]

    links = page.evaluate("""
    () => [...document.querySelectorAll("a[href*='/learn/']")]
        .map(a => ({
            title: a.innerText.trim(),
            url: a.href
        }))
        .filter(x => x.title && x.url)
    """)

    courses = []
    seen = set()

    for link in links:
        url = link["url"]

        if any(slug in url for slug in ALLOWED):
            clean_url = url.split("?")[0].replace("/home/welcome", "/home/module/1")

            if clean_url not in seen:
                seen.add(clean_url)
                courses.append({
                    "slug": course_slug_from_url(clean_url),
                    "title": link["title"],
                    "url": clean_url
                })

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.COURSES_JSON.write_text(
        json.dumps(courses, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("✅ Cursussen gevonden:", len(courses))
    for c in courses:
        print("-", c["title"])
        print(" ", c["url"])