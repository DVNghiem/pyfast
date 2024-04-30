.PHONY: clean clean-test clean-pyc clean-build dist

clean: clean-build clean-pyc clean-test dist ## remove all build, test, coverage and Python artifacts


clean-build: ## remove build artifacts
	rm -rf dist/
	rm -rf build/
	rm -rf checkpoint/
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

dist: clean ## builds source and wheel package
	python setup.py build_ext -b build
	python setup.py bdist_wheel
	ls -l dist
	find ./src -name '*.c*' -exec rm -f {} +
