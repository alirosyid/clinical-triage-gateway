from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "pii_redaction_gateway"}

def test_pii_redaction_and_routing():
    # Payload simulating a real patient with sensitive data
    payload = {
        "request_id": "req_99823",
        "raw_message": "Halo, nama saya Budi. NIK saya 3171234567890123. Tolong atur jadwal koas untuk periksa rahang saya. Hubungi 081234567890."
    }
    
    response = client.post("/api/v1/triage", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # 1. Test Security: Verify NIK and Phone are masked
    assert "3171234567890123" not in data["redacted_message"]
    assert "081234567890" not in data["redacted_message"]
    assert "[REDACTED_NIK]" in data["redacted_message"]
    assert "[REDACTED_PHONE]" in data["redacted_message"]
    
    # 2. Test Routing Logic
    assert data["routing_bucket"] == "clinical_occlusal_adjustment"
