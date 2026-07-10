// Rendert Mermaid-diagrammen die de vertaalpipeline als ```mermaid-codeblok in de
// module-markdown zet (zie prompts/daan_module_prompt.md, sectie "Visuals").
// marked.js zet zo'n codeblok om in <pre><code class="language-mermaid">...</code></pre>;
// Mermaid verwacht zelf <div class="mermaid">ruwe-diagramtekst</div>, dus we zetten
// dat hier om vóórdat we mermaid.run() aanroepen. Gewone Markdown-tabellen (voor
// vergelijkingen) hebben geen speciale behandeling nodig — marked.js rendert die al
// als normale <table>, en de reader-content-CSS stylet ze.

function prepareMermaidBlocks(containerEl) {
    const codeBlocks = containerEl.querySelectorAll("code.language-mermaid");
    let count = 0;
    codeBlocks.forEach((code) => {
        const pre = code.closest("pre");
        if (!pre) return;
        const div = document.createElement("div");
        div.className = "mermaid";
        div.textContent = code.textContent;
        pre.replaceWith(div);
        count += 1;
    });
    return count;
}

async function renderVisuals(containerEl) {
    const count = prepareMermaidBlocks(containerEl);
    if (count === 0 || typeof mermaid === "undefined") {
        return;
    }
    mermaid.initialize({
        startOnLoad: false,
        theme: "dark",
        themeVariables: {
            darkMode: true,
            background: "#1a1a1d",
            primaryColor: "#1a1a1d",
            primaryTextColor: "#f3f3f1",
            primaryBorderColor: "#00c853",
            lineColor: "#57e08c",
            secondaryColor: "#232327",
            tertiaryColor: "#232327",
        },
        securityLevel: "strict",
    });
    try {
        await mermaid.run({ querySelector: ".mermaid" });
    } catch (err) {
        console.error("Mermaid-rendering mislukt:", err);
    }
}
