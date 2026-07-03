"""Verzamelt leer-items voor alle cursussen in data/courses.json, per module.

Dit is de primaire manier om spoor 1 te vullen: bezoekt automatisch elke
cursus x module 1-5 en schrijft per cursus een data/<slug>/learning_items.json
(zelfde bestand/vorm als clean_course_links.py voor de single-page pipeline
produceert — download_lessons.py kan dus altijd hetzelfde bestand lezen,
ongeacht welke verzamelmethode gebruikt is).

In tegenstelling tot de single-page pipeline (collect_links.py) weet dit
script wél in welke module een les staat (het bezoekt elke module-pagina
apart), dus items krijgen een "module"-nummer. Dat ontbreekt nog voor cursus
1, die via de single-page pipeline verzameld is.
"""

from playwright.sync_api import sync_playwright
import json

import config
from scraping_utils import clean_title

MODULE_RANGE = range(1, 6)


def collect_links_from_current_page(page):
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

    courses = config.load_courses()
    if not courses:
        raise SystemExit(f"Geen cursussen gevonden in {config.COURSES_JSON}. Draai eerst save_program_courses.py.")

    for course in courses:
        slug = course["slug"]
        print("\n==============================")
        print("Cursus:", course["title"], f"({slug})")
        print(course["url"])

        seen_urls = set()
        course_items = []

        for module_number in MODULE_RANGE:
            base_url = course["url"].split("/home/")[0]
            module_url = f"{base_url}/home/module/{module_number}"

            print("Module:", module_number)
            print(module_url)

            page.goto(module_url, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            items = collect_links_from_current_page(page)

            new_items = 0
            for item in items:
                if item["url"] in seen_urls:
                    continue
                seen_urls.add(item["url"])
                course_items.append({
                    "title": item["title"],
                    "url": item["url"],
                    "module": module_number
                })
                new_items += 1

            print("Nieuw gevonden in module:", new_items)

        config.course_data_dir(slug).mkdir(parents=True, exist_ok=True)
        config.learning_items_json(slug).write_text(
            json.dumps(course_items, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        print(f"✅ {slug}: {len(course_items)} lessen -> {config.learning_items_json(slug)}")
