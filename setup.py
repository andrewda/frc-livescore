from setuptools import setup, find_packages


setup(
    name='livescore',
    version='2018.0.0',
    description='Get FRC scores from an image',
    author='Andrew Dassonville',
    author_email='dassonville.andrew@gmail.com',
    url='https://github.com/andrewda/frc-livescore',
    keywords = ['frc', 'score', 'robotics'],
    license='MIT',
    packages=find_packages(exclude=('tests', 'docs')),
    package_data={'livescore': ['templates/*.png', 'tessdata/*.traineddata', 'training_data/*.pkl']}
)
