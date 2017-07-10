init:
	pip install -r requirements.txt

flake8:
	pip install flake8
	flake8 livescore --statistics --show-source

publish:
	pip install 'twine>=1.5.0'
	python setup.py sdist bdist_wheel
	twine upload dist/*
	rm -fr build dist .egg livescore.egg-info
