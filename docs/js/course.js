// Lesnavigatie voor één cursus (?course=<slug>). Lessen zonder vertaling zijn
// nog gewoon te openen — de reader toont dan een duidelijke "nog niet
// vertaald"-status in plaats van de les te verbergen, zodat de hele
// cursusstructuur altijd zichtbaar is.

const params = new URLSearchParams(window.location.search);
const courseSlug = params.get("course");

function renderLessonRow(lesson, courseSlug) {
    const statusText = lesson.translated ? "Klaar om te lezen" : "Nog te vertalen";
    const rowClass = lesson.translated ? "lesson-row is-translated" : "lesson-row";

    return `<a class="${rowClass}" href="lesson.html?course=${encodeURIComponent(courseSlug)}&lesson=${encodeURIComponent(lesson.slug)}">
        <span class="lesson-index">${lesson.order}</span>
        <span class="lesson-title">${lesson.title}</span>
        <span class="lesson-status">${statusText}</span>
    </a>`;
}

if (!courseSlug) {
    document.getElementById("lesson-list").innerHTML =
        `<div class="empty-state"><span class="empty-emoji">⚠️</span>Geen cursus opgegeven.</div>`;
} else {
    loadManifest()
        .then((manifest) => {
            const course = findCourse(manifest, courseSlug);

            if (!course) {
                document.getElementById("course-header").innerHTML = `<h1>Cursus niet gevonden</h1>`;
                document.getElementById("lesson-list").innerHTML = "";
                return;
            }

            const translated = course.lessons.filter((l) => l.translated).length;
            const subtitle = course.lessons.length === 0
                ? "Deze cursus is nog niet verzameld."
                : `${translated} van de ${course.lessons.length} lessen al vertaald naar jouw leerstijl.`;

            document.getElementById("course-header").innerHTML = `
                <h1>${course.title}</h1>
                <p>${subtitle}</p>
            `;

            const list = document.getElementById("lesson-list");
            if (course.lessons.length === 0) {
                list.innerHTML = `<div class="empty-state"><span class="empty-emoji">🌱</span>Deze cursus is nog niet verzameld.</div>`;
            } else {
                list.innerHTML = course.lessons
                    .map((lesson) => renderLessonRow(lesson, courseSlug))
                    .join("");
            }
        })
        .catch((err) => {
            document.getElementById("lesson-list").innerHTML =
                `<div class="empty-state"><span class="empty-emoji">⚠️</span>Kon de lessen niet laden.<br>${err.message}</div>`;
        });
}
