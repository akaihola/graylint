Unreleased_
===========

These features will be included in the next release:

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

.. _Unreleased: https://github.com/akaihola/graylint/compare/0.0.1...HEAD
