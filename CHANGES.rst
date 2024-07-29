Unreleased_
===========

These features will be included in the next release:

Added
-----

Fixed
-----
- In the configuration dump printed when ``-vv`` verbosity is used, the configuration
  section is now correctly named ``[tool.graylint]`` instead of ``[tool.darkgraylib]``.
  This required an update to Darkgraylib 1.3.0.
- Update to Darkgraylib 1.3.1 to fix ``--version``.
- Pass Graylint version to `~darkgraylib.command_line.make_argument_parser` to make
  ``--version`` display the correct version number.


1.1.1_ - 2024-04-13
===================

Added
-----
- Update to Darkgraylib 1.2.0 for compatibility with Darker 2.1.1.

Fixed
-----
- Linter command lines with quoting on Windows.


1.1.0_ - 2024-04-02
===================

Added
-----
- Support for Python 3.12 in the package metadata and the CI build.
- In the future test, upgrade ``Pygments`` to repository ``master``.
- Messages from future test are now generic, not Black-specific.
- Require ``click`` when running tests.
- Linter failures now result in an exit value of 1. This makes Graylint compatible with
  ``pre-commit``.

Removed
-------
- Dependency on flynt and regex.
- Obsolete Mypy configuration options.
- Skip tests on Python 3.13-dev in Windows and macOS. C extension builds are failing,
  this exclusion is to be removed when Python 3.13 has been removed.
- The ``release_tools/update_contributors.py`` script was moved to the
  ``darkgray-dev-tools`` repository.

Fixed
-----
- Badge links in the README on GitHub.


1.0.1_ - 2024-03-15
===================

Added
-----
- Update Darkgraylib to 1.1.0 for compatibility with Darker.

Removed
-------
- ``bump_version.py`` is now in the separate ``darkgray-dev-tools`` repository.


1.0.0_ - 2024-03-13
===================

Added
-----
- Copied linting related code from Darker 1.7.3.
- The command ``graylint --config=check-graylint.toml`` now runs Flake8_, Mypy_,
  pydocstyle_, Pylint_ and Ruff_ on Graylint's code base and reports new linting errors
  and errors on modified lines in Python files. Those linters are installed as
  dependencies in the ``[test]`` extra.
  Similarly, ``darker --config=check-graylint.toml`` runs the same linters as well as
  Black and isort on modified lines.
- The minimum Ruff_ version is now 0.0.292. Its configuration in ``pyproject.toml`` has
  been updated accordingly.
- The contribution guide now gives better instructions for reformatting and linting.
- Separate GitHub workflow for checking code formatting and import sorting.
- Also check the action, release tools and ``setup.py`` in the build workflows.

Removed
-------
- Don't run pytest-darker_ in the CI build. It's lagging quite a bit behind.

Fixed
-----
- Omit missing paths from linter command lines. Mypy was known to lint nothing if any
  of the paths on the command line didn't exist.
- Include ``py.typed`` marker in distributions so the package is recognized as a
  PEP 561 compliant package with typing annotations.


Darker 0.1.0 to 1.7.3
=====================

For changes before the migration of code from Darker to Graylint, see
`CHANGES.rst in the Darker repository`__.

__ https://github.com/akaihola/darker/blob/master/CHANGES.rst

.. _Unreleased: https://github.com/akaihola/graylint/compare/1.1.0...HEAD
.. _1.1.0: https://github.com/akaihola/graylint/compare/v1.0.1...v1.1.0
.. _1.0.1: https://github.com/akaihola/graylint/compare/v1.0.0...v1.0.1
.. _1.0.0: https://github.com/akaihola/graylint/compare/1.7.3...v1.0.0
