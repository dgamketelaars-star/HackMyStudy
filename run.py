"""Centraal startpunt voor de HackMyStudy-pipeline.

Roept de bestaande scripts in scripts/ aan als los proces (subprocess) — de
scripts zelf zijn niet aangepast, dit is puur een overzichtelijke ingang.
Zie PIPELINE.md voor de volledige uitleg en volgorde.

Gebruik:
    python run.py <commando>
    python run.py --help
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

# (commando, scriptbestand, korte uitleg) — volgorde hier is ook de leesvolgorde
# in `python run.py --help`, gegroepeerd per fase van de pipeline.
COMMANDS = [
    # --- Sessie starten (handmatig, zie README.md voor de CDP-stap) ---
    ("login", "login.py",
     "Open een geïsoleerde browser-sessie (browser-profile/) en log in op Coursera"),
    ("open-chrome", "open_my_chrome.py",
     "Open je eigen Chrome-profiel i.p.v. een geïsoleerde sessie"),

    # --- Verzamelen: welke cursussen en lessen bestaan er ---
    ("collect-program-courses", "save_program_courses.py",
     "Verzamel de 5 officiële cursussen van het programma -> data/courses.json"),
    ("collect-program-items", "collect_program_learning_items.py",
     "Bezoek alle 5 cursussen x module 1-5 en verzamel lessen -> data/<cursus>/learning_items.json"),
    ("collect-links", "collect_links.py",
     "(losse pagina) Verzamel /learn/-links van de huidige pagina -> data/<cursus>/course_links.json(.txt)"),
    ("clean-links", "clean_course_links.py",
     "Filter course_links.json tot leer-items, voor elke cursus die dat heeft -> data/<cursus>/learning_items.json"),
    ("collect-all-links", "collect_all_links.py",
     "(losse pagina) Scroll-en-verzamel leerlinks -> data/<cursus>/learning_items_full.json"),

    # --- Downloaden: leer-items ophalen als ruwe html/text ---
    ("download-lessons", "download_lessons.py",
     "Download elk leer-item als html+text, voor elke cursus met learning_items.json -> course/<cursus>/html, text"),

    # --- Omzetten naar markdown (de brontekst voor de vertaalstap) ---
    ("lessons-to-markdown", "lessons_to_markdown.py",
     "Zet gecachte 'reading'-lessen offline om naar markdown (video's niet, zie PIPELINE.md) -> course/<cursus>/markdown"),
    ("download-course", "download_course.py",
     "(interactief) Loop via de 'volgende'-knop door een cursus, sla elke les op als markdown"),
    ("save-lesson", "save_current_lesson.py",
     "(interactief) Sla alleen de huidige pagina op als markdown-les"),

    # --- Samenvoegen, vertalen en publiceren ---
    ("combine", "combine_course.py",
     "Voeg de markdown-lessen van elke cursus samen, in de echte Coursera-volgorde -> course/<cursus>/raw.md"),
    ("translate-module", "translate_module.py",
     "Vertaal één module naar de Daan-leerstijl (echte OpenAI-kosten!) -- gebruik: run.py translate-module -- --course <slug> --module <n> [--dry-run]"),
    ("generate-module", "generate_module.py",
     "(oude proof-of-concept, zie PIPELINE.md) Vertaal een cursusfragment via OpenAI"),
    ("build-manifest", "build_manifest.py",
     "Bouw het cursus/module-overzicht dat de webapp gebruikt -> data/manifest.json"),
    ("publish-docs", "publish_docs.py",
     "Kopieer de manifest + vertaalde modules naar docs/, zodat de webapp ze kan tonen"),
]


def main():
    parser = argparse.ArgumentParser(
        description="HackMyStudy pipeline-launcher. Zie PIPELINE.md voor de volledige uitleg. "
                     "Extra argumenten na '--' worden doorgegeven aan het onderliggende script.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, script, help_text in COMMANDS:
        subparsers.add_parser(name, help=help_text)

    args, extra_args = parser.parse_known_args()
    if extra_args and extra_args[0] == "--":
        extra_args = extra_args[1:]

    script_by_name = {name: script for name, script, _ in COMMANDS}
    script_path = SCRIPTS_DIR / script_by_name[args.command]

    result = subprocess.run([sys.executable, str(script_path), *extra_args], cwd=REPO_ROOT)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
