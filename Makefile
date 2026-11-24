.PHONY: help install tailwind css watch run migrate seed test lint check

help:
	@echo "install   - cria venv e instala dependências"
	@echo "tailwind  - baixa o binário do Tailwind CSS (sem Node)"
	@echo "css       - compila o CSS minificado"
	@echo "watch     - compila o CSS em modo watch"
	@echo "run       - sobe o servidor de desenvolvimento"
	@echo "migrate   - aplica migrações"
	@echo "seed      - cria a conta demo com dados"
	@echo "test      - roda a suíte de testes"
	@echo "lint      - roda o ruff"

install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements-dev.txt

tailwind:
	mkdir -p bin
	curl -sSL -o bin/tailwindcss https://github.com/tailwindlabs/tailwindcss/releases/download/v4.3.5/tailwindcss-linux-x64
	chmod +x bin/tailwindcss

css:
	./bin/tailwindcss -i theme/input.css -o static/css/app.css --minify

watch:
	./bin/tailwindcss -i theme/input.css -o static/css/app.css --watch

run:
	.venv/bin/python manage.py runserver

migrate:
	.venv/bin/python manage.py migrate

seed:
	.venv/bin/python manage.py seed_demo

test:
	.venv/bin/pytest

lint:
	.venv/bin/ruff check .

check:
	.venv/bin/python manage.py check
	.venv/bin/ruff check .
	.venv/bin/pytest
