from playwright.sync_api import sync_playwright

import config

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        config.BROWSER_PROFILE_DIR,
        headless=False
    )

    page = browser.new_page()
    page.goto("https://www.coursera.org/")

    print("Log in op Coursera in het geopende browservenster.")
    input("Druk hier op Enter als je bent ingelogd...")

    browser.close()
    