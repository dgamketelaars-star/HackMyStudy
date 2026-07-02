from openai import OpenAI

import config

client = OpenAI()

PROMPT_FILE = config.DAAN_PROMPT_MD
COURSE_FILE = config.COURSE_1_RAW_MD
OUTPUT_FILE = config.MODULE_1_OUTPUT_MD

prompt = PROMPT_FILE.read_text(encoding="utf-8")
course_text = COURSE_FILE.read_text(encoding="utf-8")

# Eerst kleine test: alleen eerste 15.000 tekens
course_sample = course_text[:15000]

response = client.responses.create(
    model="gpt-4.1",
    input=[
        {
            "role": "system",
            "content": prompt,
        },
        {
            "role": "user",
            "content": f"""
Hieronder staat ruwe Coursera-content van module 1.

Maak hiervan een eerste Daan-versie.
Gebruik nog niet de hele module, maar test op dit eerste stuk.

RUWE CONTENT:
{course_sample}
""",
        },
    ],
)

OUTPUT_FILE.write_text(response.output_text, encoding="utf-8")

print("✅ Opgeslagen:", OUTPUT_FILE)