Contributing to ics.py
======================

Do you want to contribute? We would love your help 🤗

Feel free to submit patches, issues, feature requests, pull requests on the
`GitHub repo <http://github.com/C4ptainCrunch/ics.py>`_.

Please note that ics.py is maintained by volunteers (mostly one volunteer)
on their free time. It might take some time for us to have a look at your
work.


How to submit an issue
----------------------

Please include the following in your bug reports:

* the version of ics.py you are using; run ``pip freeze | grep ics``
* the version of Python ``python -v``
* the OS you are using

Please also include a (preferably minimal) example of the code or
the input that causes problem along with the stacktrace if there is one.

How to submit a pull request
----------------------------

First, before writing your PR, please
`open an issue <http://github.com/C4ptainCrunch/ics.py/issues/new>`_,
on GitHub to discuss the problem you want to solve and debate on the way
you are solving it. This might save you a lot of time if the maintainers
are already working on it or have a specific idea on how the problem should
be solved.

Setting up the Development Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are three Python tools required to develop, test, and release ics.py:

* `poetry <https://python-poetry.org/>`_ for managing virtualenvs, dependencies,  building, and publishing the package.
* `tox <https://tox.readthedocs.io/>`_ for running the testsuite and building the documentation.
* `bumpversion <https://pypi.org/project/bumpversion/>`_ to help with making a release.

Their respective configuration files are :file:`pyproject.toml`, :file:`tox.ini` and :file:`.bumpversion.cfg`.
Install the tools via pip:

.. code-block:: bash

    $ pip install tox poetry bumpversion --user

.. note::
    If you want to develop using multiple different Python versions, you might want to consider the
    `poetry installer <https://python-poetry.org/docs/#installation>`_.

    Poetry will automatically manage a virtualenv that you can use for developing.
    By default, it will be located centrally in your home directory (e.g. in ``/home/user/.cache/pypoetry/virtualenvs/``).
    To make poetry use a ``./.venv/`` directory within the ics.py folder, use the following config:

    .. code-block:: bash

        $ poetry config virtualenvs.in-project true

Now you are ready to setup your development environment using the following command:

.. code-block:: bash

    $ poetry install

This will create a new virtualenv and install the dependencies for using ics.py.
Furthermore, the current source of the ics.py package will be available similar to running ``./setup.py develop``.
To access the virtualenv, use ``poetry run python`` or ``poetry shell``.
The :file:`poetry.lock` file locks the versions of dependencies in the development environment set up by poetry, so that this environment is the same for everyone.
The file is only read by poetry and not included in any distributions, so these restrictions don't apply when running ``pip install ics``.
As tox manages its own environments and also doesn't read the lock file, it just installs the latest versions of dependencies for testing.
More details on the poetry side can be found `here <https://python-poetry.org/docs/basic-usage/#commit-your-poetrylock-file-to-version-control>`_.

If you made some changes and now want to lint your code, run the testsuite, or build the documentation, run tox.
You don't have to worry about which versions in which venvs are installed and whether you're directly testing against the sources or against a built package, tox handles all that for you:

.. code-block:: bash

    $ tox

To run a single task and not the whole testsuite, use the ``-e`` flag:

.. code-block:: bash

    $ tox -e docs

To get a list of all available tasks, run :command:`tox -av`.

.. note::
    If you want to run any tasks of tox manually, you need to make sure that you also have all the testing dependencies of the task listed in ``tox.ini`` installed.
    You can also let tox `set up <https://tox.readthedocs.io/en/latest/example/devenv.html#creating-development-environments-using-the-devenv-option>`_ your development environment or re-use one of its test environments:

    .. code-block:: bash

        $ tox -e py38
        $ source .tox/py38/bin/activate
        (py38) $ pytest

    This also works without having poetry installed.

If you are fixing a bug
^^^^^^^^^^^^^^^^^^^^^^^

Please add a test and add a link to it in the PR description
proving that the bug is fixed.
This will help us merge your PR quickly and above all, this will make
sure that we won't re-introduce the bug later by mistake.

If you are adding a feature
^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will ask you to provide:

* A few tests showing your feature works as intended (they are also great examples and will prevent regressions)
* Write docstrings on the public API
* Add type annotations where possible
* Think about where and how this will affect documentation and amend
  the respective section

Last thing
^^^^^^^^^^

* Please add yourself to ``AUTHORS.rst``
* and state your changes in ``CHANGELOG.rst``.

.. note::
  Your PR will most likely be squashed in a single commit, authored
  by the maintainer that merged the PR and you will be credited with a
  ``Co-authored-by:`` in the commit message (this way GitHub picks up
  your contribution).

  The title of your PR will become the commit message, please craft it
  with care.

How to make a new release
-------------------------

If you want to publish a new release, use the following steps

.. code-block:: bash

    # Grab the sources and install the dev tools
    git clone https://github.com/C4ptainCrunch/ics.py.git && cd ics.py
    pip install tox poetry bumpversion --user

    # Make sure all the test run
    tox && echo "Ready to make a new release" \
        || echo "Please fix all the tests first"

    # Bump the version and make a "0.8.0-dev -> 0.8.0 (release)" commit
    bumpversion --verbose release
    # Build the package
    poetry build
    # Ensure that the version numbers are consistent
    tox --recreate
    # Check changelog and amend if necessary
    vi CHANGELOG.rst && git commit -i CHANGELOG.rst --amend
    # Publish to GitHub
    git push && git push --tags
    # Publish to PyPi
    poetry publish

    # Bump the version again to start development of next version
    bumpversion --verbose minor # 0.8.0 (release) -> 0.9.0-dev
    # Start new changelog
    vi CHANGELOG.rst && git commit -i CHANGELOG.rst --amend
    # Publish to GitHub
    git push && git push --tags

Please note that bumpversion directly makes a commit with the new version if you don't
pass ``--no-commit`` or ``--dry-run``,
but that's no problem as you can easily amend any changes you want to make.
Further things to check:

* Check GitHub and PyPi release pages for obvious errors
* Build documentation for the tag v{version} on rtfd.org
* Set the default rtfd version to {version}
