from playwright.sync_api import Page


def extract_content(page: Page):

    # ===== Reading =====

    reading = page.locator(".rc-ReadingItem")

    if reading.count() > 0:
        return {
            "type": "reading",
            "title": page.title(),
            "text": reading.first.inner_text()
        }

    # ===== Video =====

    transcript = page.locator(".rc-Transcript")

    if transcript.count() > 0:
        return {
            "type": "video",
            "title": page.title(),
            "text": transcript.first.inner_text()
        }

    # ===== Nothing found =====

    return {
        "type": "unknown",
        "title": page.title(),
        "text": ""
    }