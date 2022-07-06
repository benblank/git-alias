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
to use the `git config` command directly. It works exclusively on your global
Git configuration (`~/.gitconfig`).

You can invoke this subcommand with zero, one, or more than one parameters.
Invoked without any parameters, it displays all defined Git aliases as
`git alias …` commands. With a single parameter, only the alias with that name
is displayed; if no such alias exists, an error will be reported. Displaying
existing aliases requires gawk to be present on your system.

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

### `git unalias`

This subcommand lets you remove a defined alias without having to use the
`git config` command directly. It works exclusively on your global Git
configuration (`~/.gitconfig`).

You must invoke it with a single parameter; the name of the alias to remove.
