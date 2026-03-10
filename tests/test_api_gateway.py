from fastapi.testclient import TestClient

from api_gateway.main import app

client = TestClient(app)


def test_receive_alert_success():
    payload = {
        "status": "firing",
        "alerts": [{"labels": {"job": "test"}, "startsAt": "2026-03-10T12:00:00Z"}],
    }
    response = client.post("/v1/alerts/webhook", json=payload)
    assert response.status_code == 200
    assert "incident_id" in response.json()
    assert response.json()["status"] == "accepted"


def test_kill_switch():
    # Hit the kill switch
    response = client.post("/v1/escalations/halt")
    assert response.status_code == 200
    assert response.json()["status"] == "HALTED"

    # Try to send a new alert, should be 503
    payload = {"status": "firing", "alerts": []}
    response = client.post("/v1/alerts/webhook", json=payload)
    assert response.status_code == 503
    assert "halted" in response.json()["detail"].lower()
