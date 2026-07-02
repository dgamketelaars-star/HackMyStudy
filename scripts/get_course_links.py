from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = browser.contexts[0].pages[0]

    result = page.evaluate("""
    () => {
        const links = [...document.querySelectorAll("a[href*='/learn/']")];

        return links.map(a => ({
            text: a.innerText.trim(),
            url: a.href
        }));
    }
    """)

    print(json.dumps(result, indent=2, ensure_ascii=False))