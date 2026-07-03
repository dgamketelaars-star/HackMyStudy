// Cursusoverzicht: toont elke cursus uit manifest.json als kaart. Cursussen
// zonder verzamelde modules (status "coming_soon") zijn zichtbaar maar niet
// klikbaar — zo zie je altijd dat het hele certificaat 5 cursussen telt.
// Voortgang wordt geteld in modules, niet losse lessen: de vertaalstap werkt
// op moduleniveau (zie PIPELINE.md).

function renderCourseCard(course) {
    const total = course.modules.length;
    const translated = course.modules.filter((m) => m.translated).length;
    const totalLessons = course.modules.reduce((sum, m) => sum + m.lesson_count, 0);
    const isAvailable = course.status === "available";
    const pct = total > 0 ? Math.round((translated / total) * 100) : 0;

    const badge = isAvailable
        ? `<span class="badge">${translated}/${total} vertaald</span>`
        : `<span class="badge is-muted">Binnenkort</span>`;

    const meta = isAvailable
        ? `<div class="progress-track"><div class="progress-fill" style="width:${pct}%"></div></div>
           <p class="course-card-meta">${total} modules, ${totalLessons} lessen</p>`
        : `<p class="course-card-meta">Nog niet verzameld</p>`;

    const tag = isAvailable ? "a" : "div";
    const href = isAvailable ? ` href="course.html?course=${encodeURIComponent(course.slug)}"` : "";
    const cardClass = isAvailable ? "course-card is-available" : "course-card is-soon";

    return `<${tag} class="${cardClass}"${href}>
        <div class="course-card-top">
            <h2>${course.title}</h2>
            ${badge}
        </div>
        ${meta}
    </${tag}>`;
}

loadManifest()
    .then((manifest) => {
        const grid = document.getElementById("course-grid");
        grid.innerHTML = manifest.courses.map(renderCourseCard).join("");
    })
    .catch((err) => {
        document.getElementById("course-grid").innerHTML =
            `<div class="empty-state"><span class="empty-emoji">⚠️</span>Kon de cursussen niet laden.<br>${err.message}</div>`;
    });
