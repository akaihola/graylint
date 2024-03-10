"""Help and usage instruction texts used for the command line parser"""

DESCRIPTION = (
    "Run linters on old and new versions of Python source files and hide unchanged"
    " messages"
)

LINT = (
    "Run a linter on changed files. `CMD` can be a name or path of the linter binary,"
    " or a full quoted command line with the command and options. Linters read their"
    " configuration as normally, and aren't affected by `-c` / `--config`. Linter"
    " output is syntax highlighted when the `pygments` package is available if run on"
    " a terminal and or enabled by explicitly (see `--color`)."
)
