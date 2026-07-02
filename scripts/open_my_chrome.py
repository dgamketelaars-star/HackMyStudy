from playwright.sync_api import sync_playwright

CHROME_PROFILE = r"C:\Users\LENOVO\AppData\Local\Google\Chrome\User Data"

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=CHROME_PROFILE,
        channel="chrome",
        headless=False,
        args=["--start-maximized"],
    )

    page = browser.new_page()
    page.goto("https://www.coursera.org/")

    input("Check of je bent ingelogd. Druk daarna op Enter...")
    browser.close()