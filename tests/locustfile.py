import json
import uuid

from locust import HttpUser, between, task


class ASHIPLoadTest(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(3)
    def trigger_alert(self):
        payload = {
            "status": "firing",
            "alerts": [
                {
                    "labels": {
                        "severity": "critical",
                        "job": f"random-job-{uuid.uuid4().hex[:4]}",
                    },
                    "startsAt": "2026-03-10T00:00:00Z",
                }
            ],
        }
        with self.client.post(
            "/v1/alerts/webhook", json=payload, catch_response=True
        ) as response:
            if response.status_code == 200:
                # Save incident ID for the next task
                try:
                    self.last_incident_id = response.json().get("incident_id")
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Failed to decode JSON")
            else:
                response.failure(f"Got {response.status_code}")

    @task(1)
    def check_incident_status(self):
        if hasattr(self, "last_incident_id"):
            self.client.get(f"/v1/incidents/{self.last_incident_id}")
