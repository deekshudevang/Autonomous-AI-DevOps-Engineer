import time
import os
import random
import logging
from datetime import datetime

# Setup logging to write to our shared temp directory
LOG_FILE = "C:\\tmp\\aship_logs\\auth_service.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("auth-service")

def simulate_auth_service():
    print(f"Starting auth-service mock payload. Writing logs to {LOG_FILE}...")
    
    # Write normal health logs for a bit
    for i in range(5):
        logger.info(f"Health Check {i}/5: Service Operational. Active Conns: {random.randint(100, 200)}")
        time.sleep(1)
        
    print("Simulating critical failure...")
    
    # Violently crash the mock service with a Memory Leak traceback
    try:
        logger.warning("Memory utilization exceeding 85% threshold.")
        time.sleep(1)
        logger.error("Failed to allocate memory for caching tier.")
        time.sleep(0.5)
        # Induce a faux OOM
        raise MemoryError("Fatal: Out of Memory (OOM Kill) - Allocation Failed.")
    except Exception as e:
        logger.exception("Service crashed unexpectedly.")
        print("Mock service has crashed!")

if __name__ == "__main__":
    # If the file exists, clear it for the demo
    if os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()
    simulate_auth_service()
