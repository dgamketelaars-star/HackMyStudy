from pathlib import Path

SOURCE = Path("course/markdown")
OUTPUT = Path("course/course_1_raw.md")

files = sorted(SOURCE.glob("*.md"))

parts = []

for file in files:
    text = file.read_text(encoding="utf-8")
    parts.append(f"\n\n---\n\n# FILE: {file.name}\n\n{text}")

OUTPUT.write_text("\n".join(parts), encoding="utf-8")

print("✅ Samengevoegd:", OUTPUT)
print("Aantal bestanden:", len(files))