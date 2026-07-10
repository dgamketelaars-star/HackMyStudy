// Luistermodus: leest de vertaalde module hardop voor via de browser-eigen
// Web Speech API (SpeechSynthesis) — geen server, geen kosten, geen nieuwe
// account. Zie PIPELINE.md voor waarom dit (voor nu) de juiste keuze is en
// wat de bekende beperkingen zijn.
//
// Belangrijk: leest NOOIT de ruwe Markdown voor. `prepareForSpeech()` is de
// speech-preparation-laag die presentatie-elementen (TOOLVERKENNING-markers,
// Mermaid-blokken, tabellen, Markdown-opmaaktekens) verwijdert of vervangt
// door een korte gesproken aankondiging, vóórdat er iets naar de synthesizer
// gaat.

const SPEECH_CHUNK_MAX_CHARS = 220;
const CHARS_PER_SECOND_AT_RATE_1 = 14; // ruwe schatting voor Nederlandse spraak, zie documentatie
const SEEK_BACK_SECONDS = 15;

function stripToolverkenningMarkers(text) {
    // Verwijdert alleen de markerregels zelf (=== TOOLVERKENNING === / EINDE),
    // niet de inhoud ertussen — die is gewoon leerstof en leest prima voor.
    return text
        .replace(/^={3,5}\s*TOOLVERKENNING\s*={0,5}\s*$/gim, "Even een tool bekijken.")
        .replace(/^={3,5}\s*EINDE TOOLVERKENNING\s*={0,5}\s*$/gim, "");
}

function stripMermaidBlocks(text) {
    return text.replace(/```mermaid[\s\S]*?```/g, "\nZie het schema in de tekst.\n");
}

function stripTablesForSpeech(text) {
    // Een Markdown-tabel bestaat uit opeenvolgende regels met "|"; vervang het
    // hele blok door één gesproken aankondiging in plaats van cellen voor te lezen.
    const lines = text.split("\n");
    const out = [];
    let i = 0;
    while (i < lines.length) {
        if (lines[i].includes("|") && lines[i].trim().startsWith("|")) {
            while (i < lines.length && lines[i].includes("|")) i += 1;
            out.push("Zie de tabel in de tekst.");
        } else {
            out.push(lines[i]);
            i += 1;
        }
    }
    return out.join("\n");
}

function stripMarkdownSyntax(text) {
    return text
        .replace(/!\[[^\]]*\]\([^)]*\)/g, "") // afbeeldingen
        .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1") // links -> alleen linktekst
        .replace(/^#{1,6}\s*/gm, "") // heading-markers
        .replace(/\*\*([^*]+)\*\*/g, "$1") // bold
        .replace(/\*([^*]+)\*/g, "$1") // italic
        .replace(/__([^_]+)__/g, "$1")
        .replace(/(?<!\w)_([^_]+)_(?!\w)/g, "$1")
        .replace(/^>\s?/gm, "") // blockquote
        .replace(/^-{3,}$/gm, "") // horizontale lijn
        .replace(/^[ \t]*[-*]\s+/gm, "") // ongeordende lijst-markers
        .replace(/^[ \t]*\d+\.\s+/gm, "") // geordende lijst-markers
        .replace(/`([^`]+)`/g, "$1") // inline code
        .replace(/[ \t]+/g, " ")
        .replace(/\n{2,}/g, ". ")
        .replace(/\n/g, ". ");
}

/** Zet vertaalde module-markdown om in platte, spreekbare tekst. */
function prepareForSpeech(markdown) {
    let text = markdown.replace(/\r\n/g, "\n");
    text = text.replace(/^#[^\n]*\n+/, ""); // leidende titel (staat al in de pagina-header)
    text = stripMermaidBlocks(text);
    text = stripTablesForSpeech(text);
    text = stripToolverkenningMarkers(text);
    text = stripMarkdownSyntax(text);
    return text.replace(/\s{2,}/g, " ").trim();
}

/** Splitst platte tekst in spreekbare stukken op zinsgrenzen, elk onder de
 * maximale chunkgrootte (browsers knippen erg lange utterances soms af). */
function splitIntoSpeechChunks(text, maxChars = SPEECH_CHUNK_MAX_CHARS) {
    const sentences = text.match(/[^.!?]+[.!?]*\s*/g) || [text];
    const chunks = [];
    let current = "";
    for (const sentence of sentences) {
        if (current.length + sentence.length > maxChars && current) {
            chunks.push(current.trim());
            current = sentence;
        } else {
            current += sentence;
        }
    }
    if (current.trim()) chunks.push(current.trim());
    return chunks.filter((c) => c.length > 0);
}

class ModulePlayer {
    constructor(text, storageKey) {
        this.chunks = splitIntoSpeechChunks(text);
        this.storageKey = storageKey;
        this.chunkIndex = 0;
        this.charOffset = 0;
        this.rate = 1;
        this.playing = false;
        this.voice = null;
        this.chunkStartedAt = 0;
        this.onStateChange = () => {};
        this._loadPosition();
        this._pickVoice();
    }

    get supported() {
        return typeof window.speechSynthesis !== "undefined" && this.chunks.length > 0;
    }

    _pickVoice() {
        const pick = () => {
            const voices = window.speechSynthesis.getVoices();
            this.voice = voices.find((v) => v.lang.toLowerCase().startsWith("nl")) || null;
        };
        pick();
        if (!this.voice && "onvoiceschanged" in window.speechSynthesis) {
            window.speechSynthesis.onvoiceschanged = pick;
        }
    }

    _loadPosition() {
        try {
            const raw = localStorage.getItem(this.storageKey);
            if (raw) {
                const saved = JSON.parse(raw);
                this.chunkIndex = Math.min(saved.chunkIndex || 0, this.chunks.length - 1);
                this.charOffset = saved.charOffset || 0;
                this.rate = saved.rate || 1;
            }
        } catch (err) {
            // corrupte/oude data, negeren en van voor af aan beginnen
        }
    }

    _savePosition() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify({
                chunkIndex: this.chunkIndex,
                charOffset: this.charOffset,
                rate: this.rate,
            }));
        } catch (err) {
            // localStorage kan vol/uitgeschakeld zijn — luistermodus werkt dan
            // gewoon door zonder positie te onthouden
        }
    }

    play() {
        if (!this.supported || this.playing) return;
        this.playing = true;
        this._speakCurrentChunk();
        this.onStateChange();
    }

    pause() {
        this.playing = false;
        window.speechSynthesis.cancel();
        this.onStateChange();
    }

    restart() {
        this.pause();
        this.chunkIndex = 0;
        this.charOffset = 0;
        this._savePosition();
        this.onStateChange();
    }

    setRate(rate) {
        this.rate = rate;
        this._savePosition();
        if (this.playing) {
            window.speechSynthesis.cancel();
            this._speakCurrentChunk();
        }
        this.onStateChange();
    }

    seekBack() {
        const charsPerSecond = CHARS_PER_SECOND_AT_RATE_1 * this.rate;
        const elapsedSeconds = (Date.now() - this.chunkStartedAt) / 1000;
        const charsIntoChunk = this.charOffset + Math.round(elapsedSeconds * charsPerSecond);
        const backChars = Math.round(SEEK_BACK_SECONDS * charsPerSecond);
        let targetChar = charsIntoChunk - backChars;

        const wasPlaying = this.playing;
        window.speechSynthesis.cancel();

        while (targetChar < 0 && this.chunkIndex > 0) {
            this.chunkIndex -= 1;
            targetChar += this.chunks[this.chunkIndex].length;
        }
        this.charOffset = Math.max(0, targetChar);
        this._savePosition();

        if (wasPlaying) {
            this._speakCurrentChunk();
        }
        this.onStateChange();
    }

    _speakCurrentChunk() {
        if (this.chunkIndex >= this.chunks.length) {
            this.playing = false;
            this.chunkIndex = 0;
            this.charOffset = 0;
            this._savePosition();
            this.onStateChange();
            return;
        }

        const fullChunk = this.chunks[this.chunkIndex];
        const textToSpeak = fullChunk.slice(this.charOffset);
        const utterance = new SpeechSynthesisUtterance(textToSpeak || fullChunk);
        utterance.lang = "nl-NL";
        utterance.rate = this.rate;
        if (this.voice) utterance.voice = this.voice;

        this.chunkStartedAt = Date.now();

        utterance.onend = () => {
            if (!this.playing) return; // was gepauzeerd/gestopt
            this.chunkIndex += 1;
            this.charOffset = 0;
            this._savePosition();
            this.onStateChange();
            this._speakCurrentChunk();
        };
        utterance.onerror = () => {
            this.playing = false;
            this.onStateChange();
        };

        window.speechSynthesis.speak(utterance);
    }

    get progressLabel() {
        return `Onderdeel ${Math.min(this.chunkIndex + 1, this.chunks.length)} van ${this.chunks.length}`;
    }
}

/** Koppelt de audio-controlbalk in de DOM aan een ModulePlayer voor de gegeven
 * module-markdown. Doet niets (en verbergt de balk) als de browser geen
 * SpeechSynthesis ondersteunt. */
function initAudioBar(rawMarkdown, storageKey) {
    const bar = document.getElementById("audio-bar");
    if (!bar) return;

    if (typeof window.speechSynthesis === "undefined") {
        bar.hidden = true;
        return;
    }

    const speechText = prepareForSpeech(rawMarkdown);
    const player = new ModulePlayer(speechText, storageKey);

    if (!player.supported) {
        bar.hidden = true;
        return;
    }

    bar.hidden = false;
    const playBtn = document.getElementById("audio-play-btn");
    const backBtn = document.getElementById("audio-back-btn");
    const rateSelect = document.getElementById("audio-rate-select");
    const progressEl = document.getElementById("audio-progress");

    rateSelect.value = String(player.rate);

    player.onStateChange = () => {
        playBtn.textContent = player.playing ? "⏸" : "▶";
        playBtn.setAttribute("aria-label", player.playing ? "Pauzeren" : "Afspelen");
        progressEl.textContent = player.progressLabel;
    };
    player.onStateChange();

    playBtn.addEventListener("click", () => {
        if (player.playing) {
            player.pause();
        } else {
            player.play();
        }
    });

    backBtn.addEventListener("click", () => player.seekBack());

    rateSelect.addEventListener("change", () => {
        player.setRate(parseFloat(rateSelect.value));
    });

    // Stop met voorlezen als je de pagina verlaat (anders blijft de browser
    // op de achtergrond doorpraten).
    window.addEventListener("beforeunload", () => player.pause());
}
