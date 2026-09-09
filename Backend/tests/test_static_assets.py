from fastapi.testclient import TestClient

import main
from services.slide_generator import create_slides


def test_generated_slides_can_load_stylesheet():
    create_slides(
        text="Introduction\n\nThis is a sample lesson.",
        title="Sample lesson",
        template="education",
    )

    client = TestClient(main.app)
    response = client.get("/static/css/education.css")

    assert response.status_code == 200
    assert "--bg" in response.text

    html = open("generated/generated_slides.html", encoding="utf-8").read()
    assert "../static/css/education.css" in html


