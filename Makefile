# AI Error Analysis Buildkite Plugin - Development Makefile

.PHONY: help test test-bats test-python test-integration lint clean setup check health install-deps

# Default target
help: ## Show this help message
	@echo "AI Error Analysis Buildkite Plugin - Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Test targets
test: test-bats test-python ## Run all tests

test-bats: ## Run BATS tests for shell scripts
	@echo "🧪 Running BATS tests..."
	docker-compose run --rm tests

test-python: ## Run Python unit tests
	@echo "🐍 Running Python tests..."
	docker-compose run --rm python-tests

test-integration: ## Run integration tests
	@echo "🔗 Running integration tests..."
	docker-compose run --rm integration-test

test-ci: ## Run tests in CI mode (with coverage)
	@echo "🚀 Running CI test suite..."
	docker-compose run --rm python-tests pytest --cov-report=xml --cov-report=term

# Code quality
lint: ## Run linting and code quality checks
	@echo "🔍 Running linting..."
	docker-compose run --rm lint

format: ## Format code using black and other formatters
	@echo "✨ Formatting Python code..."
	docker run --rm -v "$(PWD):/code" pyfound/black:latest black lib/ tests/python/

check: lint test ## Run both linting and tests

# Health and validation
health: ## Run health check
	@echo "🏥 Running health check..."
	docker-compose run --rm health-check

validate: ## Validate plugin configuration
	@echo "✅ Validating plugin configuration..."
	docker-compose run --rm lint

# Development setup
setup: ## Set up development environment
	@echo "🛠️  Setting up development environment..."
	@echo "Checking Docker..."
	@docker --version
	@echo "Checking Docker Compose..."
	@docker-compose --version
	@echo "Building test images..."
	@docker-compose build
	@echo "✅ Development environment ready!"

install-deps: ## Install local development dependencies
	@echo "📦 Installing Python development dependencies..."
	pip install -r requirements-dev.txt

# Manual testing
test-manual: ## Run manual test of the plugin
	@echo "🧪 Running manual plugin test..."
	@export BUILDKITE_COMMAND_EXIT_STATUS=1 && \
	 export BUILDKITE_COMMAND="echo 'ERROR: Test failure' && exit 1" && \
	 export BUILDKITE_BUILD_PATH="$(PWD)" && \
	 export AI_ERROR_ANALYSIS_PLUGIN_DIR="$(PWD)" && \
	 export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DRY_RUN=true && \
	 export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DEBUG_MODE=true && \
	 ./hooks/environment && \
	 ./hooks/post-command && \
	 ./hooks/pre-exit

test-hooks: ## Test individual hooks
	@echo "🪝 Testing plugin hooks..."
	@export AI_ERROR_ANALYSIS_PLUGIN_DIR="$(PWD)" && \
	 export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DRY_RUN=true && \
	 echo "Testing environment hook..." && \
	 ./hooks/environment && \
	 echo "✅ Environment hook passed"

# Cleanup
clean: ## Clean up temporary files and Docker containers
	@echo "🧹 Cleaning up..."
	docker-compose down --volumes --remove-orphans
	docker system prune -f
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf lib/__pycache__/
	rm -rf tests/python/__pycache__/
	rm -f coverage.xml
	rm -f .coverage
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	@echo "✅ Cleanup complete!"

# Documentation
docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	@echo "README.md is the main documentation"
	@echo "See docs/ directory for additional documentation"

# Release preparation
version-check: ## Check current version
	@echo "📋 Current version information:"
	@grep "version:" plugin.yml || echo "No version found in plugin.yml"
	@echo ""
	@echo "Recent git tags:"
	@git tag --sort=-v:refname | head -5 || echo "No git tags found"

prepare-release: check ## Prepare for release (run all checks)
	@echo "🚀 Preparing for release..."
	@echo "✅ All checks passed - ready for release!"

# Performance testing
perf-test: ## Run performance tests
	@echo "⚡ Running performance tests..."
	@echo "Creating large log file for testing..."
	@python3 -c "
import sys
for i in range(1000):
    if i % 100 == 0:
        print(f'Line {i}: ERROR: Performance test error {i//100}')
    else:
        print(f'Line {i}: Normal log output for performance testing')
" > /tmp/large-test.log
	@echo "Running error detection on large log..."
	@time python3 lib/error_detector.py

# Security testing
security-test: ## Run security-focused tests
	@echo "🔒 Running security tests..."
	@export BUILDKITE_COMMAND="echo 'SECRET_TOKEN=abc123' && echo 'password=secret' && exit 1" && \
	 export BUILDKITE_COMMAND_EXIT_STATUS=1 && \
	 export AI_ERROR_ANALYSIS_PLUGIN_DIR="$(PWD)" && \
	 export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DRY_RUN=true && \
	 python3 lib/context_builder.py | python3 lib/log_sanitizer.py /dev/stdin /tmp/sanitized.json && \
	 echo "Checking for leaked secrets..." && \
	 if grep -i "secret\|password\|token" /tmp/sanitized.json; then \
	   echo "❌ Security test failed - secrets found in sanitized output"; \
	   exit 1; \
	 else \
	   echo "✅ Security test passed - no secrets in sanitized output"; \
	 fi

# Debug helpers
debug: ## Run plugin in debug mode
	@echo "🐛 Running plugin in debug mode..."
	@export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DEBUG_MODE=true && \
	 export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DRY_RUN=true && \
	 $(MAKE) test-manual

shell: ## Open shell in test container
	@echo "🐚 Opening shell in test container..."
	docker-compose run --rm python-tests bash

logs: ## View recent Docker logs
	@echo "📄 Recent Docker logs..."
	docker-compose logs --tail=50

# Git helpers
git-status: ## Show detailed git status
	@echo "📊 Git repository status:"
	@git status
	@echo ""
	@echo "Recent commits:"
	@git log --oneline -5

# Environment info
env-info: ## Show environment information
	@echo "🌍 Environment Information:"
	@echo "Operating System: $$(uname -s -r)"
	@echo "Shell: $$SHELL"
	@echo "Python: $$(python3 --version 2>/dev/null || echo 'Not found')"
	@echo "Docker: $$(docker --version 2>/dev/null || echo 'Not found')"
	@echo "Docker Compose: $$(docker-compose --version 2>/dev/null || echo 'Not found')"
	@echo "Git: $$(git --version 2>/dev/null || echo 'Not found')"
	@echo ""
	@echo "Plugin Directory: $(PWD)"
	@echo "Current Branch: $$(git branch --show-current 2>/dev/null || echo 'Unknown')"

# Quick development workflow
dev: setup check ## Quick development setup and validation
	@echo "🎉 Development environment is ready!"
	@echo ""
	@echo "Next steps:"
	@echo "  make test          # Run all tests"
	@echo "  make test-manual   # Test the plugin manually"
	@echo "  make debug         # Run in debug mode"
	@echo "  make help          # Show all available commands"

# CI/CD helpers
ci-setup: ## Set up for CI/CD environment
	@echo "🤖 Setting up CI environment..."
	@docker-compose build --parallel
	@echo "✅ CI setup complete!"

ci-test: ci-setup test-ci lint ## Run full CI test suite
	@echo "✅ CI test suite completed successfully!"