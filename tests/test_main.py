import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

@pytest.fixture
def sample_pdf_path():
    return os.path.join(os.path.dirname(__file__), "sample_contract.pdf")

@patch("os.getenv")
@patch("openai.resources.chat.completions.Completions.create")
@patch("app.main.create_client")  # 👈 This mocks Supabase
def test_upload_contract(mock_create_client, mock_openai, mock_getenv, sample_pdf_path):
    mock_getenv.side_effect = lambda key: {
        "OPENAI_API_KEY": "fake-key",
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "fake-supabase-key"
    }.get(key, "")

    mock_openai.return_value.choices = [
        type("obj", (object,), {
            "message": type("msg", (object,), {
                "content": '{"mock_flag": "mock_value"}'
            })()
        })()
    ]

    # 👇 Mock Supabase insert call to do nothing
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.insert.return_value.execute.return_value = {}
    mock_create_client.return_value = mock_supabase

    response = client.post(
        "/upload",
        files={"file": ("sample_contract.pdf", open(sample_pdf_path, "rb"), "application/pdf")}
    )

    assert response.status_code == 200
    assert response.json()["flags"] == {"mock_flag": "mock_value"}

def test_upload_invalid_file_type():
    invalid_file = ("not_a_pdf.txt", b"This is not a PDF", "text/plain")
    response = client.post(
        "/upload",
        files={"file": invalid_file}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are supported."

@patch("os.getenv")
def test_upload_missing_supabase_env(mock_getenv, sample_pdf_path):
    # Simulate missing SUPABASE env vars
    mock_getenv.side_effect = lambda key: {
        "OPENAI_API_KEY": "fake-key",
        "SUPABASE_URL": "",
        "SUPABASE_KEY": ""
    }.get(key, "")

    response = client.post(
        "/upload",
        files={"file": ("sample_contract.pdf", open(sample_pdf_path, "rb"), "application/pdf")}
    )

    assert response.status_code == 500
    assert "Missing SUPABASE_URL or SUPABASE_KEY" in response.json()["detail"]

@patch("os.getenv")
@patch("openai.resources.chat.completions.Completions.create")
@patch("app.main.create_client")
def test_upload_openai_error(mock_create_client, mock_openai, mock_getenv, sample_pdf_path):
    mock_getenv.side_effect = lambda key: {
        "OPENAI_API_KEY": "fake-key",
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "fake-supabase-key"
    }.get(key, "")

    # Simulate OpenAI throwing an exception
    mock_openai.side_effect = Exception("OpenAI is down")

    mock_supabase = MagicMock()
    mock_supabase.table.return_value.insert.return_value.execute.return_value = {}
    mock_create_client.return_value = mock_supabase

    response = client.post(
        "/upload",
        files={"file": ("sample_contract.pdf", open(sample_pdf_path, "rb"), "application/pdf")}
    )

    assert response.status_code == 500
    assert "OpenAI API failed" in response.json()["detail"]

from unittest.mock import patch, MagicMock

@patch("os.getenv")
@patch("app.main.create_client")
@patch("fitz.open")
def test_upload_pdf_read_error(mock_fitz_open, mock_create_client, mock_getenv, sample_pdf_path):
    mock_getenv.side_effect = lambda key: {
        "OPENAI_API_KEY": "fake-key",
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "fake-supabase-key"
    }.get(key, "")

    # Force fitz.open to raise an exception
    mock_fitz_open.side_effect = Exception("Corrupted PDF")

    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.insert.return_value.execute.return_value = {}
    mock_create_client.return_value = mock_supabase

    response = client.post(
        "/upload",
        files={"file": ("sample_contract.pdf", open(sample_pdf_path, "rb"), "application/pdf")}
    )

    assert response.status_code == 500
    assert "Failed to read PDF" in response.json()["detail"]

@patch("os.getenv")
@patch("openai.resources.chat.completions.Completions.create")
@patch("app.main.create_client")
def test_upload_supabase_insert_error(mock_create_client, mock_openai, mock_getenv, sample_pdf_path):
    mock_getenv.side_effect = lambda key: {
        "OPENAI_API_KEY": "fake-key",
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "fake-supabase-key"
    }.get(key, "")

    mock_openai.return_value.choices = [
        type("obj", (object,), {
            "message": type("msg", (object,), {
                "content": '{"mock_flag": "mock_value"}'
            })()
        })()
    ]

    # Simulate Supabase throwing error during .execute()
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("Insert failed")
    mock_create_client.return_value = mock_supabase

    response = client.post(
        "/upload",
        files={"file": ("sample_contract.pdf", open(sample_pdf_path, "rb"), "application/pdf")}
    )

    assert response.status_code == 500
    assert "Database insert failed" in response.json()["detail"]
