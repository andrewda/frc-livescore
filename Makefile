init:
	pip install -r requirements.txt

test:
	cd tests && python test2017.py && python test2018.py && python test2019.py

flake8:
	pip install flake8
	flake8 livescore --statistics --show-source

publish:
	pip install 'twine>=1.5.0'
	python setup.py sdist bdist_wheel
	twine upload dist/*
	rm -fr build dist .egg livescore.egg-info
