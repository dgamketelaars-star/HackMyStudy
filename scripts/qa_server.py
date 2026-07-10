"""Lokale Q&A-server voor de interactieve vragenfunctie in de webapp.

Draai dit terwijl je HackMyStudy leest op je eigen computer (`python -m http.server`
in docs/, of gewoon de gedeployde site openen in je browser — beide werken, want
dit is een localhost-only server, los van waar de webapp zelf vandaan komt):

    python scripts/qa_server.py

De webapp (docs/js/qa.js) probeert automatisch http://127.0.0.1:8765 te bereiken
zodra je een vraag stelt. Is deze server niet actief, dan toont de webapp een
duidelijke melding in plaats van een nep-antwoord.

Waarom een lokale server en geen backend online?
Interactieve vragen beantwoorden vereist een echte OpenAI-aanroep per vraag, en
dus een plek die de OPENAI_API_KEY bewaart. docs/ is een statische GitHub
Pages-site zonder server — die key zou dan in de browser (en dus publiek)
terecht moeten komen. Deze lokale server gebruikt de key die je al lokaal hebt
staan (dezelfde als voor de vertaalpipeline) en is alleen bereikbaar vanaf je
eigen machine (127.0.0.1, niet 0.0.0.0) — geen nieuw account, geen nieuwe
kosten-blootstelling. Zie PIPELINE.md voor de opties om dit ook vanaf je
telefoon/onderweg te laten werken (dat vereist wél een externe, gehoste
backend — een bewuste vervolgstap, niet iets wat deze server zelf doet).
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from openai import OpenAI

import config

HOST = "127.0.0.1"  # alleen deze machine, nooit het netwerk
PORT = 8765
MODEL = "gpt-4.1-mini"  # sneller/goedkoper dan gpt-4.1, passend bij interactieve vragen

# CORS: de webapp draait op een ander origin (localhost:8000, of de gepubliceerde
# GitHub Pages-URL) dan deze server (localhost:8765) — browsers blokkeren dat
# standaard tenzij de server het expliciet toestaat. Alleen relevant binnen je
# eigen machine, dus een open CORS-policy hier is geen extra risico.
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

client = OpenAI()
qa_prompt = (config.PROMPTS_DIR / "qa_assistant_prompt.md").read_text(encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"status": "ok"})
        else:
            self._send(404, {"error": "onbekend pad"})

    def do_POST(self):
        if self.path != "/ask":
            self._send(404, {"error": "onbekend pad"})
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            self._send(400, {"error": "ongeldige JSON"})
            return

        question = (data.get("question") or "").strip()
        if not question:
            self._send(400, {"error": "geen vraag meegegeven"})
            return

        conversation = data.get("conversation") or []
        history_text = "\n".join(f"{m['role']}: {m['content']}" for m in conversation[:-1])

        user_message = f"""Cursus: {data.get('course_title', '?')}
Module: {data.get('module_title', '?')}
Onderdeel waar de gebruiker waarschijnlijk leest: {data.get('section_title', '?')}

TEKST VAN DIT ONDERDEEL:
{data.get('section_text', '')[:6000]}

{"EERDERE BERICHTEN IN DIT GESPREK:" + chr(10) + history_text if history_text else ""}

VRAAG VAN DE GEBRUIKER:
{question}
"""

        try:
            response = client.responses.create(
                model=MODEL,
                input=[
                    {"role": "system", "content": qa_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            self._send(200, {"answer": response.output_text})
        except Exception as e:
            self._send(502, {"error": f"OpenAI-aanroep mislukt: {e}"})

    def log_message(self, format, *args):
        print(f"[qa_server] {self.address_string()} - {format % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Q&A-server draait op http://{HOST}:{PORT} (alleen bereikbaar vanaf deze machine)")
    print("Druk Ctrl+C om te stoppen.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nGestopt.")
