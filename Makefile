# Regalion AML — Django best-practice run targets
# Usage: make run | make migrate | make test | make prod-run

PYTHON ?= python3
MANAGE = cd backend && $(PYTHON) manage.py
VENV = backend/venv
VENV_BIN = $(VENV)/bin

.PHONY: help venv install migrate run run-prod test shell createsuperuser collectstatic create-sample-rules

help:
	@echo "Regalion AML — targets: venv, install, migrate, run, run-prod, test, shell, createsuperuser, collectstatic, create-sample-rules"

venv:
	$(PYTHON) -m venv $(VENV)
	@echo "Activate with: source $(VENV_BIN)/activate"

install: venv
	$(VENV_BIN)/pip install -r backend/requirements.txt

migrate:
	$(MANAGE) migrate

run:
	$(MANAGE) runserver 0.0.0.0:8000

run-prod:
	export DJANGO_ENV=production && $(MANAGE) runserver 0.0.0.0:8000

test:
	$(MANAGE) test

shell:
	$(MANAGE) shell

createsuperuser:
	$(MANAGE) createsuperuser

collectstatic:
	$(MANAGE) collectstatic --noinput

create-sample-rules:
	$(MANAGE) create_sample_rules

check:
	$(MANAGE) check
