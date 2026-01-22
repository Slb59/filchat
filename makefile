include .env

run:
	clear
	uv run manage.py runserver

quality:
	clear
	uv run isort .
	uv run black .
	uv run flake8 . > tests/output/flake8.txt
	uv run pylint . --fail-under=9 --ignore=migrations,.venv,tests/output > tests/output/pylint.txt

tests:
	clear
	uv run pytest --benchmark-only
	uv run pytest
	npx playwright test

run-front:
	clear
	uv run manage.py tailwind start # remplacer par npm par la suite

build:
	clear