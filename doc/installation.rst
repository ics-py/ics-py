.. _`installation`:

Installation
============

This part of the documentation covers the installation of ics.py.
The first step to using any software package is getting it properly installed.


Distribute & Pip
----------------

Installing ics.py is simple with `pip <http://www.pip-installer.org/>`_::

    $ pip install ics

or, with `easy_install <http://pypi.python.org/pypi/setuptools>`_::

    $ easy_install ics

But, you really `shouldn't do that <http://www.pip-installer.org/en/latest/other-tools.html#pip-compared-to-easy-install>`_.


Get the Code
------------

Ics.py is actively developed on GitHub, where the code is
`always available <https://github.com/C4ptainCrunch/ics.py>`_.

You can either clone the public repository::

    git clone git://github.com/C4ptainCrunch/ics.py.git

Download the `tarball <https://github.com/C4ptainCrunch/ics.py/tarball/master>`_::

    $ curl -OL https://github.com/C4ptainCrunch/ics.py/tarball/master

Or, download the `zipball <https://github.com/C4ptainCrunch/ics.py/zipball/master>`_::

    $ curl -OL https://github.com/C4ptainCrunch/ics.py/zipball/master


Once you have a copy of the source, you can embed it in your Python package,
or install it into your site-packages easily::

    $ python setup.py install
