## Still to do

- investigate handling of paths which need escaped (e.g. contain spaces) on
  command line and in git-alias.config-file (probably doesn't work without some
  weird quoting)
- add name-only output to `git alias`
- add wildcard support to `git alias <name>` (get all names a la unalias, find
  matching names, combine into `--get-regex '^alias\.(one|two|three)$'`?)
- switch to using `--null` instead of accumulating lines?
- combine git-alias.sh and git-unalias.sh into a single script (`git alias add`,
  `git alias remove`, `git alias show`)
- add better test coverage for failure states (invalid alias names, etc.)
- add output when defining an alias?

## Done

- ~~add JSON output to `git alias` (formatting?)~~
- ~~harden scripts against variable injection (e.g. `indent=foo git alias --config --no-header`)~~
- ~~reorganize `git-alias.sh` to make it less redundant (the sections for each
  formatting style are nearly identical)~~
- ~~write at least _some_ tests 😔~~
- ~~fix handling of relative symlinks~~
- ~~give `TestExecutionContext` knowledge of location flags~~
- ~~rejigger command-line options (`--json` `--compact` -> `--json-compact`?)~~
