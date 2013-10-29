from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='ics',
	version='indev',
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
	author='Nikita Marchant',
	author_email='nikita.marchant@gmail.com',
	license='WTFPL',
	packages=['ics'],
	include_package_data=True,
	test_suite='nose.collector',
    tests_require=['nose'],
	zip_safe=False
)