/**
 * VOORBEREID, NIET GEACTIVEERD.
 *
 * Cloudflare Worker die dezelfde /ask-functie als scripts/qa_server.py biedt,
 * maar dan online bereikbaar (dus ook vanaf je telefoon, niet alleen als je
 * eigen computer aanstaat). Dit bestand is klaar om te deployen zodra je dat
 * wilt — er is hier NIETS aangemaakt of geactiveerd. Dat vereist een
 * Cloudflare-account (gratis tier is ruim voldoende voor persoonlijk
 * gebruik) en het toevoegen van je OPENAI_API_KEY als secret, wat ik niet
 * zonder jouw akkoord doe (nieuw account + credentials).
 *
 * Deploy-stappen (samengevat, zie ook PIPELINE.md):
 *   1. Maak een gratis Cloudflare-account (workers.cloudflare.com).
 *   2. Installeer wrangler: npm install -g wrangler
 *   3. wrangler login
 *   4. wrangler secret put OPENAI_API_KEY   (plak je key, wordt niet in code opgeslagen)
 *   5. wrangler deploy deploy/cloudflare-worker-qa.js
 *   6. Vervang QA_LOCAL_ENDPOINT in docs/js/qa.js door de uitgegeven
 *      workers.dev-URL (of een eigen domein).
 *
 * Dit bestand bevat geen key en geen andere secrets.
 */

const ALLOWED_ORIGIN = "*"; // beperk dit tot je eigen GitHub Pages-origin zodra je live gaat

const QA_SYSTEM_PROMPT = `Je bent de interactieve leerbegeleider van HackMyStudy. Je beantwoordt
een vraag die de gebruiker stelt terwijl hij een specifieke, al vertaalde cursusmodule leest. Je
bent geen algemene chatbot, maar de leerbegeleider binnen de context van deze cursus en module.
Antwoord kort, concreet, in gewoon Nederlands, als iemand die naast de gebruiker zit. Je mag extra
uitleg en voorbeelden geven (ook uit de eigen projecten van de gebruiker, zoals HackMyStudy, als
dat relevant is) zolang ze feitelijk correct zijn — vervang de kerninhoud van de module niet
ongemerkt door losse AI-kennis, en maak onderscheid tussen "dit stond in de module" en "dit is
aanvullende uitleg van mij".`;

function corsHeaders() {
    return {
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    };
}

async function handleAsk(request, env) {
    let data;
    try {
        data = await request.json();
    } catch (err) {
        return new Response(JSON.stringify({ error: "ongeldige JSON" }), {
            status: 400,
            headers: { "Content-Type": "application/json", ...corsHeaders() },
        });
    }

    const question = (data.question || "").trim();
    if (!question) {
        return new Response(JSON.stringify({ error: "geen vraag meegegeven" }), {
            status: 400,
            headers: { "Content-Type": "application/json", ...corsHeaders() },
        });
    }

    const conversation = data.conversation || [];
    const historyText = conversation
        .slice(0, -1)
        .map((m) => `${m.role}: ${m.content}`)
        .join("\n");

    const userMessage = `Cursus: ${data.course_title || "?"}
Module: ${data.module_title || "?"}
Onderdeel waar de gebruiker waarschijnlijk leest: ${data.section_title || "?"}

TEKST VAN DIT ONDERDEEL:
${(data.section_text || "").slice(0, 6000)}

${historyText ? "EERDERE BERICHTEN IN DIT GESPREK:\n" + historyText : ""}

VRAAG VAN DE GEBRUIKER:
${question}`;

    const openaiResponse = await fetch("https://api.openai.com/v1/responses", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${env.OPENAI_API_KEY}`,
        },
        body: JSON.stringify({
            model: "gpt-4.1-mini",
            input: [
                { role: "system", content: QA_SYSTEM_PROMPT },
                { role: "user", content: userMessage },
            ],
        }),
    });

    if (!openaiResponse.ok) {
        const errText = await openaiResponse.text();
        return new Response(JSON.stringify({ error: `OpenAI-aanroep mislukt: ${errText}` }), {
            status: 502,
            headers: { "Content-Type": "application/json", ...corsHeaders() },
        });
    }

    const result = await openaiResponse.json();
    return new Response(JSON.stringify({ answer: result.output_text }), {
        status: 200,
        headers: { "Content-Type": "application/json", ...corsHeaders() },
    });
}

export default {
    async fetch(request, env) {
        const url = new URL(request.url);

        if (request.method === "OPTIONS") {
            return new Response(null, { status: 204, headers: corsHeaders() });
        }
        if (url.pathname === "/health") {
            return new Response(JSON.stringify({ status: "ok" }), {
                headers: { "Content-Type": "application/json", ...corsHeaders() },
            });
        }
        if (url.pathname === "/ask" && request.method === "POST") {
            return handleAsk(request, env);
        }
        return new Response(JSON.stringify({ error: "onbekend pad" }), {
            status: 404,
            headers: { "Content-Type": "application/json", ...corsHeaders() },
        });
    },
};
