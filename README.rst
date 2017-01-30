.. image:: https://readthedocs.org/projects/pybuilder-pip-tools/badge/?version=1.1.0
   :target: http://pybuilder-pip-tools.readthedocs.io/en/1.1.0/?badge=1.1.0
   :alt: Documentation Status

.. image:: https://travis-ci.org/timdiels/pybuilder-pip-tools.svg?branch=1.1.0
   :target: https://travis-ci.org/timdiels/pybuilder-pip-tools
   :alt: Build Status of 1.1.0

.. image:: https://coveralls.io/repos/github/timdiels/pybuilder-pip-tools/badge.svg
   :target: https://coveralls.io/github/timdiels/pybuilder-pip-tools
   :alt: Test coverage of latest build


PyBuilder Pip Tools is a PyBuilder plugin which generates
``*requirements*.txt`` files from your project (build) dependencies and keeps
your virtual env in sync with them. This is achieved with `pip-compile` and
`pip-sync` from `pip-tools`_.

.. _pip-tools: https://github.com/nvie/pip-tools

Links
=====

- `Documentation <http://pybuilder-pip-tools.readthedocs.io/en/1.1.0/>`_
- `PyPI <https://pypi.python.org/pypi/pybuilder-pip-tools/>`_
- `GitHub <https://github.com/timdiels/pybuilder-pip-tools>`_

Interface stability
===================
While all features are documented (docstrings only) and tested, the API is
changed frequently.  When doing so, the `major version <semver_>`_ is bumped
and a changelog is kept to help upgrade. Fixes will not be backported. It is
recommended to pin the major version in your build.py, e.g. for 1.x.y::

    use_plugin('pypi:pybuilder_pip_tools', '==1.*')

.. _semver: http://semver.org/spec/v2.0.0.html
