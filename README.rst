==================================================
 Graylint – show new linter errors in Python code
==================================================

|build-badge| |license-badge| |pypi-badge| |downloads-badge| |black-badge| |changelog-badge|

.. |build-badge| image:: https://github.com/akaihola/graylint/actions/workflows/python-package.yml/badge.svg
   :alt: master branch build status
   :target: https://github.com/akaihola/graylint/actions/workflows/python-package.yml?query=branch%3Amaster
.. |license-badge| image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
   :alt: BSD 3 Clause license
   :target: https://github.com/akaihola/graylint/blob/master/LICENSE.rst
.. |pypi-badge| image:: https://img.shields.io/pypi/v/graylint
   :alt: Latest release on PyPI
   :target: https://pypi.org/project/graylint/
.. |downloads-badge| image:: https://pepy.tech/badge/graylint
   :alt: Number of downloads
   :target: https://pepy.tech/project/graylint
.. |black-badge| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :alt: Source code formatted using Black
   :target: https://github.com/psf/black
.. |changelog-badge| image:: https://img.shields.io/badge/-change%20log-purple
   :alt: Change log
   :target: https://github.com/akaihola/graylint/blob/master/CHANGES.rst
.. |next-milestone| image:: https://img.shields.io/github/milestones/progress/akaihola/graylint/2?color=red&label=release%201.2.0
   :alt: Next milestone
   :target: https://github.com/akaihola/graylint/milestone/3


What?
=====

This utility runs linters on Python source code files.
However, when run in a Git repository, it runs the linters both in an old and a newer
revision of the source tree. It then only reports those linting messages which appeared
after the modifications to the source code files between those revisions.

To integrate Graylint with your IDE or with pre-commit_,
see the relevant sections below in this document.

.. _Pytest: https://docs.pytest.org/

+------------------------------------------------+--------------------------------+
| |you-can-help|                                 | |support|                      |
+================================================+================================+
| We're asking the community kindly for help to  | We have a                      |
| review pull requests for |next-milestone|_ .   | `community support channel`_   |
| If you have a moment to spare, please take a   | on GitHub Discussions. Welcome |
| look at one of them and shoot us a comment!    | to ask for help and advice!    |
+------------------------------------------------+--------------------------------+

.. |you-can-help| image:: https://img.shields.io/badge/-You%20can%20help-green?style=for-the-badge
   :alt: You can help
.. |support| image:: https://img.shields.io/badge/-Support-green?style=for-the-badge
   :alt: Support
.. _community support channel: https://github.com/akaihola/graylint/discussions


Why?
====

You want to lint your code with more or less strict linter rules.
Your code base is known to violate some of those linter rules.

When running the linters, you only want to see the new violations which have appeared
e.g. in your open feature branch, compared to the branch point from the main branch.

This can also be useful
when contributing to upstream codebases that are not under your complete control.

Note that this tool is meant for special situations
when dealing with existing code bases.
You should just aim to conform 100% with linter rules
when starting a project from scratch.


How?
====

To install or upgrade, use::

  pip install --upgrade graylint~=1.1.2

Or, if you're using Conda_ for package management::

  conda install -c conda-forge graylint~=0.0.1
  conda update -c conda-forge graylint

..

    **Note:** It is recommended to use the '``~=``' "`compatible release`_" version
    specifier for Graylint. See `Guarding against linter compatibility breakage`_ for
    more information.

As an example,
the ``graylint --lint pylint <myfile.py>``
or ``graylint --lint pylint <directory>`` command
reads the original file(s),
runs Pylint on them in the original state of the current commit,
then runs Pylint again on the working tree,
and finally filters out the messages which appeared in both runs.

Alternatively, you can invoke the module directly through the ``python`` executable,
which may be preferable depending on your setup.
Use ``python -m graylint`` instead of ``graylint`` in that case.

By default, ``graylint`` doesn't run any linters.
You can enable individual linters with the
``-L <linter>`` / ``--lint <linter>`` command line options:

.. _Conda: https://conda.io/
.. _conda-forge: https://conda-forge.org/


Example
=======

This example walks you through a minimal practical use case for Graylint.

First, create an empty Git repository:

.. code-block:: shell

   $ mkdir /tmp/test
   $ cd /tmp/test
   $ git init
   Initialized empty Git repository in /tmp/test/.git/

In the root of that directory, create the Python file ``our_file.py``
which violates one Pylint rule:

.. code-block:: python

   first_name = input("Enter your first name: ")
   if first_name == "Guido":
       print("I know you")
   else:
       print("Nice to meet you")

.. code-block:: shell

   $ pylint our_file.py
   ************* Module our_file
   our_file.py:1:0: C0114: Missing module docstring (missing-module-docstring)

   ------------------------------------------------------------------
   Your code has been rated at 7.50/10 (previous run: 7.50/10, +0.00)

Commit that file:

.. code-block:: shell

   $ git add our_file.py
   $ git commit -m "Initial commit"
   [master (root-commit) a0c7c32] Initial commit
    1 file changed, 3 insertions(+)
    create mode 100644 our_file.py

Now modify the fourth line in that file:

.. code-block:: python

   first_name = input("Enter your first name: ")
   if first_name == "Guido":
       print("I know you")
   elif True:
       print("Nice to meet you")

.. code-block:: shell

   $ pylint our_file.py
   ************* Module our_file
   our_file.py:1:0: C0114: Missing module docstring (missing-module-docstring)
   our_file.py:4:5: W0125: Using a conditional statement with a constant value (using-constant-test)

   ------------------------------------------------------------------
   Your code has been rated at 6.00/10 (previous run: 7.50/10, -1.50)

You can ask Graylint to show only the newly appeared linting violations:

.. code-block:: shell

   $ graylint --lint pylint our_file.py
   our_file.py:4:5: W0125: Using a conditional statement with a constant value (using-constant-test) [pylint]

You can also ask Graylint to run linters on all Python files in the repository:

.. code-block:: shell

   $ graylint --lint pylint .

Or, if you want to compare to another branch (or, in fact, any commit)
instead of the last commit:

.. code-block:: shell

   $ graylint --lint pylint --revision main .


Customizing ``graylint`` and linter behavior
============================================

Mypy_, Pylint_, Flake8_ and other compatible linters are invoked as
subprocesses by ``graylint``, so normal configuration mechanisms apply for each of those
tools. Linters can also be configured on the command line, for example::

    graylint -L "mypy --strict" .
    graylint --lint "pylint --errors-only" .
  
The following command line arguments can also be used to modify the defaults:

-r REV, --revision REV
       Revisions to compare. The default is ``HEAD..:WORKTREE:`` which compares the
       latest commit to the working tree. Tags, branch names, commit hashes, and other
       expressions like ``HEAD~5`` work here. Also a range like ``main...HEAD`` or
       ``main...`` can be used to compare the best common ancestor. With the magic value
       ``:PRE-COMMIT:``, Graylint works in pre-commit compatible mode. Graylint expects
       the revision range from the ``PRE_COMMIT_FROM_REF`` and ``PRE_COMMIT_TO_REF``
       environment variables. If those are not found, Graylint works against ``HEAD``.
       Also see ``--stdin-filename=`` for the ``:STDIN:`` special value.
--stdin-filename PATH
       The path to the file when passing it through stdin. Useful so Graylint can find
       the previous version from Git. Only valid with ``--revision=<rev1>..:STDIN:``
       (``HEAD..:STDIN:`` being the default if ``--stdin-filename`` is enabled).
-c PATH, --config PATH
       Read Graylint configuration from ``PATH``. Note that linters run by Graylint
       won't read this configuration file.
-v, --verbose
       Show steps taken and summarize modifications
-q, --quiet
       Reduce amount of output
--color
       Enable syntax highlighting even for non-terminal output. Overrides the
       environment variable PY_COLORS=0
--no-color
       Disable syntax highlighting even for terminal output. Overrides the environment
       variable PY_COLORS=1
-W WORKERS, --workers WORKERS
       How many parallel workers to allow, or ``0`` for one per core [default: 1]
-L CMD, --lint CMD
       Run a linter on changed files. ``CMD`` can be a name or path of the linter
       binary, or a full quoted command line with the command and options. Linters read
       their configuration as normally, and aren't affected by ``-c`` / ``--config``.
       Linter output is syntax highlighted when the ``pygments`` package is available if
       run on a terminal and or enabled by explicitly (see ``--color``).

To change default values for these options for a given project,
add a ``[tool.graylint]`` section to ``pyproject.toml`` in the
project's root directory, or to a different TOML file specified using the ``-c`` /
``--config`` option. For example:

.. code-block:: toml

   [tool.graylint]
   src = [
       "src/mypackage",
   ]
   revision = "master"
   lint = [
       "pylint",
   ]
   log_level = "INFO"


Editor integration
==================

Many editors have plugins or recipes for running linters.
You may be able to adapt them to be used with ``graylint``.
Currently we have no specific instructions for any editor,
but we welcome contributions to this document.


Using as a pre-commit hook
==========================

To use Graylint locally as a Git pre-commit hook for a Python project,
do the following:

1. Install pre-commit_ in your environment
   (see `pre-commit Installation`_ for details).

2. Create a base pre-commit configuration::

       pre-commit sample-config >.pre-commit-config.yaml

3. Append to the created ``.pre-commit-config.yaml`` the following lines:

   .. code-block:: yaml

      - repo: https://github.com/akaihola/graylint
        rev: 1.0.0
        hooks:
          - id: graylint

4. install the Git hook scripts and update to the newest version::

       pre-commit install
       pre-commit autoupdate

When auto-updating, care is being taken to protect you from possible incompatibilities
introduced by linter updates. See `Guarding against linter compatibility breakage`_ for
more information.

If you'd prefer to not update but keep a stable pre-commit setup, you can pin linters
you use to known compatible versions, for example:

.. code-block:: yaml

   - repo: https://github.com/akaihola/graylint
     rev: 1.0.0
     hooks:
       - id: graylint
         args:
           - --isort
           - --lint
           - mypy
           - --lint
           - flake8
           - --lint
           - pylint
         additional_dependencies:
           - mypy==0.990
           - flake8==5.0.4
           - pylint==2.15.5

.. _pre-commit: https://pre-commit.com/
.. _pre-commit Installation: https://pre-commit.com/#installation


Using arguments
---------------

You can provide arguments, such as choosing linters, by specifying ``args``.
Note the inclusion of the ``ruff`` Python package under ``additional_dependencies``:

.. code-block:: yaml

   - repo: https://github.com/akaihola/graylint
     rev: 1.0.0
     hooks:
       - id: graylint
         args: [--lint "ruff check"]
         additional_dependencies:
           - ruff~=0.3.2


GitHub Actions integration
==========================

You can use Graylint within a GitHub Actions workflow
without setting your own Python environment.
Great for enforcing that no linter regressions are introduced.

Compatibility
-------------

This action is known to support all GitHub-hosted runner OSes. In addition, only
published versions of Graylint are supported (i.e. whatever is available on PyPI).
You can `search workflows in public GitHub repositories`_ to see how Graylint is being
used.

.. _search workflows in public GitHub repositories: https://github.com/search?q=%22uses%3A+akaihola%2Fgraylint%22+path%3A%2F%5E.github%5C%2Fworkflows%5C%2F.*%2F&type=code

Usage
-----

Create a file named ``.github/workflows/graylint.yml`` inside your repository with:

.. code-block:: yaml

   name: Lint

   on: [push, pull_request]

   jobs:
     lint:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
           with:
             fetch-depth: 0 
         - uses: actions/setup-python@v5
         - uses: akaihola/graylint@1.1.2
           with:
             options: "-v"
             src: "./src"
             version: "~=1.1.2"
             lint: "flake8,pylint==2.13.1"

There needs to be a working Python environment, set up using ``actions/setup-python``
in the above example. Graylint will be installed in an isolated virtualenv to prevent
conflicts with other workflows.

``"uses:"`` specifies which Graylint release to get the GitHub Action definition from.
We recommend to pin this to a specific release.
``"version:"`` specifies which version of Graylint to run in the GitHub Action.
It defaults to the same version as in ``"uses:"``,
but you can force it to use a different version as well.
Graylint versions available from PyPI are supported, as well as commit SHAs or branch
names, prefixed with an ``@`` symbol (e.g. ``version: "@master"``).

The ``revision: "master..."`` (or ``"main..."``) option instructs Graylint
to run linters in the branching point from main branch
and then run them again in the current branch.
If omitted, the Graylint GitHub Action will determine the commit range automatically.

``"src:"`` defines the root directory to run Graylint for.
This is typically the source tree, but you can use ``"."`` (the default)
to also lint Python files like ``"setup.py"`` in the root of the whole repository.

You can also configure other arguments passed to Graylint via ``"options:"``.
It defaults to ``""``.
You can e.g. add ``"--verbose"`` for debug logging.

To run linters through Graylint, you can provide a comma separated list of linters using
the ``lint:`` option. Only ``flake8``, ``pylint`` and ``mypy`` are supported. Other
linters may or may not work with Graylint, depending on their message output format.
Versions can be constrained using ``pip`` syntax, e.g. ``"flake8>=3.9.2"``.


.. _Using linters:

Using linters
=============

Graylint supports any linter with output in one of the following formats::

    <file>:<linenum>: <description>
    <file>:<linenum>:<col>: <description>

Most notably, the following linters/checkers have been verified to work with Graylint:

- Mypy_ for static type checking
- Pylint_ for generic static checking of code
- Flake8_ for style guide enforcement
- `cov_to_lint.py`_ for test coverage

To run a linter, use the ``--lint`` / ``-L`` command line option with the linter
command or a full command line to pass to a linter. Some examples:

- ``-L flake8``: enforce the Python style guide using Flake8_
- ``-L "mypy --strict"``: do static type checking using Mypy_
- ``--lint="pylint --ignore='setup.py'"``: analyze code using Pylint_
- ``-L cov_to_lint.py``: read ``.coverage`` and list non-covered modified lines

**Note:** Full command lines aren't fully tested on Windows. See issue `#456`_ for a
possible bug (in Darker which is where Graylint code originates from).

Graylint also groups linter output into blocks of consecutive lines
separated by blank lines.
Here's an example of `cov_to_lint.py`_ output::

    $ graylint --revision 0.1.0.. --lint cov_to_lint.py src
    src/graylint/__main__.py:94:  no coverage:             logger.debug("No changes in %s after isort", src)
    src/graylint/__main__.py:95:  no coverage:             break

    src/graylint/__main__.py:125: no coverage:         except NotEquivalentError:

    src/graylint/__main__.py:130: no coverage:             if context_lines == max_context_lines:
    src/graylint/__main__.py:131: no coverage:                 raise
    src/graylint/__main__.py:132: no coverage:             logger.debug(

.. _Mypy: https://pypi.org/project/mypy
.. _Pylint: https://pypi.org/project/pylint
.. _Flake8: https://pypi.org/project/flake8
.. _cov_to_lint.py: https://gist.github.com/akaihola/2511fe7d2f29f219cb995649afd3d8d2
.. _#456: https://github.com/akaihola/darker/issues/456


Syntax highlighting
===================

Graylint automatically enables syntax highlighting for the ``-L``/``--lint`` option
if it's running on a terminal and the
Pygments_ package is installed.

You can force enable syntax highlighting on non-terminal output using

- the ``color = true`` option in the ``[tool.graylint]`` section of ``pyproject.toml``
  of your Python project's root directory,
- the ``PY_COLORS=1`` environment variable, and
- the ``--color`` command line option for ``graylint``.
  
You can force disable syntax highlighting on terminal output using

- the ``color = false`` option in ``pyproject.toml``,
- the ``PY_COLORS=0`` environment variable, and
- the ``--no-color`` command line option.

In the above lists, latter configuration methods override earlier ones, so the command
line options always take highest precedence.

.. _Pygments: https://pypi.org/project/Pygments/


Guarding against linter compatibility breakage
==============================================

Graylint relies on calling linters with well-known command line arguments
and expects their output to conform to a defined format.
Graylint is subject to becoming incompatible with future versions of linters
if either of these change.

To protect users against such breakage, we test Graylint daily against main branches of
supported linters and strive to proactively fix any potential incompatibilities through
this process. If a commit to a linter's ``main`` branch introduces an incompatibility
with Graylint, we will release a first patch version for Graylint that prevents
upgrading that linter and a second patch version that fixes the incompatibility.
A hypothetical example:

1. Graylint 9.0.0; Pylint 35.12.0
   -> OK
2. Graylint 9.0.0; Pylint ``main`` (after 35.12.0)
   -> ERROR on CI test-future_ workflow
3. Graylint 9.0.1 released, with constraint ``Pylint<=35.12.0``
   -> OK
4. Pylint 36.1.0 released, but Graylint 9.0.1 prevents upgrade; Pylint 35.12.0
   -> OK
5. Graylint 9.0.2 released with a compatibility fix, constraint removed; Pylint 36.1.0
   -> OK

If a Pylint release introduces an incompatibility before the second Graylint patch
version that fixes it, the first Graylint patch version will downgrade Pylint to the
latest compatible version:

1. Graylint 9.0.0; Pylint 35.12.0
   -> OK
2. Graylint 9.0.0; Pylint 36.1.0
   -> ERROR
3. Graylint 9.0.1, constraint ``Pylint<=35.12.0``; downgrades to Pylint 35.12.0
   -> OK
4. Graylint 9.0.2 released with a compatibility fix, constraint removed; Pylint 36.1.0
   -> OK

To be completely safe, you can pin both Graylint and Pylint to known good versions, but
this may prevent you from receiving improvements in Black. 

It is recommended to use the '``~=``' "`compatible release`_" version specifier for
Graylint to ensure you have the latest version before the next major release that may
cause compatibility issues. 

See issue `#382`_ and PR `#430`_ in Darker (where this feature originates from)
for more information.

.. _compatible release: https://peps.python.org/pep-0440/#compatible-release
.. _test-future: https://github.com/akaihola/graylint/blob/master/.github/workflows/test-future.yml
.. _#382: https://github.com/akaihola/darker/issues/382
.. _#430: https://github.com/akaihola/darker/issues/430


How does it work?
=================

Graylint runs linters in two different revisions of your repository,
records which lines of current files have been edited or added,
and tracks which lines they correspond to in the older revision.
It then filters out any linter errors which appear in both revisions
on matching lines.
Finally, only remaining errors in the newer revision are displayed.


License
=======

BSD. See ``LICENSE.rst``.


Interesting code formatting and analysis projects to watch
==========================================================

The following projects are related to Graylint in some way or another.
Some of them we might want to integrate to be part of a Graylint run.

- Darker__ – Reformat code only in modified blocks of code
- diff-cov-lint__ – Pylint and coverage reports for git diff only
- xenon__ – Monitor code complexity

__ https://github.com/akaihola/darker
__ https://gitlab.com/sVerentsov/diff-cov-lint
__ https://github.com/rubik/xenon


Contributors ✨
===============

Thanks goes to these wonderful people (`emoji key`_):

.. raw:: html

   <!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section
        This is automatically generated. Please update `contributors.yaml` and
        see `CONTRIBUTING.rst` for how to re-generate this table. -->
   <table>
     <tr>
       <td align="center">
         <a href="https://github.com/wnoise">
           <img src="https://avatars.githubusercontent.com/u/9107?v=3" width="100px;" alt="@wnoise" />
           <br />
           <sub>
             <b>Aaron Denney</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Awnoise" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/agandra">
           <img src="https://avatars.githubusercontent.com/u/1072647?v=3" width="100px;" alt="@agandra" />
           <br />
           <sub>
             <b>Aditya Gandra</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Aagandra" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/kedhammar">
           <img src="https://avatars.githubusercontent.com/u/89784800?v=3" width="100px;" alt="@kedhammar" />
           <br />
           <sub>
             <b>Alfred Kedhammar</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/discussions?discussions_q=author%3Akedhammar" title="Bug reports">🐛</a>
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Akedhammar" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/aljazerzen">
           <img src="https://avatars.githubusercontent.com/u/11072061?v=3" width="100px;" alt="@aljazerzen" />
           <br />
           <sub>
             <b>Aljaž Mur Eržen</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/commits?author=aljazerzen" title="Code">💻</a>
       </td>
       <td align="center">
         <a href="https://github.com/akaihola">
           <img src="https://avatars.githubusercontent.com/u/13725?v=3" width="100px;" alt="@akaihola" />
           <br />
           <sub>
             <b>Antti Kaihola</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/search?q=akaihola" title="Answering Questions">💬</a>
         <a href="https://github.com/akaihola/graylint/commits?author=akaihola" title="Code">💻</a>
         <a href="https://github.com/akaihola/graylint/commits?author=akaihola" title="Documentation">📖</a>
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+reviewed-by%3Aakaihola" title="Reviewed Pull Requests">👀</a>
         <a href="https://github.com/akaihola/graylint/commits?author=akaihola" title="Maintenance">🚧</a>
       </td>
       <td align="center">
         <a href="https://github.com/Ashblaze">
           <img src="https://avatars.githubusercontent.com/u/25725925?v=3" width="100px;" alt="@Ashblaze" />
           <br />
           <sub>
             <b>Ashblaze</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/discussions?discussions_q=author%3AAshblaze" title="Bug reports">🐛</a>
       </td>
     </tr>
     <tr>
       <td align="center">
         <a href="https://github.com/levouh">
           <img src="https://avatars.githubusercontent.com/u/31262046?v=3" width="100px;" alt="@levouh" />
           <br />
           <sub>
             <b>August Masquelier</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3Alevouh" title="Code">💻</a>
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Alevouh" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/AckslD">
           <img src="https://avatars.githubusercontent.com/u/23341710?v=3" width="100px;" alt="@AckslD" />
           <br />
           <sub>
             <b>Axel Dahlberg</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3AAckslD" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/baod-rate">
           <img src="https://avatars.githubusercontent.com/u/6306455?v=3" width="100px;" alt="@baod-rate" />
           <br />
           <sub>
             <b>Bao</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3Abaod-rate" title="Code">💻</a>
       </td>
       <td align="center">
         <a href="https://github.com/qubidt">
           <img src="https://avatars.githubusercontent.com/u/6306455?v=3" width="100px;" alt="@qubidt" />
           <br />
           <sub>
             <b>Bao</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Aqubidt" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/falkben">
           <img src="https://avatars.githubusercontent.com/u/653031?v=3" width="100px;" alt="@falkben" />
           <br />
           <sub>
             <b>Ben Falk</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3Afalkben" title="Documentation">📖</a>
         <a href="https://github.com/akaihola/graylint/discussions?discussions_q=author%3Afalkben" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/brtknr">
           <img src="https://avatars.githubusercontent.com/u/2181426?v=3" width="100px;" alt="@brtknr" />
           <br />
           <sub>
             <b>Bharat</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+reviewed-by%3Abrtknr" title="Reviewed Pull Requests">👀</a>
       </td>
     </tr>
     <tr>
       <td align="center">
         <a href="https://github.com/bdperkin">
           <img src="https://avatars.githubusercontent.com/u/3385145?v=3" width="100px;" alt="@bdperkin" />
           <br />
           <sub>
             <b>Brandon Perkins</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Abdperkin" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/casio">
           <img src="https://avatars.githubusercontent.com/u/29784?v=3" width="100px;" alt="@casio" />
           <br />
           <sub>
             <b>Carsten Kraus</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Acasio" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/mrfroggg">
           <img src="https://avatars.githubusercontent.com/u/35123233?v=3" width="100px;" alt="@mrfroggg" />
           <br />
           <sub>
             <b>Cedric</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/search?q=commenter%3Amrfroggg&type=issues" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/chmouel">
           <img src="https://avatars.githubusercontent.com/u/98980?v=3" width="100px;" alt="@chmouel" />
           <br />
           <sub>
             <b>Chmouel Boudjnah</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3Achmouel" title="Code">💻</a>
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Achmouel" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/cclauss">
           <img src="https://avatars.githubusercontent.com/u/3709715?v=3" width="100px;" alt="@cclauss" />
           <br />
           <sub>
             <b>Christian Clauss</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3Acclauss" title="Code">💻</a>
       </td>
       <td align="center">
         <a href="https://github.com/chrisdecker1201">
           <img src="https://avatars.githubusercontent.com/u/20707614?v=3" width="100px;" alt="@chrisdecker1201" />
           <br />
           <sub>
             <b>Christian Decker</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3Achrisdecker1201" title="Code">💻</a>
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Achrisdecker1201" title="Bug reports">🐛</a>
       </td>
     </tr>
     <tr>
       <td align="center">
         <a href="https://github.com/KangOl">
           <img src="https://avatars.githubusercontent.com/u/38731?v=3" width="100px;" alt="@KangOl" />
           <br />
           <sub>
             <b>Christophe Simonis</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3AKangOl" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/CorreyL">
           <img src="https://avatars.githubusercontent.com/u/16601729?v=3" width="100px;" alt="@CorreyL" />
           <br />
           <sub>
             <b>Correy Lim</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/commits?author=CorreyL" title="Code">💻</a>
         <a href="https://github.com/akaihola/graylint/commits?author=CorreyL" title="Documentation">📖</a>
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+reviewed-by%3ACorreyL" title="Reviewed Pull Requests">👀</a>
       </td>
       <td align="center">
         <a href="https://github.com/dkeraudren">
           <img src="https://avatars.githubusercontent.com/u/82873215?v=3" width="100px;" alt="@dkeraudren" />
           <br />
           <sub>
             <b>Damien Keraudren</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/search?q=commenter%3Adkeraudren&type=issues" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/fizbin">
           <img src="https://avatars.githubusercontent.com/u/4110350?v=3" width="100px;" alt="@fizbin" />
           <br />
           <sub>
             <b>Daniel Martin</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Afizbin" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/DavidCDreher">
           <img src="https://avatars.githubusercontent.com/u/47252106?v=3" width="100px;" alt="@DavidCDreher" />
           <br />
           <sub>
             <b>David Dreher</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3ADavidCDreher" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/shangxiao">
           <img src="https://avatars.githubusercontent.com/u/1845938?v=3" width="100px;" alt="@shangxiao" />
           <br />
           <sub>
             <b>David Sanders</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3Ashangxiao" title="Code">💻</a>
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Ashangxiao" title="Bug reports">🐛</a>
       </td>
     </tr>
     <tr>
       <td align="center">
         <a href="https://github.com/dhrvjha">
           <img src="https://avatars.githubusercontent.com/u/43818577?v=3" width="100px;" alt="@dhrvjha" />
           <br />
           <sub>
             <b>Dhruv Kumar Jha</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/search?q=commenter%3Adhrvjha&type=issues" title="Bug reports">🐛</a>
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3Adhrvjha" title="Code">💻</a>
       </td>
       <td align="center">
         <a href="https://github.com/dshemetov">
           <img src="https://avatars.githubusercontent.com/u/1810426?v=3" width="100px;" alt="@dshemetov" />
           <br />
           <sub>
             <b>Dmitry Shemetov</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Adshemetov" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/k-dominik">
           <img src="https://avatars.githubusercontent.com/u/24434157?v=3" width="100px;" alt="@k-dominik" />
           <br />
           <sub>
             <b>Dominik Kutra</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/search?q=commenter%3Ak-dominik&type=issues" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/virtuald">
           <img src="https://avatars.githubusercontent.com/u/567900?v=3" width="100px;" alt="@virtuald" />
           <br />
           <sub>
             <b>Dustin Spicuzza</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Avirtuald" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/DylanYoung">
           <img src="https://avatars.githubusercontent.com/u/5795220?v=3" width="100px;" alt="@DylanYoung" />
           <br />
           <sub>
             <b>DylanYoung</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3ADylanYoung" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/phitoduck">
           <img src="https://avatars.githubusercontent.com/u/32227767?v=3" width="100px;" alt="@phitoduck" />
           <br />
           <sub>
             <b>Eric Riddoch</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Aphitoduck" title="Bug reports">🐛</a>
       </td>
     </tr>
     <tr>
       <td align="center">
         <a href="https://github.com/Eyobkibret15">
           <img src="https://avatars.githubusercontent.com/u/64076953?v=3" width="100px;" alt="@Eyobkibret15" />
           <br />
           <sub>
             <b>Eyob Kibret</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/discussions?discussions_q=author%3AEyobkibret15" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/samoylovfp">
           <img src="https://avatars.githubusercontent.com/u/17025459?v=3" width="100px;" alt="@samoylovfp" />
           <br />
           <sub>
             <b>Filipp Samoilov</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+reviewed-by%3Asamoylovfp" title="Reviewed Pull Requests">👀</a>
       </td>
       <td align="center">
         <a href="https://github.com/philipgian">
           <img src="https://avatars.githubusercontent.com/u/6884633?v=3" width="100px;" alt="@philipgian" />
           <br />
           <sub>
             <b>Filippos Giannakos</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3Aphilipgian" title="Code">💻</a>
       </td>
       <td align="center">
         <a href="https://github.com/foxwhite25">
           <img src="https://avatars.githubusercontent.com/u/39846845?v=3" width="100px;" alt="@foxwhite25" />
           <br />
           <sub>
             <b>Fox_white</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/search?q=foxwhite25" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/gdiscry">
           <img src="https://avatars.githubusercontent.com/u/476823?v=3" width="100px;" alt="@gdiscry" />
           <br />
           <sub>
             <b>Georges Discry</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3Agdiscry" title="Code">💻</a>
       </td>
       <td align="center">
         <a href="https://github.com/gergelypolonkai">
           <img src="https://avatars.githubusercontent.com/u/264485?v=3" width="100px;" alt="@gergelypolonkai" />
           <br />
           <sub>
             <b>Gergely Polonkai</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Agergelypolonkai" title="Bug reports">🐛</a>
       </td>
     </tr>
     <tr>
       <td align="center">
         <a href="https://github.com/muggenhor">
           <img src="https://avatars.githubusercontent.com/u/484066?v=3" width="100px;" alt="@muggenhor" />
           <br />
           <sub>
             <b>Giel van Schijndel</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/commits?author=muggenhor" title="Code">💻</a>
       </td>
       <td align="center">
         <a href="https://github.com/jabesq">
           <img src="https://avatars.githubusercontent.com/u/12049794?v=3" width="100px;" alt="@jabesq" />
           <br />
           <sub>
             <b>Hugo Dupras</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3Ajabesq" title="Code">💻</a>
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Ajabesq" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/hugovk">
           <img src="https://avatars.githubusercontent.com/u/1324225?v=3" width="100px;" alt="@hugovk" />
           <br />
           <sub>
             <b>Hugo van Kemenade</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3Ahugovk" title="Code">💻</a>
       </td>
       <td align="center">
         <a href="https://github.com/irynahryshanovich">
           <img src="https://avatars.githubusercontent.com/u/62266480?v=3" width="100px;" alt="@irynahryshanovich" />
           <br />
           <sub>
             <b>Iryna</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Airynahryshanovich" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/yajo">
           <img src="https://avatars.githubusercontent.com/u/973709?v=3" width="100px;" alt="@yajo" />
           <br />
           <sub>
             <b>Jairo Llopis</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/search?q=commenter%3Ayajo&type=issues" title="Reviewed Pull Requests">👀</a>
       </td>
       <td align="center">
         <a href="https://github.com/jasleen19">
           <img src="https://avatars.githubusercontent.com/u/30443449?v=3" width="100px;" alt="@jasleen19" />
           <br />
           <sub>
             <b>Jasleen Kaur</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Ajasleen19" title="Bug reports">🐛</a>
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+reviewed-by%3Ajasleen19" title="Reviewed Pull Requests">👀</a>
       </td>
     </tr>
     <tr>
       <td align="center">
         <a href="https://github.com/jedie">
           <img src="https://avatars.githubusercontent.com/u/71315?v=3" width="100px;" alt="@jedie" />
           <br />
           <sub>
             <b>Jens Diemer</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Ajedie" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/jenshnielsen">
           <img src="https://avatars.githubusercontent.com/u/548266?v=3" width="100px;" alt="@jenshnielsen" />
           <br />
           <sub>
             <b>Jens Hedegaard Nielsen</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/search?q=jenshnielsen" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/leej3">
           <img src="https://avatars.githubusercontent.com/u/5418152?v=3" width="100px;" alt="@leej3" />
           <br />
           <sub>
             <b>John lee</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/search?q=commenter%3Aleej3&type=issues" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/wkentaro">
           <img src="https://avatars.githubusercontent.com/u/4310419?v=3" width="100px;" alt="@wkentaro" />
           <br />
           <sub>
             <b>Kentaro Wada</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Awkentaro" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/Asuskf">
           <img src="https://avatars.githubusercontent.com/u/36687747?v=3" width="100px;" alt="@Asuskf" />
           <br />
           <sub>
             <b>Kevin David</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/discussions?discussions_q=author%3AAsuskf" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/Krischtopp">
           <img src="https://avatars.githubusercontent.com/u/56152637?v=3" width="100px;" alt="@Krischtopp" />
           <br />
           <sub>
             <b>Krischtopp</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3AKrischtopp" title="Bug reports">🐛</a>
       </td>
     </tr>
     <tr>
       <td align="center">
         <a href="https://github.com/leotrs">
           <img src="https://avatars.githubusercontent.com/u/1096704?v=3" width="100px;" alt="@leotrs" />
           <br />
           <sub>
             <b>Leo Torres</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Aleotrs" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/Carreau">
           <img src="https://avatars.githubusercontent.com/u/335567?v=3" width="100px;" alt="@Carreau" />
           <br />
           <sub>
             <b>M Bussonnier</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/commits?author=Carreau" title="Code">💻</a>
         <a href="https://github.com/akaihola/graylint/commits?author=Carreau" title="Documentation">📖</a>
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+reviewed-by%3ACarreau" title="Reviewed Pull Requests">👀</a>
       </td>
       <td align="center">
         <a href="https://github.com/magnunm">
           <img src="https://avatars.githubusercontent.com/u/45951302?v=3" width="100px;" alt="@magnunm" />
           <br />
           <sub>
             <b>Magnus N. Malmquist</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Amagnunm" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/markddavidoff">
           <img src="https://avatars.githubusercontent.com/u/1360543?v=3" width="100px;" alt="@markddavidoff" />
           <br />
           <sub>
             <b>Mark Davidoff</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Amarkddavidoff" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/dwt">
           <img src="https://avatars.githubusercontent.com/u/57199?v=3" width="100px;" alt="@dwt" />
           <br />
           <sub>
             <b>Martin Häcker</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Adwt" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/matclayton">
           <img src="https://avatars.githubusercontent.com/u/126218?v=3" width="100px;" alt="@matclayton" />
           <br />
           <sub>
             <b>Mat Clayton</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Amatclayton" title="Bug reports">🐛</a>
       </td>
     </tr>
     <tr>
       <td align="center">
         <a href="https://github.com/MatthijsBurgh">
           <img src="https://avatars.githubusercontent.com/u/18014833?v=3" width="100px;" alt="@MatthijsBurgh" />
           <br />
           <sub>
             <b>Matthijs van der Burgh</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3AMatthijsBurgh" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/minrk">
           <img src="https://avatars.githubusercontent.com/u/151929?v=3" width="100px;" alt="@minrk" />
           <br />
           <sub>
             <b>Min RK</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/conda-forge/graylint-feedstock/search?q=graylint+author%3Aminrk&type=issues" title="Code">💻</a>
       </td>
       <td align="center">
         <a href="https://github.com/my-tien">
           <img src="https://avatars.githubusercontent.com/u/3898364?v=3" width="100px;" alt="@my-tien" />
           <br />
           <sub>
             <b>My-Tien Nguyen</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Amy-tien" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/Mystic-Mirage">
           <img src="https://avatars.githubusercontent.com/u/1079805?v=3" width="100px;" alt="@Mystic-Mirage" />
           <br />
           <sub>
             <b>Mystic-Mirage</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/commits?author=Mystic-Mirage" title="Code">💻</a>
         <a href="https://github.com/akaihola/graylint/commits?author=Mystic-Mirage" title="Documentation">📖</a>
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+reviewed-by%3AMystic-Mirage" title="Reviewed Pull Requests">👀</a>
       </td>
       <td align="center">
         <a href="https://github.com/njhuffman">
           <img src="https://avatars.githubusercontent.com/u/66969728?v=3" width="100px;" alt="@njhuffman" />
           <br />
           <sub>
             <b>Nathan Huffman</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Anjhuffman" title="Bug reports">🐛</a>
         <a href="https://github.com/akaihola/graylint/commits?author=njhuffman" title="Code">💻</a>
       </td>
       <td align="center">
         <a href="https://github.com/wasdee">
           <img src="https://avatars.githubusercontent.com/u/8089231?v=3" width="100px;" alt="@wasdee" />
           <br />
           <sub>
             <b>Nutchanon Ninyawee</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Awasdee" title="Bug reports">🐛</a>
       </td>
     </tr>
     <tr>
       <td align="center">
         <a href="https://github.com/Pacu2">
           <img src="https://avatars.githubusercontent.com/u/21290461?v=3" width="100px;" alt="@Pacu2" />
           <br />
           <sub>
             <b>Pacu2</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3APacu2" title="Code">💻</a>
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+reviewed-by%3APacu2" title="Reviewed Pull Requests">👀</a>
       </td>
       <td align="center">
         <a href="https://github.com/PatrickJordanCongenica">
           <img src="https://avatars.githubusercontent.com/u/85236670?v=3" width="100px;" alt="@PatrickJordanCongenica" />
           <br />
           <sub>
             <b>Patrick Jordan</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/discussions?discussions_q=author%3APatrickJordanCongenica" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/ivanov">
           <img src="https://avatars.githubusercontent.com/u/118211?v=3" width="100px;" alt="@ivanov" />
           <br />
           <sub>
             <b>Paul Ivanov</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/commits?author=ivanov" title="Code">💻</a>
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Aivanov" title="Bug reports">🐛</a>
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+reviewed-by%3Aivanov" title="Reviewed Pull Requests">👀</a>
       </td>
       <td align="center">
         <a href="https://github.com/gesslerpd">
           <img src="https://avatars.githubusercontent.com/u/11217948?v=3" width="100px;" alt="@gesslerpd" />
           <br />
           <sub>
             <b>Peter Gessler</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Agesslerpd" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/flying-sheep">
           <img src="https://avatars.githubusercontent.com/u/291575?v=3" width="100px;" alt="@flying-sheep" />
           <br />
           <sub>
             <b>Philipp A.</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Aflying-sheep" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/RishiKumarRay">
           <img src="https://avatars.githubusercontent.com/u/87641376?v=3" width="100px;" alt="@RishiKumarRay" />
           <br />
           <sub>
             <b>Rishi Kumar Ray</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/search?q=RishiKumarRay" title="Bug reports">🐛</a>
       </td>
     </tr>
     <tr>
       <td align="center">
         <a href="https://github.com/ioggstream">
           <img src="https://avatars.githubusercontent.com/u/1140844?v=3" width="100px;" alt="@ioggstream" />
           <br />
           <sub>
             <b>Roberto Polli</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/search?q=commenter%3Aioggstream&type=issues" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/roniemartinez">
           <img src="https://avatars.githubusercontent.com/u/2573537?v=3" width="100px;" alt="@roniemartinez" />
           <br />
           <sub>
             <b>Ronie Martinez</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Aroniemartinez" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/rossbar">
           <img src="https://avatars.githubusercontent.com/u/1268991?v=3" width="100px;" alt="@rossbar" />
           <br />
           <sub>
             <b>Ross Barnowski</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Arossbar" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/sgaist">
           <img src="https://avatars.githubusercontent.com/u/898010?v=3" width="100px;" alt="@sgaist" />
           <br />
           <sub>
             <b>Samuel Gaist</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3Asgaist" title="Code">💻</a>
       </td>
       <td align="center">
         <a href="https://github.com/seweissman">
           <img src="https://avatars.githubusercontent.com/u/3342741?v=3" width="100px;" alt="@seweissman" />
           <br />
           <sub>
             <b>Sarah</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Aseweissman" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/sherbie">
           <img src="https://avatars.githubusercontent.com/u/15087653?v=3" width="100px;" alt="@sherbie" />
           <br />
           <sub>
             <b>Sean Hammond</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+reviewed-by%3Asherbie" title="Reviewed Pull Requests">👀</a>
       </td>
     </tr>
     <tr>
       <td align="center">
         <a href="https://github.com/hauntsaninja">
           <img src="https://avatars.githubusercontent.com/u/12621235?v=3" width="100px;" alt="@hauntsaninja" />
           <br />
           <sub>
             <b>Shantanu</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Ahauntsaninja" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/simgunz">
           <img src="https://avatars.githubusercontent.com/u/466270?v=3" width="100px;" alt="@simgunz" />
           <br />
           <sub>
             <b>Simone Gaiarin</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/search?q=commenter%3Asimgunz&type=issues" title="Reviewed Pull Requests">👀</a>
       </td>
       <td align="center">
         <a href="https://github.com/soxofaan">
           <img src="https://avatars.githubusercontent.com/u/44946?v=3" width="100px;" alt="@soxofaan" />
           <br />
           <sub>
             <b>Stefaan Lippens</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3Asoxofaan" title="Documentation">📖</a>
       </td>
       <td align="center">
         <a href="https://github.com/strzonnek">
           <img src="https://avatars.githubusercontent.com/u/80001458?v=3" width="100px;" alt="@strzonnek" />
           <br />
           <sub>
             <b>Stephan Trzonnek</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Astrzonnek" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/tkolleh">
           <img src="https://avatars.githubusercontent.com/u/3095197?v=3" width="100px;" alt="@tkolleh" />
           <br />
           <sub>
             <b>TJ Kolleh</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Atkolleh" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/talhajunaidd">
           <img src="https://avatars.githubusercontent.com/u/6547611?v=3" width="100px;" alt="@talhajunaidd" />
           <br />
           <sub>
             <b>Talha Juanid</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/commits?author=talhajunaidd" title="Code">💻</a>
       </td>
     </tr>
     <tr>
       <td align="center">
         <a href="https://github.com/guettli">
           <img src="https://avatars.githubusercontent.com/u/414336?v=3" width="100px;" alt="@guettli" />
           <br />
           <sub>
             <b>Thomas Güttler</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Aguettli" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/tobiasdiez">
           <img src="https://avatars.githubusercontent.com/u/5037600?v=3" width="100px;" alt="@tobiasdiez" />
           <br />
           <sub>
             <b>Tobias Diez</b>
           </sub>
         </a>
         <br />
       </td>
       <td align="center">
         <a href="https://github.com/tapted">
           <img src="https://avatars.githubusercontent.com/u/1721312?v=3" width="100px;" alt="@tapted" />
           <br />
           <sub>
             <b>Trent Apted</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Atapted" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/tgross35">
           <img src="https://avatars.githubusercontent.com/u/13724985?v=3" width="100px;" alt="@tgross35" />
           <br />
           <sub>
             <b>Trevor Gross</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Atgross35" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/victorcui96">
           <img src="https://avatars.githubusercontent.com/u/14048976?v=3" width="100px;" alt="@victorcui96" />
           <br />
           <sub>
             <b>Victor Cui</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/search?q=commenter%3Avictorcui96&type=issues" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/yoursvivek">
           <img src="https://avatars.githubusercontent.com/u/163296?v=3" width="100px;" alt="@yoursvivek" />
           <br />
           <sub>
             <b>Vivek Kushwaha</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Ayoursvivek" title="Bug reports">🐛</a>
         <a href="https://github.com/akaihola/graylint/commits?author=yoursvivek" title="Documentation">📖</a>
       </td>
     </tr>
     <tr>
       <td align="center">
         <a href="https://github.com/Hainguyen1210">
           <img src="https://avatars.githubusercontent.com/u/15359217?v=3" width="100px;" alt="@Hainguyen1210" />
           <br />
           <sub>
             <b>Will</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3AHainguyen1210" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/wjdp">
           <img src="https://avatars.githubusercontent.com/u/1690934?v=3" width="100px;" alt="@wjdp" />
           <br />
           <sub>
             <b>Will Pimblett</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Awjdp" title="Bug reports">🐛</a>
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3Awjdp" title="Documentation">📖</a>
       </td>
       <td align="center">
         <a href="https://github.com/wpnbos">
           <img src="https://avatars.githubusercontent.com/u/33165624?v=3" width="100px;" alt="@wpnbos" />
           <br />
           <sub>
             <b>William Bos</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Awpnbos" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/zachnorton4C">
           <img src="https://avatars.githubusercontent.com/u/49661202?v=3" width="100px;" alt="@zachnorton4C" />
           <br />
           <sub>
             <b>Zach Norton</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Azachnorton4C" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/clintonsteiner">
           <img src="https://avatars.githubusercontent.com/u/47841949?v=3" width="100px;" alt="@clintonsteiner" />
           <br />
           <sub>
             <b>csteiner</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Aclintonsteiner" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/deadkex">
           <img src="https://avatars.githubusercontent.com/u/59506422?v=3" width="100px;" alt="@deadkex" />
           <br />
           <sub>
             <b>deadkex</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/discussions?discussions_q=author%3Adeadkex" title="Bug reports">🐛</a>
       </td>
     </tr>
     <tr>
       <td align="center">
         <a href="https://github.com/dsmanl">
           <img src="https://avatars.githubusercontent.com/u/67360039?v=3" width="100px;" alt="@dsmanl" />
           <br />
           <sub>
             <b>dsmanl</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Adsmanl" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/jsuit">
           <img src="https://avatars.githubusercontent.com/u/1467906?v=3" width="100px;" alt="@jsuit" />
           <br />
           <sub>
             <b>jsuit</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/discussions?discussions_q=author%3Ajsuit" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/martinRenou">
           <img src="https://avatars.githubusercontent.com/u/21197331?v=3" width="100px;" alt="@martinRenou" />
           <br />
           <sub>
             <b>martinRenou</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/conda-forge/staged-recipes/search?q=graylint&type=issues&author=martinRenou" title="Code">💻</a>
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+reviewed-by%3AmartinRenou" title="Reviewed Pull Requests">👀</a>
       </td>
       <td align="center">
         <a href="https://github.com/mayk0gan">
           <img src="https://avatars.githubusercontent.com/u/96263702?v=3" width="100px;" alt="@mayk0gan" />
           <br />
           <sub>
             <b>mayk0gan</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Amayk0gan" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/okuuva">
           <img src="https://avatars.githubusercontent.com/u/2804020?v=3" width="100px;" alt="@okuuva" />
           <br />
           <sub>
             <b>okuuva</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/search?q=commenter%3Aokuuva&type=issues" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/overratedpro">
           <img src="https://avatars.githubusercontent.com/u/1379994?v=3" width="100px;" alt="@overratedpro" />
           <br />
           <sub>
             <b>overratedpro</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Aoverratedpro" title="Bug reports">🐛</a>
       </td>
     </tr>
     <tr>
       <td align="center">
         <a href="https://github.com/simonf-dev">
           <img src="https://avatars.githubusercontent.com/u/52134089?v=3" width="100px;" alt="@simonf-dev" />
           <br />
           <sub>
             <b>sfoucek</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/search?q=commenter%3Asimonf-dev&type=issues" title="Bug reports">🐛</a>
       </td>
       <td align="center">
         <a href="https://github.com/rogalski">
           <img src="https://avatars.githubusercontent.com/u/9485217?v=3" width="100px;" alt="@rogalski" />
           <br />
           <sub>
             <b>Łukasz Rogalski</b>
           </sub>
         </a>
         <br />
         <a href="https://github.com/akaihola/graylint/pulls?q=is%3Apr+author%3Arogalski" title="Code">💻</a>
         <a href="https://github.com/akaihola/graylint/issues?q=author%3Arogalski" title="Bug reports">🐛</a>
       </td>
     </tr>
   </table>   <!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the all-contributors_ specification.
Contributions of any kind are welcome!

.. _README.rst: https://github.com/akaihola/graylint/blob/master/README.rst
.. _emoji key: https://allcontributors.org/docs/en/emoji-key
.. _all-contributors: https://allcontributors.org


GitHub stars trend
==================

|stargazers|_

.. |stargazers| image:: https://starchart.cc/akaihola/graylint.svg
.. _stargazers: https://starchart.cc/akaihola/graylint
