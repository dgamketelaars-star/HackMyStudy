from openai import OpenAI

import config

# LET OP: dit is nog de oorspronkelijke proof-of-concept (hele cursus afgekapt
# op 15.000 tekens, niet per module/les) — bewust ongewijzigd gelaten. Zie
# PIPELINE.md voor de openstaande beslissing over de echte vertaalgranulariteit
# (per les vs. per module) voordat dit script de echte vertaalstap wordt.
SLUG = "microsoft-enterprise-product-management-fundamentals"

client = OpenAI()

PROMPT_FILE = config.DAAN_PROMPT_MD
COURSE_FILE = config.raw_md(SLUG)
OUTPUT_FILE = config.course_dir(SLUG) / "module_1_daan_test.md"

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