"""Kleine hulpfuncties die letterlijk hetzelfde zijn in meerdere scrape-scripts.

Let op: de scroll-en-verzamel-loops in collect_all_links.py en
collect_program_learning_items.py lijken op elkaar maar zijn bewust anders
afgesteld (wachttijden, scrollafstand, filtermoment) en zijn daarom
opzettelijk NIET samengevoegd — zie PIPELINE.md voor de toelichting.
"""

import re
import unicodedata

MODULE_TITLE_PATTERN = re.compile(r"Module (\d)\n([^\n]+)\n")


def slugify(text):
    """Zet een titel om in een URL-veilige slug, bv. voor lesson-ids in de
    webapp-manifest: 'Casestudie: Cloudproducten' -> 'casestudie-cloudproducten'."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def clean_title(text):
    text = re.sub(r"\n+", "\n", text).strip()
    return text


def course_slug_from_url(url):
    """Haal de cursus-slug uit een Coursera-URL, bv.
    'https://www.coursera.org/learn/microsoft-enterprise-.../lecture/xyz'
    -> 'microsoft-enterprise-...'. Geeft None als de URL geen /learn/<slug>/ bevat.
    """
    match = re.search(r"/learn/([^/]+)/", url)
    return match.group(1) if match else None


def guess_module_title(markdown_dir, module_number):
    """Zoekt de echte moduletitel in het zijbalkmenu dat in sommige (video-)
    scrapes is meegekomen (zie translate_module.py voor de achtergrond).
    Geeft None als niets gevonden wordt (bv. cursus nog niet gescraped)."""
    if not markdown_dir.exists():
        return None
    for f in markdown_dir.glob("*.md"):
        text = f.read_text(encoding="utf-8")
        for match in MODULE_TITLE_PATTERN.finditer(text):
            if int(match.group(1)) == module_number:
                return match.group(2).strip()
    return None


def normalize_title(text):
    """Normaliseer een lestitel voor het matchen van bestandsnamen tegen
    ruwe scrape-titels: eerste regel, geen speciale tekens, spaties/koppeltekens
    gelijk, lowercase. Gebruikt door build_manifest.py en combine_course.py om
    de originele Coursera-volgorde te herstellen (bestandsnamen zelf zijn
    alfabetisch gesorteerd en dus geen betrouwbare volgorde)."""
    text = text.split("\n")[0].strip()
    text = re.sub(r'[<>:"/\\|?*]', "", text)
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text
