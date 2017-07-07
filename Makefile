init:
	pip install -r requirements.txt

flake8:
	flake8 livescore

publish:
	pip install 'twine>=1.5.0'
	python setup.py sdist bdist_wheel
	twine upload dist/*
	rm -fr build dist .egg livescore.egg-info
