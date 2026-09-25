import os
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app import app


@pytest.fixture(scope="module")
def client():
    with patch("api.chat.generate_response", new_callable=AsyncMock) as mock_gen, \
         patch("api.chat.generate_response_stream") as mock_stream:
        mock_gen.return_value = "Encapsulation is bundling data and methods."
        
        async def mock_stream_gen(*args, **kwargs):
            yield "Polymorphism allows method overriding."
        mock_stream.side_effect = mock_stream_gen

        with TestClient(app) as test_client:
            yield test_client


def test_home_endpoint(client):
    """Verify that home endpoint loads correctly or returns status JSON."""
    response = client.get("/")
    assert response.status_code == 200
    if response.headers.get("content-type") == "application/json":
        data = response.json()
        assert "message" in data


def test_ask_empty_question(client):
    """Verify that empty questions are rejected with 400 Bad Request."""
    response = client.post(
        "/ask",
        json={
            "student_id": "test_stud_1",
            "lecture_id": "java001",
            "question": ""
        }
    )
    assert response.status_code == 400
    assert "detail" in response.json()


def test_ask_path_traversal(client):
    """Verify that path traversal in lecture_id is safely handled."""
    response = client.post(
        "/ask",
        json={
            "student_id": "test_stud_1",
            "lecture_id": "../../etc/passwd",
            "question": "What is encapsulation?"
        }
    )
    assert response.status_code == 200
    assert "answer" in response.json()


def test_stream_ask_endpoint(client):
    """Verify that streaming ask endpoint yields SSE data packages."""
    response = client.post(
        "/ask/stream",
        json={
            "student_id": "test_stud_1",
            "lecture_id": "java001",
            "question": "Define polymorphism."
        }
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    
    content = response.content.decode("utf-8")
    assert "data:" in content


def test_translate_empty_text(client):
    """Verify empty text translation is rejected."""
    response = client.post(
        "/api/translate",
        json={
            "text": "",
            "target_lang": "Telugu"
        }
    )
    assert response.status_code == 400


def test_notes_crud_endpoints(client):
    """Verify notes API creation, retrieval, and deletion."""
    # Create note
    create_resp = client.post(
        "/api/notes",
        json={
            "student_id": "test_student",
            "title": "UnitTest Note",
            "content": "This is a unit test note."
        }
    )
    assert create_resp.status_code == 200
    note_data = create_resp.json()
    assert note_data["title"] == "UnitTest Note"
    note_id = note_data["id"]

    # Get notes
    get_resp = client.get("/api/notes?student_id=test_student")
    assert get_resp.status_code == 200
    notes = get_resp.json()
    assert any(n["id"] == note_id for n in notes)

    # Delete note
    del_resp = client.delete(f"/api/notes/{note_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True


