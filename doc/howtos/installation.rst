Installing ics.py
=================

.. meta::
   :keywords: install ics.py
   :keywords: pip
   :keywords: macos
   :keywords: linux
   :keywords: windows

.. topic:: Abstract

   In this document, we show you how to install the ics.py package with
   the command :command:`pip` on a virtual Python environment and on
   your system.

.. contents::  Content
   :local:


.. _sec.install.check-python-and-pip:

Checking your Python & pip version
----------------------------------

Make sure you have Python available. Type::

    $ python --version

You should get an output like ``3.6.10``. This package needs a minimal
version of Python |minpyver|.

Some systems still distinguish between Python 2 and Python 3. Since 2020,
Python 2 is deprecated. If the command above replies with ``2.7.x``, you
should replace the command :command:`python` with :command:`python3` and
run it again.


.. _sec.install.with-pip:

Installing with pip
-------------------

What is pip?
~~~~~~~~~~~~

The command :command:`pip` [#pip]_ is the Python package manager. Usually, you use a
:command:`pip` in combination with a *virtual Python environment* to install
packages.


What is a "Virtual Python Environment"?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A virtual Python environment "is an isolated runtime environment that allows
Python users and applications to install and upgrade Python distribution
packages without interfering with the behaviour of other Python applications
running on the same system."[#pyvirtenv]_

Install ics.py with pip
~~~~~~~~~~~~~~~~~~~~~~~

To use :command:`pip`, you can install the ics.py package with or without a
virtual Python environment:

**With a virtual Python environment (preferred)**

   #. Start a terminal (in Windows: open up a command prompt window).
   #. In your project directory, create a virtual Python environment first:

     * For Linux and MacOS, run::

       $ python3 -m venv .env

     * For Windows, run::

       > python -m venv %systemdrive%%homepath%\.env

   #. Activate the environment:

      * For Linux and MacOS, run::

        $ source .env/bin/activate

      * For Windows, run::

        > %systemdrive%%homepath%\.env\Scripts\activate.bat

      The prompt will change and show ``(.env)``.

   #. Install the package::

      $ pip install ics

   #. If you do not need the virtual Python environment anymore, run
      the command :command:`deactivate`.


**Without a virtual Python environment**

   Depending on your operating system, you need root privileges to install
   a package with :command:`pip`. To avoid compromising your system
   installation, we recommend to use a virtual Python environment.

   However, if you really want to, run::

   $ pip install ics


Regardless which method you use, the command :command:`pip list` shows you a
list of all installed packages. The list should contain the ics.py package.



.. rubric:: Footnotes

.. [#pip] https://pip.pypa.io
.. [#pyvirtenv] Taken from https://docs.python.org/3/glossary.html#term-virtual-environment
