import json

import config

LEARNING_TYPES = [
    "/supplement/",
    "/lecture/",
    "/coach/",
    "/discussionPrompt/",
    "/assignment-submission/",
]

with open(config.COURSE_LINKS_JSON, "r", encoding="utf-8") as f:
    links = json.load(f)

cleaned = []

for item in links:
    url = item["url"]
    title = item["title"].strip()

    if any(t in url for t in LEARNING_TYPES):
        cleaned.append({
            "title": title,
            "url": url
        })

with open(config.LEARNING_ITEMS_JSON, "w", encoding="utf-8") as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

print(f"✅ {len(cleaned)} leer-items gevonden")
for i, item in enumerate(cleaned, 1):
    print(i, item["title"])