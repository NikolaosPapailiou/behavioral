all: format lint install

lint:
	ruff check . --fix

format:
	ruff format .
	isort .

install:
	pip install -e .
