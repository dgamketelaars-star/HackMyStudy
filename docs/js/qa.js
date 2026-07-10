// Interactief vragenpaneel tijdens het lezen van een module. Lost de
// "nep-interactiviteit" op: de vertaalde tekst stelt regelmatig een directe
// vraag aan de lezer ("Snap je waarom...?"), maar tot nu toe kon je daar niks
// mee. Dit paneel is altijd beschikbaar tijdens het lezen (los van of de
// tekst toevallig een vraag stelt), met een paar snelle acties + een vrij
// tekstveld.
//
// BELANGRIJK: dit bestand bouwt alleen de front-end (paneel, context,
// verzoek-payload). Het daadwerkelijk BEANTWOORDEN vereist een backend die de
// OpenAI-key serverside bewaart (zie PIPELINE.md, sectie "Interactief
// vragen"). Zonder die backend toont het paneel een eerlijke melding in
// plaats van te doen alsof er een antwoord komt.

const QA_LOCAL_ENDPOINT = "http://127.0.0.1:8765/ask";
const QA_LOCAL_PROBE_TIMEOUT_MS = 1200;

let qaContext = null;
let qaSectionTexts = [];
let qaCurrentSectionIndex = 0;
let qaConversation = [];
let qaLocalServerAvailable = null; // null = nog niet gecontroleerd

function splitModuleIntoSections(markdown) {
    const withoutLeadingTitle = markdown.replace(/^#[^\n]*\n+/, "");
    const parts = withoutLeadingTitle.split(/^##\s+/m).filter((p) => p.trim());
    return parts.map((part) => {
        const [firstLine, ...rest] = part.split("\n");
        return { title: firstLine.trim(), text: rest.join("\n").trim() };
    });
}

function trackCurrentSection() {
    const headings = document.querySelectorAll("#reader-content h2");
    if (headings.length === 0) return;

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const idx = Array.from(headings).indexOf(entry.target);
                    if (idx !== -1) qaCurrentSectionIndex = idx;
                }
            });
        },
        { rootMargin: "-10% 0px -70% 0px" }
    );
    headings.forEach((h) => observer.observe(h));
}

async function probeLocalServer() {
    if (qaLocalServerAvailable !== null) return qaLocalServerAvailable;
    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), QA_LOCAL_PROBE_TIMEOUT_MS);
        const response = await fetch(QA_LOCAL_ENDPOINT.replace("/ask", "/health"), {
            signal: controller.signal,
        });
        clearTimeout(timeout);
        qaLocalServerAvailable = response.ok;
    } catch (err) {
        qaLocalServerAvailable = false;
    }
    return qaLocalServerAvailable;
}

function addMessage(role, text) {
    const messagesEl = document.getElementById("qa-messages");
    const bubble = document.createElement("div");
    bubble.className = `qa-bubble qa-bubble-${role}`;
    bubble.textContent = text;
    messagesEl.appendChild(bubble);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return bubble;
}

async function askQuestion(question) {
    if (!question.trim()) return;
    addMessage("user", question);
    qaConversation.push({ role: "user", content: question });

    const thinkingBubble = addMessage("assistant", "Even denken…");
    thinkingBubble.classList.add("qa-bubble-thinking");

    const available = await probeLocalServer();

    if (!available) {
        thinkingBubble.remove();
        addMessage(
            "assistant",
            "Deze functie heeft nog geen actieve verbinding met een AI-model. " +
            "Start lokaal 'python scripts/qa_server.py' (met je OPENAI_API_KEY " +
            "ingesteld) als je nu op je eigen computer leest, of zie PIPELINE.md " +
            "voor de opties om dit ook vanaf je telefoon te laten werken."
        );
        return;
    }

    const section = qaSectionTexts[qaCurrentSectionIndex] || { title: qaContext.moduleTitle, text: "" };

    try {
        const response = await fetch(QA_LOCAL_ENDPOINT, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                course_title: qaContext.courseTitle,
                module_title: qaContext.moduleTitle,
                section_title: section.title,
                section_text: section.text,
                question,
                conversation: qaConversation.slice(-6),
            }),
        });
        thinkingBubble.remove();
        if (!response.ok) {
            addMessage("assistant", `De lokale server gaf een fout terug (${response.status}).`);
            return;
        }
        const data = await response.json();
        addMessage("assistant", data.answer);
        qaConversation.push({ role: "assistant", content: data.answer });
    } catch (err) {
        thinkingBubble.remove();
        addMessage("assistant", "Kon geen antwoord ophalen: " + err.message);
    }
}

function initQaPanel(context) {
    const fab = document.getElementById("qa-fab-btn");
    const panel = document.getElementById("qa-panel");
    if (!fab || !panel) return;

    qaContext = context;
    qaSectionTexts = splitModuleIntoSections(context.moduleMarkdown);
    qaConversation = [];

    fab.hidden = false;
    trackCurrentSection();

    fab.addEventListener("click", () => {
        panel.hidden = !panel.hidden;
        if (!panel.hidden) document.getElementById("qa-input").focus();
    });

    document.getElementById("qa-close-btn").addEventListener("click", () => {
        panel.hidden = true;
    });

    document.querySelectorAll(".qa-quick-btn").forEach((btn) => {
        btn.addEventListener("click", () => askQuestion(btn.dataset.question));
    });

    const form = document.getElementById("qa-form");
    form.addEventListener("submit", (e) => {
        e.preventDefault();
        const input = document.getElementById("qa-input");
        const question = input.value;
        input.value = "";
        askQuestion(question);
    });
}
