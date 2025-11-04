from setuptools import setup, find_packages

setup(
    name='time-tracker',
    version='0.1.0',
    packages=find_packages(),
    install_requires=['click>=8.1.7'],
    entry_points={
        'console_scripts': ['track=src.tracker:cli'],
    },
)