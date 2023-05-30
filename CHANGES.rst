Unreleased_
===========

These features will be included in the next release:

Added
-----
- Copied linting related code from Darker 1.7.0.

Fixed
-----
- Use ``git worktree`` instead of ``git clone`` and ``git checkout`` to set up a
  temporary working tree for running linters for a baseline in the ``rev1`` revision of
  the repository.
- Use the original repository working directory name as the name of the temporary
  directory for getting the linter baseline. This avoids issues with Mypy when there's
  an ``__init__.py`` in the repository root.


Darker 0.1.0 to 0.7.0
======================

For changes before the migration of code from Darker to Darkgraylib and Graylint, see
`CHANGES.rst in the Darker repository`__.

__ https://github.com/akaihola/darker/blob/master/CHANGES.rst

.. _Unreleased: https://github.com/akaihola/graylint/compare/860c231...HEAD
