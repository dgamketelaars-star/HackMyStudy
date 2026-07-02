from playwright.sync_api import sync_playwright

USER_DATA_DIR = "browser-profile"

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        USER_DATA_DIR,
        headless=False
    )

    page = browser.new_page()
    page.goto("https://www.coursera.org/")

    print("Log in op Coursera in het geopende browservenster.")
    input("Druk hier op Enter als je bent ingelogd...")

    browser.close()
    