from setuptools import setup
from ics import __version__, __title__, __license__, __author__


def readme():
    with open('README.rst') as f:
        return f.read()

setup(name=__title__,
    version=__version__,
    description='Python icalendar (rfc5545) parser',
    long_description=readme(),
    keywords='ics icalendar calendar event todo rfc5545 parser pythonic',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Software Development :: Libraries',
        'Intended Audience :: Developers',
        'Topic :: Office/Business :: Scheduling',
    ],
    url='http://github.com/C4ptainCrunch/ics.py',
    author=__author__,
    author_email='nikita.marchant@gmail.com',
    install_requires=[
        "python-dateutil",
        "arrow",
        "six",
    ],
    license=__license__,
    packages=['ics'],
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=['nose'],
    zip_safe=False
)
