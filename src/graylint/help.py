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

FORMAT_TEMPLATE = (
    "Specify output format and destination. Format can be one of:"
    " {output_format_names}. Optional destination path can be specified after colon,"
    " e.g. 'gnu:-' for stdout or 'gnu:annotations.txt' for file output. Multiple "
    " formats can be specified with comma separation or by repeating the option."
)
