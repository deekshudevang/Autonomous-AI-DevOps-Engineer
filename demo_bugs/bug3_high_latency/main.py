import time

from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health_check():
    # Simulated deadlock / high latency bug
    time.sleep(30)
    return {"status": "ok"}
