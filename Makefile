distribution:
	python setup.py register sdist upload

format:
	python -m black --config pyproject.toml .

lint:
	python -m flake8 --config lint.cfg
	python -m black  --config pyproject.toml --check .
