.PHONY: run test lint clean install

run:
	cd app && python3 run.py

test:
	pytest tests/

lint:
	flake8 app/
	black --check app/
	isort --check-only app/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf data/

install:
	pip install -e .
