// Cursusoverzicht: toont elke cursus uit manifest.json als kaart. Cursussen
// zonder verzamelde lessen (status "coming_soon") zijn zichtbaar maar niet
// klikbaar — zo zie je altijd dat het hele certificaat 5 cursussen telt.

function renderCourseCard(course) {
    const total = course.lessons.length;
    const translated = course.lessons.filter((l) => l.translated).length;
    const isAvailable = course.status === "available";
    const pct = total > 0 ? Math.round((translated / total) * 100) : 0;

    const badge = isAvailable
        ? `<span class="badge">${translated}/${total} vertaald</span>`
        : `<span class="badge is-muted">Binnenkort</span>`;

    const meta = isAvailable
        ? `<div class="progress-track"><div class="progress-fill" style="width:${pct}%"></div></div>
           <p class="course-card-meta">${total} lessen gevonden</p>`
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
