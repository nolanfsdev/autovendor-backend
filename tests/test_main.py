import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

@pytest.fixture
def sample_pdf_path():
    return os.path.join(os.path.dirname(__file__), "sample_contract.pdf")

@patch("os.getenv")
@patch("openai.resources.chat.completions.Completions.create")
def test_upload_contract(mock_openai, mock_getenv, sample_pdf_path):
    mock_getenv.side_effect = lambda key: {
        "OPENAI_API_KEY": "fake-key",
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "fake-supabase-key"
    }.get(key, "")

    mock_openai.return_value.choices = [
        type("obj", (object,), {"message": type("msg", (object,), {"content": '{"mock_flag": "mock_value"}'})})()
    ]

    response = client.post("/upload", files={"file": ("sample_contract.pdf", open(sample_pdf_path, "rb"), "application/pdf")})

    assert response.status_code == 200
    assert response.json()["flags"] == {"mock_flag": "mock_value"}
