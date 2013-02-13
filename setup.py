from setuptools import setup

from flake8 import __version__

scripts = ["flake8/flake8"]
README = open('README.rst').read()

setup(
    name="flake8",
    license="MIT",
    version=__version__,
    description="code checking using pep8 and pyflakes",
    author="Tarek Ziade",
    author_email="tarek@ziade.org",
    maintainer="Ian Cordasco",
    maintainer_email="graffatcolmingov@gmail.com",
    url="http://bitbucket.org/tarek/flake8",
    packages=["flake8", "flake8.tests"],
    scripts=scripts,
    install_requires=[
        "setuptools",
        "pyflakes==0.6.1",
        "pep8==1.4.2",
    ],
    long_description=README,
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Topic :: Software Development",
        "Topic :: Utilities",
    ],
    entry_points={
        'distutils.commands': ['flake8 = flake8.main:Flake8Command'],
        'console_scripts': ['flake8 = flake8.main:main'],
        'flake8.extension': [
            'F = flake8._pyflakes:FlakesChecker',
        ],
    },
    tests_require=['nose'],
    test_suite='nose.collector',
)
