import logging
import os
import random
import time

import mongomock
import psutil
from bson.objectid import ObjectId
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
# Global AutoHeal State
AUTO_HEALED = False


@app.route("/api/autoheal", methods=["POST"])
def apply_autoheal():
    global AUTO_HEALED
    AUTO_HEALED = True
    return jsonify({"status": "healed"})


import traceback


@app.errorhandler(Exception)
def handle_exception(e):
    # Ensure it writes directly to disk because Flask dev server swallows uncaught tracebacks
    err_str = f"Unhandled Exception: {str(e)}\n{traceback.format_exc()}"
    logger.error(err_str)

    # Also manual fallback just to be absolutely sure the Live Agent gets the data
    with open("C:\\tmp\\aship_logs\\demo_app.log", "a") as f:
        f.write(
            f"\n[ERROR] {time.strftime('%Y-%m-%d %H:%M:%S')}\nService: TaskService\nError: {err_str}\n"
        )

    return jsonify({"error": str(e)}), 500


# Configure Logging (Specific format requested: [ERROR] Date Service: TaskService Error: Msg)
class CustomFormatter(logging.Formatter):
    def format(self, record):
        time_str = self.formatTime(record, self.datefmt)
        return f"[{record.levelname}] {time_str}\nService: TaskService\nError: {record.getMessage()}"


os.makedirs("C:\\tmp\\aship_logs", exist_ok=True)
fh = logging.FileHandler("C:\\tmp\\aship_logs\\demo_app.log")
fh.setFormatter(CustomFormatter(datefmt="%Y-%m-%d %H:%M:%S"))

sh = logging.StreamHandler()
sh.setFormatter(CustomFormatter(datefmt="%Y-%m-%d %H:%M:%S"))

# Intercept default Flask logger and root logger
logging.basicConfig(level=logging.DEBUG, handlers=[fh, sh])
logger = logging.getLogger("TaskService")

# Setup Database - AutoHealed to MongoDB (Mocked for deployment ease)
mongo_client = mongomock.MongoClient()
db = mongo_client["demo_db"]
tasks_col = db["tasks"]

# Memory Leak Global Array (Fixed for AI Demo Re-Injection)
memory_leak_store = []


def get_db_connection():
    # Bug 4 Fix: Database Connection Failure (30% chance)
    if not AUTO_HEALED and random.random() < 0.3:
        logger.error("Database connection timeout")
        raise Exception("Database connection timeout")
    return tasks_col


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    logger.info("Login attempt received.")
    request.json
    return jsonify({"message": "Logged in successfully", "token": "test_token"})


@app.route("/tasks", methods=["GET"])
def get_tasks():
    try:
        col = get_db_connection()
        tasks_cursor = col.find()
        tasks = []
        for task in tasks_cursor:
            task["_id"] = str(task["_id"])
            task["id"] = task["_id"]  # map _id to id for frontend parity
            tasks.append(task)
        logger.info("Fetched tasks successfully.")
        return jsonify(tasks)
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/tasks", methods=["POST"])
def create_task():
    try:
        # Bug 3: Memory Leak Simulation
        if not AUTO_HEALED:
            memory_leak_store.append("A" * 10**6)  # Adds 1MB per task creation

        data = request.json
        title = data.get("title", "New Task")
        col = get_db_connection()
        col.insert_one({"title": title, "status": "pending"})
        logger.info(f"Task created: {title}")
        return jsonify({"message": "Task created successfully"}), 201
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/tasks/<task_id>", methods=["PUT"])
def update_task(task_id):
    try:
        data = request.json
        status = data.get("status", "completed")
        col = get_db_connection()
        col.update_one({"_id": ObjectId(task_id)}, {"$set": {"status": status}})
        return jsonify({"message": "Task updated"})
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    try:
        col = get_db_connection()
        col.delete_one({"_id": ObjectId(task_id)})
        return jsonify({"message": "Task deleted"})
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": str(e)}), 500


# ---------------- Intentional Bugs ----------------


@app.route("/api/slow", methods=["GET"])
@app.route("/api/tasks/slow", methods=["GET"])
def slow_api():
    if AUTO_HEALED:
        return jsonify({"message": "Response after 0 ms. Telemetry green."})

    # Bug 1: Slow API Response
    logger.warning("Slow API endpoint invoked. Delaying response for 6 seconds...")
    time.sleep(6)
    return jsonify({"message": "Response after 6 seconds"})


@app.route("/api/crash", methods=["GET"])
def crash_api():
    if AUTO_HEALED:
        return jsonify(
            {"message": "The AutoHealer successfully prevented this memory overflow."}
        )

    # Bug 2: Application Crash
    err_msg = "Fatal Server Crash: Memory overflow in handler"
    fake_traceback = f'Traceback (most recent call last):\n  File "/usr/local/lib/python3.11/site-packages/flask/app.py", line 1478, in __call__\n    return self.wsgi_app(environ, start_response)\nException: {err_msg}'

    with open("C:\\tmp\\aship_logs\\demo_app.log", "a") as f:
        f.write(
            f"\n[ERROR] {time.strftime('%Y-%m-%d %H:%M:%S')}\nService: TaskService\nError: {fake_traceback}\n"
        )

    logger.error(err_msg)
    raise Exception(err_msg)


@app.route("/api/stats", methods=["GET"])
def incorrectly_calculated_stats():
    # Bug 5: Incorrect Logic Bug
    try:
        col = get_db_connection()
        total = col.count_documents({})
        completed = col.count_documents({"status": "completed"})

        # LOGIC BUG: Division by random wrong number or simple mistake
        if not AUTO_HEALED:
            percentage = (completed + 1) / (total - 1) * 100 if total > 1 else 100
        else:
            percentage = (completed / total * 100) if total > 0 else 100.0

        return jsonify(
            {"total": total, "completed": completed, "percentage": percentage}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/metrics", methods=["GET"])
def get_metrics():
    # Generate system metrics
    cpu = psutil.cpu_percent(interval=0.1)
    mem_info = psutil.virtual_memory()
    return jsonify(
        {
            "cpu_usage_percent": cpu,
            "memory_usage_percent": mem_info.percent,
            "api_response_time_ms": random.randint(10, 500),  # Mock
            "request_count": len(memory_leak_store) * 10 + random.randint(1, 100),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
