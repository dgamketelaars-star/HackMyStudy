"""Kleine hulpfuncties die letterlijk hetzelfde zijn in meerdere scrape-scripts.

Let op: de scroll-en-verzamel-loops in collect_all_links.py en
collect_program_learning_items.py lijken op elkaar maar zijn bewust anders
afgesteld (wachttijden, scrollafstand, filtermoment) en zijn daarom
opzettelijk NIET samengevoegd — zie PIPELINE.md voor de toelichting.
"""

import re
import unicodedata


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
