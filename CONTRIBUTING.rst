Contributing
============

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

If you are fixing a bug
>>>>>>>>>>>>>>>>>>>>>>>

Please add a test and add a link to it in the PR description
proving that the bug is fixed.
This will help us merge your PR quickly and above all, this will make
sure that we won't re-introduce the bug later by mistake.

If you are adding a feature
>>>>>>>>>>>>>>>>>>>>>>>>>>>

We will ask you to provide:

* A few tests showing your feature works as intended (they are also great examples and will prevent regressions)
* Docstrings on the public API
* Type annotations where possible

Last thing
>>>>>>>>>>

* Please add yourself to ``AUTHORS.rst``
* and state your changes in ``CHANGELOG.rst``.

.. note::
  Your PR will most likely be squashed in a single commit, authored
  by the maintainer that merged the PR and you will be credited with a
  ``Co-authored-by:`` in the commit message (this way GitHub picks up
  your contribution).

  The title of your PR will become the commit message, please craft it
  with care.
