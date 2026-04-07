SHELL := /bin/bash

DOCS_DIR := docs
DOCS_SRC := $(DOCS_DIR)/src
DOCS_BUILD := $(DOCS_DIR)/book

.DEFAULT_GOAL := help

.PHONY: help check.tools.docs build serve clean lint lint.ci screenshots docs.build docs.serve docs.clean docs.lint.links docs.lint docs.lint.ci

help:
	@echo "FluxOmni Self-Hosted: common targets"
	@echo ""
	@echo "  make build          Build mdBook docs"
	@echo "  make serve          Serve docs locally (PORT=3000 by default)"
	@echo "  make clean          Remove generated docs/book output"
	@echo "  make lint           Build + local link lint (+ markdownlint if installed)"
	@echo "  make lint.ci        Strict lint for CI (requires markdownlint-cli2)"
	@echo "  make screenshots    Capture user-guide screenshots (requires running instance)"
	@echo ""
	@echo "  Compatibility aliases: docs.build docs.serve docs.clean docs.lint docs.lint.ci"

build: docs.build

serve: docs.serve

clean: docs.clean

lint: docs.lint

lint.ci: docs.lint.ci

check.tools.docs:
	@command -v mdbook >/dev/null 2>&1 || { \
		echo "Error: mdbook is required."; \
		echo "Install: cargo install mdbook"; \
		exit 1; \
	}

screenshots:
	@cd screenshots && npm install --silent && npx playwright install chromium --with-deps 2>/dev/null; \
	 npx playwright test

docs.build: check.tools.docs
	@mdbook build $(DOCS_DIR)

docs.serve: check.tools.docs
	@mdbook serve $(DOCS_DIR) --hostname 127.0.0.1 --port $${PORT:-3000}

docs.clean:
	@rm -rf $(DOCS_BUILD)

docs.lint.links:
	@./scripts/check-md-links.sh $(DOCS_SRC)

docs.lint: check.tools.docs docs.build docs.lint.links
	@if command -v markdownlint-cli2 >/dev/null 2>&1; then \
		markdownlint-cli2; \
	else \
		echo "Skipping markdown style lint (markdownlint-cli2 not installed)."; \
		echo "Install: npm install -g markdownlint-cli2"; \
	fi

docs.lint.ci: check.tools.docs docs.build docs.lint.links
	@command -v markdownlint-cli2 >/dev/null 2>&1 || { \
		echo "Error: markdownlint-cli2 is required for CI lint."; \
		echo "Install: npm install -g markdownlint-cli2"; \
		exit 1; \
	}
	@markdownlint-cli2
