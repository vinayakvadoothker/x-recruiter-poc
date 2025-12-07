.PHONY: api start-api kill-api stop help

help:
	@echo "Available commands:"
	@echo "  make api       - Start the FastAPI server (with Docker and migrations)"
	@echo "  make kill-api  - Kill any process running on port 8000"
	@echo "  make stop      - Stop the backend service (alias for 'make kill-api')"
	@echo "  make start-api - Alias for 'make api'"

api:
	@python scripts/start_api.py

kill-api:
	@./scripts/kill_api.sh

stop: kill-api

start-api: api

