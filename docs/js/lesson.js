// Reader voor één les (?course=<slug>&lesson=<slug>). Haalt de vertaalde
// markdown op uit content/<course>/<lesson>.md als die bestaat; anders een
// duidelijke "nog niet vertaald"-melding in plaats van een foutmelding of
// lege pagina.

const params = new URLSearchParams(window.location.search);
const courseSlug = params.get("course");
const lessonSlug = params.get("lesson");

function renderNav(course, currentIndex) {
    const prev = currentIndex > 0 ? course.lessons[currentIndex - 1] : null;
    const next = currentIndex < course.lessons.length - 1 ? course.lessons[currentIndex + 1] : null;

    const lessonUrl = (lesson) =>
        `lesson.html?course=${encodeURIComponent(courseSlug)}&lesson=${encodeURIComponent(lesson.slug)}`;

    const prevHtml = prev
        ? `<a class="prev" href="${lessonUrl(prev)}"><span class="nav-label">Vorige</span>${prev.title}</a>`
        : `<span></span>`;

    const nextHtml = next
        ? `<a class="next" href="${lessonUrl(next)}"><span class="nav-label">Volgende</span>${next.title}</a>`
        : `<a class="next" href="course.html?course=${encodeURIComponent(courseSlug)}"><span class="nav-label">Klaar</span>Terug naar overzicht</a>`;

    document.getElementById("reader-nav").innerHTML = prevHtml + nextHtml;
}

async function renderLesson() {
    if (!courseSlug || !lessonSlug) {
        document.getElementById("reader-content").innerHTML =
            `<div class="empty-state"><span class="empty-emoji">⚠️</span>Geen les opgegeven.</div>`;
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

    const lesson = findLesson(course, lessonSlug);
    if (!lesson) {
        document.getElementById("reader-header").innerHTML = `<h1>Les niet gevonden</h1>`;
        return;
    }

    const moduleLabel = lesson.module ? `Module ${lesson.module}` : course.title;
    document.getElementById("reader-header").innerHTML = `
        <p class="reader-eyebrow">${moduleLabel}</p>
        <h1>${lesson.title}</h1>
    `;

    const contentEl = document.getElementById("reader-content");

    if (!lesson.translated) {
        contentEl.innerHTML = `
            <div class="empty-state">
                <span class="empty-emoji">🛠️</span>
                Deze les is nog niet vertaald naar jouw leerstijl.
            </div>
        `;
    } else {
        const response = await fetch(`content/${encodeURIComponent(courseSlug)}/${encodeURIComponent(lessonSlug)}.md`);
        if (!response.ok) {
            contentEl.innerHTML = `<div class="empty-state"><span class="empty-emoji">⚠️</span>Kon deze les niet laden.</div>`;
        } else {
            const markdown = await response.text();
            contentEl.innerHTML = marked.parse(markdown);
        }
    }

    const currentIndex = course.lessons.findIndex((l) => l.slug === lessonSlug);
    renderNav(course, currentIndex);
}

renderLesson().catch((err) => {
    document.getElementById("reader-content").innerHTML =
        `<div class="empty-state"><span class="empty-emoji">⚠️</span>Er ging iets mis.<br>${err.message}</div>`;
});
