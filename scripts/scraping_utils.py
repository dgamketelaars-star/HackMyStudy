"""Kleine hulpfuncties die letterlijk hetzelfde zijn in meerdere scrape-scripts.

Let op: de scroll-en-verzamel-loops in collect_all_links.py en
collect_program_learning_items.py lijken op elkaar maar zijn bewust anders
afgesteld (wachttijden, scrollafstand, filtermoment) en zijn daarom
opzettelijk NIET samengevoegd — zie PIPELINE.md voor de toelichting.
"""

import re


def clean_title(text):
    text = re.sub(r"\n+", "\n", text).strip()
    return text
