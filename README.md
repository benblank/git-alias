These are a couple of scripts I wrote to make defining [Git
aliases][git-aliases] simpler by, among other things, removing a lot of the
boilerplate.

[git-aliases]: https://git-scm.com/book/en/v2/Git-Basics-Git-Aliases

## Installation

The simplest way to install these scripts is to clone this repository or
download the scripts directly using the "Raw" buttons at the top of their GitHub
pages, then copy/move/symlink them into a location which is available on your
PATH.

For example, if `~/.local/bin` is on your path:

```
$ git clone https://github.com/benblank/git-alias.git
$ ln -s "$(pwd)"/git-alias/git-alias.sh ~/.local/bin/git-alias
$ ln -s "$(pwd)"/git-alias/git-unalias.sh ~/.local/bin/git-unalias
```

Note that the destination names lack the `.sh` extension. This is imporant, as
Git will otherwise require you to include it when invoking the scripts!

## Subcommands

### `git alias`

This subcommand lets you define, redefine, and view Git aliases without having
to use the `git config` command directly. It works on your global Git
configuration (`~/.gitconfig`) by default, but this can be changed using the
`--local` flag.

You can invoke this subcommand with zero, one, or more than one positional
parameters.

Invoked without any parameters, it displays all defined Git aliases as either
`git alias …` commands (the default) or as Git configuration lines (when given
the `--config` flag). Displaying all existing aliases requires gawk to be
present on your system.

With a single parameter, only the alias with that name is displayed; if no such
alias exists, an error will be reported.

With more than one parameter, the first is taken to be an alias name and a new
alias with that name is defined as the remaining parameters (joined by spaces).
For example, these invokations create identical aliases:

```
$ git alias cdiff "diff --cached"
$ git alias cdiff diff --cached
```

If you need control over the whitespace in your alias, it's always best to quote
it yourself rather than let `git alias` join it together for you.

Defining an alias whose name matches an existing alias will replace that alias
with the new definion.

#### Flags

You can optionally provide flags to `git alias` which modify its behavior. Flags
are interpreted in the order in which they appear, which means that flags which
appear later "override" flags which appear earlier. In other words,
`git alias --config --shell` will display all aliases in shell format, as that
flag appeared last.

All flags must precede the alias name, if any.

- `--config` — Format aliases as appropriate for including in a Git
  configuration file when displaying them. Overrides `--shell`. Not applicable
  when creating an alias.

- `--global` (default) — Use the "global" Git configuration file
  (`~/.gitconfig`) when reading or creating aliases. Overrides `--local`.

- `--header` (default when using `--config`) — Include the `[alias]` section
  header when displaying aliases and indent each alias definition. Overrides
  `--no-header`. Only applicable after `--config`.

- `--local` — Use the "local" Git configuration file
  (`<repository-root>/.git/config`) when reading or creating aliases. Overrides
  `--global`.

- `--no-header` — Do not include a section header or use indentation when
  displaying aliases. Overrides `--header`. Only applicable after `--config`.

- `--shell` (default) — Format aliases as appropriate for execution via the
  shell when displaying them. Overrides `--config`. Not applicable when creating
  an alias.

### `git unalias`

This subcommand lets you remove a defined alias without having to use the
`git config` command directly. It works on your global Git configuration
(`~/.gitconfig`) by default, but this can be changed using the `--local` flag.

You must invoke it with a single parameter; the name of the alias to remove.

#### Flags

You can optionally provide flags to `git unalias` which modify its behavior.
Flags are interpreted in the order in which they appear, which means that flags
which appear later "override" flags which appear earlier. In other words,
`git unalias --local --global foo` will remove the alias "foo" from the global
Git configuration file, as that flag appeared last.

All flags must precede the alias name.

- `--global` (default) — Use the "global" Git configuration file
  (`~/.gitconfig`) when removing aliases. Overrides `--local`.

- `--local` — Use the "local" Git configuration file
  (`<repository-root>/.git/config`) when removing aliases. Overrides `--global`.
