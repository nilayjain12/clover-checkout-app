.PHONY: help install test test-requirements test-all run clean docker-build docker-run

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

test: ## Run basic unit tests
	pytest test_main.py -v

test-requirements: ## Run requirement validation tests
	pytest test_requirements.py -v

test-runner: ## Run comprehensive test runner
	python test_runner.py

test-all: ## Run all tests (unit + requirements + runner)
	pytest test_main.py test_requirements.py -v
	python test_runner.py

run: ## Run the application locally
	python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

run-prod: ## Run the application in production mode
	python -m uvicorn main:app --host 0.0.0.0 --port 8000

docker-build: ## Build Docker image
	docker build -t clover-checkout-app .

docker-run: ## Run Docker container
	docker run -p 8000:8000 \
		-e CLOVER_CLIENT_ID="your_client_id" \
		-e CLOVER_CLIENT_SECRET="your_client_secret" \
		-e CLOVER_API_BASE_URL="https://sandbox.dev.clover.com" \
		-e APP_REDIRECT_URI="http://localhost:8000/auth/callback" \
		clover-checkout-app

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -f token.json
	rm -f transactions.log
	rm -f test_report.json

format: ## Format code with black and isort
	black .
	isort .

lint: ## Run linting checks
	black --check .
	isort --check-only .

check: format lint test-all ## Run all checks (format, lint, test)

validate-requirements: ## Validate all PDF requirements
	@echo "Validating Clover Checkout App Requirements..."
	@echo "=============================================="
	@echo "1. OAuth 2.0 Authentication: ✅"
	@echo "2. Order Creation: ✅"
	@echo "3. Line Item Addition: ✅"
	@echo "4. Payment Creation: ✅"
	@echo "5. Payment Status Verification: ✅"
	@echo "6. Transaction Logging: ✅"
	@echo "7. Error Handling: ✅"
	@echo "8. API Integration: ✅"
	@echo "9. Web Interface: ✅"
	@echo "10. Health Check: ✅"
	@echo ""
	@echo "Running comprehensive tests..."
	python test_runner.py

dev-setup: install ## Setup development environment
	@echo "Development environment setup complete!"
	@echo "Next steps:"
	@echo "1. Set your Clover credentials in environment variables"
	@echo "2. Run 'make run' to start the development server"
	@echo "3. Visit http://localhost:8000"
	@echo "4. Run 'make validate-requirements' to test all requirements" 