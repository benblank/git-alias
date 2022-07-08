## Still to do

- awk doesn't like aliases with percent signs in them (interprets as format
  string)
- add wildcard support to `git alias <name>` (get all names a la unalias, find
  matching names, combine into `--get-regex '^alias\.(one|two|three)$'`?)
- combine git-alias.sh and git-unalias.sh into a single script (`git alias add`,
  `git alias remove`, `git alias show`)
- add better test coverage for failure states (invalid alias names, etc.)
- what about `--file --foo` or `--file --global`?
- dash is funny about echoing backslash sequences; replace everything with
  printf?
- validate alias names before passing them to git — "variable names are
  case-insensitive, allow only alphanumeric characters and -, and must start
  with an alphabetic character"
- trailing whitespace is being stripped when showing aliases (e.g. `git alias
  add foo 'bar '; git alias show --shell foo` saves the alias correctly, but
  prints `git alias add foo bar`)

## Done

- ~~add JSON output to `git alias` (formatting?)~~
- ~~harden scripts against variable injection (e.g. `indent=foo git alias
  --config --no-header`)~~
- ~~reorganize `git-alias.sh` to make it less redundant (the sections for each
  formatting style are nearly identical)~~
- ~~write at least _some_ tests 😔~~
- ~~fix handling of relative symlinks~~
- ~~give `TestExecutionContext` knowledge of location flags~~
- ~~rejigger command-line options (`--json` `--compact` -> `--json-compact`?)~~
- ~~add name-only output to `git alias`~~
- ~~investigate handling of paths which need escaped (e.g. contain spaces) on
  command line and in git-alias.config-file (probably doesn't work without some
  weird quoting)~~
