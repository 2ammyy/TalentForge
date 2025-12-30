# Makefile (works with PowerShell)
.PHONY: help up down build restart logs shell migrate superuser test clean status

help:
	@echo "TalentForge Docker Commands:"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"
	@echo "  make build     - Rebuild containers"
	@echo "  make restart   - Restart all services"
	@echo "  make logs      - Follow all logs"
	@echo "  make shell     - Open Django shell"
	@echo "  make migrate   - Run migrations"
	@echo "  make superuser - Create superuser"
	@echo "  make test      - Run tests"
	@echo "  make clean     - Remove all containers and volumes"
	@echo "  make status    - Show service status"

up:
	docker-compose up -d
	@echo "Services starting..."
	@echo "Django:    http://localhost:8000"
	@echo "Admin:     http://localhost:8000/admin"
	@echo "Ollama:    http://localhost:11434"
	@echo ""
	@echo "First time? Ollama will download llama2 (4GB) - check logs:"
	@echo "docker-compose logs -f ollama"

down:
	docker-compose down

build:
	docker-compose build --no-cache

restart: down up

logs:
	docker-compose logs -f

logs-web:
	docker-compose logs -f web

logs-db:
	docker-compose logs -f db

logs-ollama:
	docker-compose logs -f ollama

shell:
	docker-compose exec web python manage.py shell

migrate:
	docker-compose exec web python manage.py migrate

makemigrations:
	docker-compose exec web python manage.py makemigrations

superuser:
	docker-compose exec web python manage.py createsuperuser

test:
	docker-compose exec web python manage.py test

clean:
	docker-compose down -v
	docker system prune -af

status:
	docker-compose ps

test-ollama:
	curl http://localhost:11434/api/tags

test-db:
	docker-compose exec db psql -U django_user -d talentforge -c "SELECT version();"