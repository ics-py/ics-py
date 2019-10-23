#!/usr/bin/env python
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand

from ics.__meta__ import __author__, __license__, __title__, __version__

with open("requirements.txt") as f:
    install_requires = [line for line in f if line and line[0] not in "#-"]

with open("dev/requirements-test.txt") as f:
    tests_require = [line for line in f if line and line[0] not in "#-"]


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = [
            '--cov',
            'ics',
            'ics/',
            'tests/'
        ]
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


def readme():
    with open('README.rst', encoding='utf-8') as f:
        return f.read()


setup(
    name=__title__,
    version=__version__,
    description='Python icalendar (rfc5545) parser',
    long_description=readme(),
    keywords='ics icalendar calendar event todo rfc5545 parser pythonic',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
        'Topic :: Office/Business :: Scheduling',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Typing :: Typed',

    ],
    url='http://github.com/C4ptainCrunch/ics.py',
    author=__author__,
    author_email='nikita.marchant@gmail.com',
    install_requires=install_requires,
    license=__license__,
    packages=['ics'],
    include_package_data=True,
    cmdclass={'test': PyTest},
    tests_require=tests_require,
    test_suite="py.test",
    zip_safe=False,
)
