fetch("../content/module1.md")
    .then(response => response.text())
    .then(text => {
        document.getElementById("lesson").innerHTML = marked.parse(text);
    });