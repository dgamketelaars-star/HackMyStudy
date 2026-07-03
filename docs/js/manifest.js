// Kleine gedeelde helper: haalt content/manifest.json op (relatief aan de
// pagina die het aanroept — elke pagina staat direct in docs/, dus
// "content/manifest.json" werkt overal).
async function loadManifest() {
    const response = await fetch("content/manifest.json");
    if (!response.ok) {
        throw new Error("Kon manifest.json niet laden (" + response.status + ")");
    }
    return response.json();
}

function findCourse(manifest, slug) {
    return manifest.courses.find((c) => c.slug === slug);
}

function findLesson(course, slug) {
    return course.lessons.find((l) => l.slug === slug);
}
