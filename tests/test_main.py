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
@patch("app.main.extract_contract_flags")

def test_upload_contract(mock_getenv, mock_extract, sample_pdf_path):
    mock_getenv.return_value = "fake-key"
    mock_extract.return_value = {"mock_flag": "mock_value"}

    from app.main import app
    client = TestClient(app)

    with open(sample_pdf_path, "rb") as f:
        response = client.post("/upload", files={"file": ("sample_contract.pdf", f, "application/pdf")})

    assert response.status_code == 200
    assert response.json()["flags"] == {"mock_flag": "mock_value"}
