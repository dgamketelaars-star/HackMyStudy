// Reader voor één module (?course=<slug>&module=<nummer>). Haalt de vertaalde
// markdown op uit content/<course>/module-<nummer>.md als die bestaat; anders
// een duidelijke "nog niet vertaald"-melding in plaats van een foutmelding of
// lege pagina. Navigatie is hier op moduleniveau (prev/next module), niet per
// losse les — de vertaalstap werkt op de hele module tegelijk.

const params = new URLSearchParams(window.location.search);
const courseSlug = params.get("course");
const moduleNumber = parseInt(params.get("module"), 10);

function renderNav(course, currentIndex) {
    const prev = currentIndex > 0 ? course.modules[currentIndex - 1] : null;
    const next = currentIndex < course.modules.length - 1 ? course.modules[currentIndex + 1] : null;

    const moduleUrl = (module) =>
        `module.html?course=${encodeURIComponent(courseSlug)}&module=${module.number}`;

    const prevHtml = prev
        ? `<a class="prev" href="${moduleUrl(prev)}"><span class="nav-label">Vorige module</span>${prev.title}</a>`
        : `<span></span>`;

    const nextHtml = next
        ? `<a class="next" href="${moduleUrl(next)}"><span class="nav-label">Volgende module</span>${next.title}</a>`
        : `<a class="next" href="course.html?course=${encodeURIComponent(courseSlug)}"><span class="nav-label">Klaar</span>Terug naar overzicht</a>`;

    document.getElementById("reader-nav").innerHTML = prevHtml + nextHtml;
}

async function renderModule() {
    if (!courseSlug || !moduleNumber) {
        document.getElementById("reader-content").innerHTML =
            `<div class="empty-state"><span class="empty-emoji">⚠️</span>Geen module opgegeven.</div>`;
        return;
    }

    const manifest = await loadManifest();
    const course = findCourse(manifest, courseSlug);

    if (!course) {
        document.getElementById("reader-header").innerHTML = `<h1>Cursus niet gevonden</h1>`;
        return;
    }

    document.getElementById("topbar").innerHTML =
        `<a class="back" href="course.html?course=${encodeURIComponent(courseSlug)}">← ${course.title}</a>`;

    const module = findModule(course, moduleNumber);
    if (!module) {
        document.getElementById("reader-header").innerHTML = `<h1>Module niet gevonden</h1>`;
        return;
    }

    const lessonWord = module.lesson_count === 1 ? "les" : "lessen";
    document.getElementById("reader-header").innerHTML = `
        <p class="reader-eyebrow">${course.title}</p>
        <h1>${module.title}</h1>
        <p>${module.lesson_count} ${lessonWord} uit de originele cursus, samengevoegd tot één leerroute.</p>
    `;

    const contentEl = document.getElementById("reader-content");

    if (!module.translated) {
        contentEl.innerHTML = `
            <div class="empty-state">
                <span class="empty-emoji">🛠️</span>
                Deze module is nog niet vertaald naar jouw leerstijl.
            </div>
        `;
    } else {
        const response = await fetch(`content/${encodeURIComponent(courseSlug)}/module-${module.number}.md`);
        if (!response.ok) {
            contentEl.innerHTML = `<div class="empty-state"><span class="empty-emoji">⚠️</span>Kon deze module niet laden.</div>`;
        } else {
            const markdown = (await response.text()).replace(/\r\n/g, "\n");
            // de titel staat al in reader-header hierboven; voorkom een dubbele
            // weergave door een leidende "# Titel"-regel uit de markdown te strippen
            const withoutLeadingTitle = markdown.replace(/^#[^\n]*\n+/, "");
            contentEl.innerHTML = marked.parse(withoutLeadingTitle);
            await renderVisuals(contentEl);

            const storageKey = `hackmystudy-audio-${courseSlug}-${module.number}`;
            initAudioBar(markdown, storageKey);
            initQaPanel({
                courseSlug,
                courseTitle: course.title,
                moduleNumber: module.number,
                moduleTitle: module.title,
                moduleMarkdown: markdown,
            });
        }
    }

    const currentIndex = course.modules.findIndex((m) => m.number === moduleNumber);
    renderNav(course, currentIndex);
}

renderModule().catch((err) => {
    document.getElementById("reader-content").innerHTML =
        `<div class="empty-state"><span class="empty-emoji">⚠️</span>Er ging iets mis.<br>${err.message}</div>`;
});
