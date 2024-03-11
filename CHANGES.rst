Unreleased_
===========

These features will be included in the next release:

Added
-----
- Copied linting related code from Darker 1.7.3.

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
