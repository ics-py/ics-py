Contributing to ics.py
======================

Do you want to contribute? We would love your help 🤗

Feel free to submit patches, issues, feature requests, pull requests on the
`GitHub repo <http://github.com/ics-py/ics-py>`_.

Please note that ics.py is maintained by volunteers (mostly one volunteer)
on their free time. It might take some time for us to have a look at your
work.


Style guide
-----------

Pre-commit checks
^^^^^^^^^^^^^^^

`pre-commit <https://pre-commit.com>`_ is a framework for managing pre-commit
hooks. These hooks help to identify simple issues before committing code for
review. By checking for these issues before code review it allows the reviewer
to focus on the change itself, and it can also help to reduce the number of CI
runs.

To use the tool, first install ``pre-commit`` and then the git hooks:

.. console::

    $ python -m pip install pre-commit
    $ pre-commit install

On the first commit ``pre-commit`` will install the hooks, these are
installed in their own environments and will take a short while to
install on the first run. Subsequent checks will be significantly faster.
If an error is found an appropriate error message will be displayed.
If the error was with ``black`` or ``isort`` then the tool will go ahead and
fix them for you. Review the changes and re-stage for commit if you are happy
with them.

Code formatting
^^^^^^^^^^^^^^^

* All files should be formatted using the
  `black <https://black.readthedocs.io/en/stable/>`_ auto-formatter. This will be
  run by ``pre-commit`` if that is configured.
* Use `isort <https://github.com/PyCQA/isort#readme>`_ to automate import sorting.
  This will be run by ``pre-commit`` if that is configured.
* String variable interpolation may use
  %-formatting, f-strings or ``str.format`` as appropriate, with the goal of
  maximizing code readability. In case of doubt, use f-strings.

Docstrings
^^^^^^^^^^

The style to be used in docstrings is still discussed in
`Issue 344 <https://github.com/ics-py/ics-py/issues/344>`_.
In the meantime, you can take inspiration from the
`Google Python Style Guide <https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings>`_.

How to submit an issue
----------------------

Please include the following in your bug reports:

* the version of ics.py you are using; run :command:`pip freeze | grep ics`
* the version of Python :command:`python -v`
* the OS you are using

Please also include a (preferably minimal) example of the code or
the input that causes problem along with the stacktrace if there is one.

How to submit a pull request
----------------------------

First, before writing your PR, please
`open an issue <http://github.com/ics-py/ics-py/issues/new>`_,
on GitHub to discuss the problem you want to solve and debate on the way
you are solving it. This might save you a lot of time if the maintainers
are already working on it or have a specific idea on how the problem should
be solved.

Setting up the Development Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Clone latest development release

.. code-block:: bash

   git clone git@github.com:ics-py/ics-py.git

* Install `Hatch <https://hatch.pypa.io/latest/>`_

.. code-block:: bash

   pip install hatch tox

* Open shell

.. code-block:: bash

   hatch shell

* Run python

.. code-block:: bash

   hatch run python

* Lint, run the testsuite or build the documentation

.. code-block:: bash

   hatch run tox

* List available einvironments

.. code-block:: bash

   hatch run tox -av

* Run a single environment

.. code-block:: bash

   hatch run tox -e docs

* Build

.. code-block:: bash

   hatch build

Fixing a bug
^^^^^^^^^^^^^^^^^^^^^^^

Please add a test and add a link to it in the PR description
proving that the bug is fixed.
This will help us merge your PR quickly and above all, this will make
sure that we won't re-introduce the bug later by mistake.

Adding a feature
^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will ask you to provide:

* A few tests showing your feature works as intended (they are also great examples and will prevent regressions)
* Write docstrings on the public API
* Add type annotations where possible
* Think about where and how this will affect documentation and amend
  the respective section

Working on the documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Run tox for the docs environment

.. code-block:: bash

   hatch run tox -e docs

* View the pages at ``.tox/docs_out/index.html``

Last thing
^^^^^^^^^^

* Please add yourself to :file:`AUTHORS.rst`
* and state your changes in :file:`CHANGELOG.rst`.

.. note::
  Your PR will most likely be squashed in a single commit, authored
  by the maintainer that merged the PR and you will be credited with a
  ``Co-authored-by:`` in the commit message (this way GitHub picks up
  your contribution).

  The title of your PR will become the commit message, please craft it
  with care.

How to make a new release
-------------------------

* `Prepare environment <#setting-up-the-development-environment>`_

* Run tests

.. code-block:: bash

   hatch run tox && echo "Ready to make a new release" || echo "Please fix all the tests first"

* Set tag with v*

.. code-block:: bash

   git tag -a v0.8 -m "Version 0.8"

* Finalize changelog for current release

.. code-block:: bash

   vi CHANGELOG.rst && git commit -i CHANGELOG.rst --amend

* Build the package

.. code-block:: bash

   hatch build

* Publish

.. code-block:: bash

   hatch publish

* Start new changelog

.. code-block:: bash

   vi CHANGELOG.rst && git commit -i CHANGELOG.rst --amend

* Push

.. code-block:: bash

   git push

* Check GitHub and PyPi release pages for obvious errors
 * https://github.com/ics-py/ics-py/releases
 * https://pypi.org/project/ics/

* Build documentation for the tag v{version} on rtfd.org

* Set the default rtfd version to {version}
