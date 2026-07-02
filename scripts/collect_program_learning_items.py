from playwright.sync_api import sync_playwright
from pathlib import Path
import json
import re

COURSES_FILE = Path("data/program_courses.json")
OUTPUT_FILE = Path("data/all_learning_items.json")


def clean_title(text):
    text = re.sub(r"\n+", "\n", text).strip()
    return text


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
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
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