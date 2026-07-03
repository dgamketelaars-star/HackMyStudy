"""Centrale configuratie: cursussen, paden en constanten voor de pipeline.

Alle paden zijn relatief aan de repo-root. Scripts worden uitgevoerd vanuit de
repo-root (bv. `python scripts/clean_course_links.py`, of via run.py), dus dat
is het uitgangspunt.

De pipeline werkt met meerdere cursussen tegelijk (spoor 1: alle 5 Microsoft-
cursussen). Elke cursus heeft een stabiele "slug": het laatste segment van de
Coursera-URL (bv. "microsoft-enterprise-product-management-fundamentals").
Alle content voor die cursus staat onder course/<slug>/ en data/<slug>/.
"""

from pathlib import Path

# Chrome-debugsessie waar de scrape-scripts zich mee verbinden via connect_over_cdp.
# Deze sessie moet handmatig gestart zijn (zie README.md) voordat je een scrape-script draait.
CDP_URL = "http://127.0.0.1:9222"

# Mappen
DATA_DIR = Path("data")
COURSE_DIR = Path("course")
PROMPTS_DIR = Path("prompts")
DOCS_DIR = Path("docs")

# De 5 officiële cursussen (slug, titel, Coursera-URL) — zie save_program_courses.py
COURSES_JSON = DATA_DIR / "courses.json"

# Prompt voor de learning-translation-stap (kernfunctionaliteit, zie PIPELINE.md)
DAAN_PROMPT_MD = PROMPTS_DIR / "daan_module_prompt.md"

# Playwright user-data-dir voor de isolated login-sessie (zie scripts/login.py)
BROWSER_PROFILE_DIR = "browser-profile"

# Manifest die de webapp gebruikt om cursussen/lessen te tonen
MANIFEST_JSON = DATA_DIR / "manifest.json"
DOCS_CONTENT_DIR = DOCS_DIR / "content"
DOCS_MANIFEST_JSON = DOCS_CONTENT_DIR / "manifest.json"


def course_data_dir(slug: str) -> Path:
    return DATA_DIR / slug


def course_links_json(slug: str) -> Path:
    return course_data_dir(slug) / "course_links.json"


def course_links_txt(slug: str) -> Path:
    return course_data_dir(slug) / "course_links.txt"


def learning_items_json(slug: str) -> Path:
    return course_data_dir(slug) / "learning_items.json"


def course_dir(slug: str) -> Path:
    return COURSE_DIR / slug


def html_dir(slug: str) -> Path:
    return course_dir(slug) / "html"


def text_dir(slug: str) -> Path:
    return course_dir(slug) / "text"


def markdown_dir(slug: str) -> Path:
    return course_dir(slug) / "markdown"


def raw_md(slug: str) -> Path:
    return course_dir(slug) / "raw.md"


def translated_dir(slug: str) -> Path:
    return course_dir(slug) / "translated"


def load_courses() -> list[dict]:
    """Lees data/courses.json (de 5 officiële cursussen). Geeft [] als het
    bestand nog niet bestaat (bv. save_program_courses.py nog niet gedraaid)."""
    import json

    if not COURSES_JSON.exists():
        return []
    return json.loads(COURSES_JSON.read_text(encoding="utf-8"))


def known_course_slugs() -> list[str]:
    """Alle cursus-slugs waarvoor al data/<slug>/ bestaat op schijf, ongeacht
    of ze in courses.json staan (handig voor batch-scripts die 'alles wat er
    is' willen verwerken)."""
    if not DATA_DIR.exists():
        return []
    return sorted(
        p.name for p in DATA_DIR.iterdir()
        if p.is_dir() and p.name != "__pycache__"
    )
