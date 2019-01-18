from setuptools import setup

setup(
    name='pytest-shelltest',
    description='Doctest for command line code examples.'
    author='Oliver Sanders',
    author_email='.',
    version='0.1',
    py_modules = ['pytest_shelltest'],
    entry_points = {
        'pytest11': [
            'pytest_shelltest = pytest_shelltest',
        ]
    },
    install_requires = ['py>=1.3.0'],
)
