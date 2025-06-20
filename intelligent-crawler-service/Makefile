# Intelligent Crawler Service Makefile

.PHONY: help build up down logs test clean

# Default target
help:
	@echo "Intelligent Crawler Service - Available commands:"
	@echo "  make build    - Build all Docker images"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make logs     - Show service logs"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean up containers and volumes"
	@echo "  make dev      - Start in development mode"
	@echo "  make shell    - Open shell in API container"

# Build Docker images
build:
	docker-compose build

# Start services
up:
	docker-compose up -d
	@echo "Services started. API available at http://localhost:8080"
	@echo "Flower (Celery monitor) available at http://localhost:5555"

# Start in development mode
dev:
	docker-compose up

# Stop services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Run tests
test:
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test-runner test-runner
	docker-compose -f docker-compose.test.yml down -v

# Clean up
clean:
	docker-compose down -v
	docker system prune -f

# Open shell in API container
shell:
	docker-compose exec api /bin/bash

# Database operations
db-migrate:
	docker-compose exec api alembic upgrade head

db-reset:
	docker-compose exec postgres psql -U crawler -d crawler_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	docker-compose exec api alembic upgrade head

# Service health check
health:
	@curl -s http://localhost:8080/health | jq .

# Quick crawl test
test-crawl:
	@curl -X POST http://localhost:8080/api/v1/crawl \
		-H "Content-Type: application/json" \
		-d '{"urls": ["https://example.com"], "config": {"max_depth": 1}}' | jq .