Unreleased_
===========

These features will be included in the next release:

Added
-----
- Copied linting related code from Darker 1.7.0.
- The ``extra_packages`` option for the GitHub Action now allows installing other
  packages in addition to the linters used, e.g. ``-e .[test]`` for installing the
  tested package itself with its test dependencies so Mypy can find them.

Fixed
-----
- Use ``git worktree`` instead of ``git clone`` and ``git checkout`` to set up a
  temporary working tree for running linters for a baseline in the ``rev1`` revision of
  the repository.


Darker 0.1.0 to 1.7.0
=====================

For changes before the migration of code from Darker to Darkgraylib and Graylint, see
`CHANGES.rst in the Darker repository`__.

__ https://github.com/akaihola/darker/blob/master/CHANGES.rst

.. _Unreleased: https://github.com/akaihola/graylint/compare/860c231...HEAD
