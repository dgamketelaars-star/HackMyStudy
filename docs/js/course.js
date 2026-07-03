// Modulenavigatie voor één cursus (?course=<slug>). Modules zonder vertaling
// zijn nog gewoon te openen — de reader toont dan een duidelijke "nog niet
// vertaald"-status in plaats van de module te verbergen, zodat de hele
// cursusstructuur altijd zichtbaar is. De vertaalstap werkt op moduleniveau
// (een hele module wordt in samenhang vertaald, niet losse lessen), dus dat
// is ook de eenheid waarop je hier navigeert.

const params = new URLSearchParams(window.location.search);
const courseSlug = params.get("course");

function renderModuleRow(module, courseSlug) {
    const statusText = module.translated ? "Klaar om te lezen" : "Nog te vertalen";
    const rowClass = module.translated ? "lesson-row is-translated" : "lesson-row";
    const lessonWord = module.lesson_count === 1 ? "les" : "lessen";

    return `<a class="${rowClass}" href="module.html?course=${encodeURIComponent(courseSlug)}&module=${module.number}">
        <span class="lesson-index">${module.number}</span>
        <span class="lesson-title">${module.title}<br><small>${module.lesson_count} ${lessonWord}</small></span>
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

            const translated = course.modules.filter((m) => m.translated).length;
            const subtitle = course.modules.length === 0
                ? "Deze cursus is nog niet verzameld."
                : `${translated} van de ${course.modules.length} modules al vertaald naar jouw leerstijl.`;

            document.getElementById("course-header").innerHTML = `
                <h1>${course.title}</h1>
                <p>${subtitle}</p>
            `;

            const list = document.getElementById("lesson-list");
            if (course.modules.length === 0) {
                list.innerHTML = `<div class="empty-state"><span class="empty-emoji">🌱</span>Deze cursus is nog niet verzameld.</div>`;
            } else {
                list.innerHTML = course.modules
                    .map((module) => renderModuleRow(module, courseSlug))
                    .join("");
            }
        })
        .catch((err) => {
            document.getElementById("lesson-list").innerHTML =
                `<div class="empty-state"><span class="empty-emoji">⚠️</span>Kon de modules niet laden.<br>${err.message}</div>`;
        });
}
