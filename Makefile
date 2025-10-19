# Makefile for Rental Management System

.PHONY: help dev test seed clean install build-css

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt
	npm install

dev: ## Start development server
	python manage.py migrate
	python manage.py runserver

test: ## Run tests
	python manage.py test
	pytest

seed: ## Seed database with demo data
	python manage.py seed_demo

seed-clear: ## Clear and seed database with demo data
	python manage.py seed_demo --clear

migrate: ## Run database migrations
	python manage.py makemigrations
	python manage.py migrate

superuser: ## Create superuser
	python manage.py createsuperuser

collectstatic: ## Collect static files
	python manage.py collectstatic --noinput

build-css: ## Build Tailwind CSS
	npm run build-css-prod

build-css-dev: ## Build Tailwind CSS in watch mode
	npm run build-css

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

lint: ## Run linting
	black .
	flake8 .
	isort .

format: ## Format code
	black .
	isort .

check: ## Run all checks
	make lint
	make test

setup: ## Initial setup
	make install
	make migrate
	make seed
	make build-css
	@echo "Setup complete! Run 'make dev' to start the development server."
	@echo "Login with admin/admin123"
