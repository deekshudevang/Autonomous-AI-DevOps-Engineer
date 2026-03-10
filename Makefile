.PHONY: check build test demo clean

check:
	black --check .
	isort --check-only .
	flake8 .
	mypy .
	opa test policy_engine/policies/

test:
	pytest tests/

build:
	docker compose build

run:
	docker compose up -d

stop:
	docker compose down

demo:
	docker compose up -d
	@echo "========================================="
	@echo " ASHIP Demo Environment is Starting Up...  "
	@echo "========================================="
	@echo " Waiting 10s for services to stabilize..."
	@sleep 10
	@echo " Triggering synthetic webhook alert to API Gateway..."
	@curl -X POST http://localhost:8000/v1/alerts/webhook \
		-H "Content-Type: application/json" \
		-d '{"status":"firing","alerts":[{"labels":{"job":"billing-api","severity":"critical"},"startsAt":"2026-03-10T00:00:00Z"}]}'
	@echo "\n========================================="
	@echo " Alert Ingested! Check agent logs for ReAct execution."

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -r {} +
