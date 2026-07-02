"""Centraal startpunt voor de HackMyStudy-pipeline.

Roept de bestaande scripts in scripts/ aan als los proces (subprocess) — de
scripts zelf zijn niet aangepast, dit is puur een overzichtelijke ingang.
Zie PIPELINE.md voor de volledige uitleg en volgorde van beide pipelines.

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
# in `python run.py --help`, gegroepeerd per pipeline.
COMMANDS = [
    # --- Sessie starten (handmatig, zie README.md voor de CDP-stap) ---
    ("login", "login.py",
     "Open een geïsoleerde browser-sessie (browser-profile/) en log in op Coursera"),
    ("open-chrome", "open_my_chrome.py",
     "Open je eigen Chrome-profiel i.p.v. een geïsoleerde sessie"),

    # --- Single-course pipeline ---
    ("collect-links", "collect_links.py",
     "Verzamel alle /learn/-links van de huidige pagina -> data/course_links.json(.txt)"),
    ("clean-links", "clean_course_links.py",
     "Filter ruwe links tot leer-items -> data/learning_items.json"),
    ("download-lessons", "download_lessons.py",
     "Download elk leer-item uit data/learning_items.json als html+text -> course/html, course/text"),
    ("download-course", "download_course.py",
     "Loop via de 'volgende'-knop door een cursus en sla elke les op als markdown -> course/markdown"),
    ("save-lesson", "save_current_lesson.py",
     "Sla alleen de huidige pagina op als één markdown-les -> course/markdown"),
    ("combine", "combine_course_1.py",
     "Voeg alle markdown-lessen samen -> course/course_1_raw.md"),
    ("generate-module", "generate_module.py",
     "Genereer een Daan-versie van module 1 via OpenAI -> course/module_1_daan_test.md"),

    # --- Programma-brede pipeline (meerdere cursussen tegelijk) ---
    ("collect-program-courses", "save_program_courses.py",
     "Verzamel toegestane cursussen van het programma -> data/program_courses.json"),
    ("collect-program-items", "collect_program_learning_items.py",
     "Verzamel leer-items voor alle programma-cursussen -> data/all_learning_items.json"),
    ("collect-all-links", "collect_all_links.py",
     "Scroll-en-verzamel alle leerlinks op de huidige pagina -> data/learning_items_full.json"),
]


def main():
    parser = argparse.ArgumentParser(
        description="HackMyStudy pipeline-launcher. Zie PIPELINE.md voor de volledige uitleg.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, script, help_text in COMMANDS:
        subparsers.add_parser(name, help=help_text)

    args = parser.parse_args()

    script_by_name = {name: script for name, script, _ in COMMANDS}
    script_path = SCRIPTS_DIR / script_by_name[args.command]

    result = subprocess.run([sys.executable, str(script_path)], cwd=REPO_ROOT)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
