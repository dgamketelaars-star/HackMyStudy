from playwright.sync_api import sync_playwright
import re

import config

OUTPUT = config.MARKDOWN_DIR
OUTPUT.mkdir(parents=True, exist_ok=True)


def clean_filename(name):
    return re.sub(r'[<>:"/\\|?*]', "", name).strip()


with sync_playwright() as p:

    browser = p.chromium.connect_over_cdp(config.CDP_URL)
    page = browser.contexts[0].pages[0]

    while True:

        title = page.title().replace(" | Coursera", "")
        print(f"\n===== {title} =====")

        # -----------------------
        # Inhoud ophalen
        # -----------------------

        result = page.evaluate("""
        () => {

            let article =
                document.querySelector(".rc-ReadingItem")
                || document.querySelector("[data-testid='transcript']")
                || document.body;

            return {
                text: article.innerText
            }

        }
        """)

        filename = OUTPUT / (clean_filename(title) + ".md")

        filename.write_text(result["text"], encoding="utf-8")

        print("Opgeslagen:", filename)

        # -----------------------
        # Volgende zoeken
        # -----------------------

        buttons = page.get_by_role("button", name=re.compile("Volgende|Next|Ga naar het volgende item", re.I))

        if buttons.count() == 0:
            print("Geen volgende les meer.")
            break

        old_url = page.url

        buttons.first.click()

        page.wait_for_url(lambda url: url != old_url)

        page.wait_for_timeout(1500)