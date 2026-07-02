from playwright.sync_api import sync_playwright
import json

import config
from scraping_utils import clean_title

COURSES_FILE = config.PROGRAM_COURSES_JSON
OUTPUT_FILE = config.ALL_LEARNING_ITEMS_JSON


def collect_links_from_current_page(page, course_title):
    seen = {}

    for i in range(40):
        items = page.evaluate("""
        () => [...document.querySelectorAll("a[href*='/learn/']")]
            .map(a => ({
                title: a.innerText,
                url: a.href
            }))
            .filter(x => x.title && x.url)
        """)

        for item in items:
            url = item["url"]
            title = clean_title(item["title"])

            if "/lecture/" in url or "/supplement/" in url:
                if url not in seen:
                    seen[url] = {
                        "course": course_title,
                        "title": title,
                        "url": url
                    }

        print(f"  scroll {i+1}: {len(seen)} lessen")

        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(500)

        page.evaluate("""
        () => {
            [...document.querySelectorAll("div")]
                .filter(el => el.scrollHeight > el.clientHeight + 100)
                .forEach(el => el.scrollTop = el.scrollTop + 900)
        }
        """)
        page.wait_for_timeout(500)

    return list(seen.values())


with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(config.CDP_URL)
    page = browser.contexts[0].pages[0]

    courses = json.loads(COURSES_FILE.read_text(encoding="utf-8"))

    all_items = []

    for course in courses:
        print("\n==============================")
        print("Cursus:", course["title"])
        print(course["url"])

        for module_number in range(1, 6):
            base_url = course["url"].split("/home/")[0]
            module_url = f"{base_url}/home/module/{module_number}"

            print("Module:", module_number)
            print(module_url)

            page.goto(module_url, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            items = collect_links_from_current_page(
                page,
                f"{course['title']} - module {module_number}"
            )

            all_items.extend(items)

            print("Gevonden in module:", len(items))


    OUTPUT_FILE.write_text(
        json.dumps(all_items, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("\n✅ Totaal lessen:", len(all_items))
    print("✅ Opgeslagen:", OUTPUT_FILE)