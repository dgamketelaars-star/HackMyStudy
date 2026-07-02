import config

SOURCE = config.MARKDOWN_DIR
OUTPUT = config.COURSE_1_RAW_MD

files = sorted(SOURCE.glob("*.md"))

parts = []

for file in files:
    text = file.read_text(encoding="utf-8")
    parts.append(f"\n\n---\n\n# FILE: {file.name}\n\n{text}")

OUTPUT.write_text("\n".join(parts), encoding="utf-8")

print("✅ Samengevoegd:", OUTPUT)
print("Aantal bestanden:", len(files))