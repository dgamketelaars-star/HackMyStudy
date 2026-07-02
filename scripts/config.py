"""Centrale configuratie: paden en constanten die door meerdere scripts gebruikt worden.

Alle paden zijn relatief aan de repo-root. Scripts worden uitgevoerd vanuit de
repo-root (bv. `python scripts/clean_course_links.py`), dus dat is het uitgangspunt.
"""

from pathlib import Path

# Chrome-debugsessie waar de scrape-scripts zich mee verbinden via connect_over_cdp.
# Deze sessie moet handmatig gestart zijn (zie README.md) voordat je een scrape-script draait.
CDP_URL = "http://127.0.0.1:9222"

# Mappen
DATA_DIR = Path("data")
COURSE_DIR = Path("course")
MARKDOWN_DIR = COURSE_DIR / "markdown"
HTML_DIR = COURSE_DIR / "html"
TEXT_DIR = COURSE_DIR / "text"
PROMPTS_DIR = Path("prompts")

# Databestanden — single-course pipeline
COURSE_LINKS_JSON = DATA_DIR / "course_links.json"
COURSE_LINKS_TXT = DATA_DIR / "course_links.txt"
LEARNING_ITEMS_JSON = DATA_DIR / "learning_items.json"

# Databestanden — programma-brede pipeline
PROGRAM_COURSES_JSON = DATA_DIR / "program_courses.json"
ALL_LEARNING_ITEMS_JSON = DATA_DIR / "all_learning_items.json"
LEARNING_ITEMS_FULL_JSON = DATA_DIR / "learning_items_full.json"

# Cursusoutput
COURSE_1_RAW_MD = COURSE_DIR / "course_1_raw.md"
MODULE_1_OUTPUT_MD = COURSE_DIR / "module_1_daan_test.md"

# Prompts
DAAN_PROMPT_MD = PROMPTS_DIR / "daan_module_prompt.md"

# Playwright user-data-dir voor de isolated login-sessie (zie scripts/login.py)
BROWSER_PROFILE_DIR = "browser-profile"
