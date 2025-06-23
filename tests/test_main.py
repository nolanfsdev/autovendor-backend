import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def sample_pdf_path():
    return os.path.join(os.path.dirname(__file__), "sample_contract.pdf")

def test_upload_contract(sample_pdf_path):
    with open(sample_pdf_path, "rb") as file:
        response = client.post("/upload", files={"file": ("sample_contract.pdf", file, "application/pdf")})
    
    assert response.status_code == 200
    assert "flags" in response.json()
