import os
import re
import time

import requests

LOG_DIR = "C:\\tmp\\aship_logs\\"
API_GATEWAY_URL = "http://localhost:8000/v1/alerts/webhook"

# A basic heuristic dictionary linking raw error patterns to our UI "Target Services"
SERVICE_MAP = {
    "auth_service.log": "auth-service",
    "billing_db.log": "prod-billing-db",
    "api_gateway.log": "api-gateway",
    "demo_app.log": "api-gateway",  # Map demo to the gateway for visual representation
}

# Regex to detect classic Python Tracebacks or explicit ERROR designations
# Modified to catch the specific '[ERROR] Date Service:' footprint required by the user prompt
ERROR_REGEX = re.compile(
    r"(\[ERROR\])|(Traceback \(most recent call last\):)|(ERROR)|(MemoryError)|(Exception)|(FATAL)"
)


def parse_and_alert(filepath, fault_lines):
    filename = os.path.basename(filepath)
    service_name = SERVICE_MAP.get(filename, "unknown-service")

    # Try to extract the specific error type from the traceback/logs
    fault_str = " ".join(fault_lines)
    fault_type = "Unknown Exception"
    if "MemoryError" in fault_str or "Out of Memory" in fault_str or "OOM" in fault_str:
        fault_type = "Memory Leak (OOM Kill)"
    elif "Timeout" in fault_str:
        fault_type = "Network Latency (5000ms+)"
    elif "ConnectionRefused" in fault_str:
        fault_type = "TCP Connection Refused (Port Blocked)"

    print(f"\n[Live Agent] 🚨 DETECTED CRITICAL FAULT IN: {service_name}")
    print(f"[Live Agent] 🔍 Inferred Fault Type: {fault_type}")
    print(f"[Live Agent] 📡 Forwarding telemetry to ASHIP API Gateway...")

    payload = {
        "status": "firing",
        "alerts": [
            {
                "labels": {
                    "job": service_name,
                    "severity": "critical",
                    "type": fault_type,
                },
                "startsAt": str(time.time()),
                "raw_trace": fault_str,
            }
        ],
    }

    try:
        res = requests.post(API_GATEWAY_URL, json=payload, timeout=2)
        if res.status_code == 200:
            print(
                f"[Live Agent] ✅ Alert Successfully Routed. Incident ID: {res.json().get('incident_id')}"
            )
        else:
            print(f"[Live Agent] ❌ Gateway Rejected: {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"[Live Agent] ❌ Gateway Unreachable: {e}")


def tail_logs():
    print(f"[*] Starting ASHIP Live Observability Agent...")
    print(f"[*] Monitoring directory: {LOG_DIR}")

    # Track file positions to emulate `tail -f`
    file_positions = {}

    while True:
        if not os.path.exists(LOG_DIR):
            time.sleep(2)
            continue

        for filename in os.listdir(LOG_DIR):
            if not filename.endswith(".log"):
                continue

            filepath = os.path.join(LOG_DIR, filename)

            # Init tracker for new files
            if filepath not in file_positions:
                # Start at the beginning of the file so we don't accidentally skip crashes that happened before we bound
                file_positions[filepath] = 0

            try:
                with open(filepath, "r") as f:
                    f.seek(file_positions[filepath])
                    new_lines = f.readlines()
                    file_positions[filepath] = f.tell()

                    if new_lines:
                        # Scan for regex patterns
                        fault_buffer = []
                        is_faulting = False

                        for line in new_lines:
                            if ERROR_REGEX.search(line):
                                is_faulting = True
                                fault_buffer.append(line.strip())
                            elif is_faulting and (
                                line.startswith(" ")
                                or line.startswith("\t")
                                or "Error" in line
                            ):
                                # Catch traceback lines or continuous error output
                                fault_buffer.append(line.strip())
                            else:
                                if is_faulting:
                                    # End of fault block, trigger alert
                                    parse_and_alert(filepath, fault_buffer)
                                    is_faulting = False
                                    fault_buffer = []
                                    break  # Only trigger once per batch to avoid spam

                        # Catch if EOF reached mid-trace
                        if is_faulting and fault_buffer:
                            parse_and_alert(filepath, fault_buffer)

            except Exception as e:
                print(f"Error reading {filepath}: {e}")

        time.sleep(2)  # Polling interval


if __name__ == "__main__":
    tail_logs()
