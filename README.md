These are a couple of scripts I wrote to make defining [Git
aliases][git-aliases] simpler by, among other things, removing a lot of the
boilerplate.

[git-aliases]: https://git-scm.com/book/en/v2/Git-Basics-Git-Aliases

## Installation

### `git clone`

The simplest way to install these scripts is to clone this repository, then
symlink the `.sh` files into a location which is available on your PATH.

For example, if `~/.local/bin` is on your path:

```console
$ git clone https://github.com/benblank/git-alias.git
$ ln -s "$PWD"/git-alias/git-alias.sh ~/.local/bin/git-alias
$ ln -s "$PWD"/git-alias/git-unalias.sh ~/.local/bin/git-unalias
```

_Note that the destination names lack the `.sh` extension. This is imporant, as
Git will otherwise require you to include it when invoking the scripts!_

This makes it easy to update the scripts when new versions are released, by
going back into the git-alias directory and running `git pull`.

### Downloading directly

Alternatively, you can download the files and place them in a directory which is
on your PATH. Make sure to also download the `.awk` files, which are necessary
to view your aliases. They must be in the same directory as the `git-alias.sh`
and `git-unalias.sh` scripts, though a single level of symlinking should work
fine.

For example, if `~/.local/bin` is on your path and you downloaded all the files
to `~/Downloads`:

```console
$ mv ~/Downloads/git-alias.sh ~/.local/bin/git-alias
$ mv ~/Downloads/git-unalias.sh ~/.local/bin/git-unalias
$ mv ~/Downloads/handle-gitconfig.awk ~/.local/bin
$ mv ~/Downloads/handle-shell.awk ~/.local/bin
$ mv ~/Downloads/read-aliases.awk ~/.local/bin
$ mv ~/Downloads/git-alias.sh ~/.local/bin
$ chmod +x ~/.local/bin/git-alias
$ chmod +x ~/.local/bin/git-unalias
```

_Note that the main scripts are given new names, without the `.sh` extension.
This is imporant, as Git will otherwise require you to include it when invoking
the scripts! You also need to make those scripts executable (the awk scripts
don't need to be)._

## Configuration files

All subcommands added by git-alias operate on configuration files, and you can
specify which file you want them to use. By default, they will use the value
stored at the location specified in your `git-alias.config-file` Git setting,
which can be either one of the flags in the [Common flags](#common-flags)
section or the path to a file. If that setting is absent, your "global" Git
configuration will be used instead (usually `~/.gitconfig`).

When invoking a git-alias subcommand, you can also use any of the flags
understood by `git config` to change which file is used to store aliases.

### Example: Moving your existing aliases into a separate file

I find it convenient to keep my Git aliases in a dedicated file, so that I can
share it between computers without bringing along _all_ of my Git settings (some
of which are system-specific). Using the steps below, you can move your new or
existing aliases into a separate file.

_Be sure to back up your Git configuration first, just in case something goes
wrong._

1. Move your existing global aliases to a new file:

   ```console
   $ git alias --global > ~/.gitconfig-aliases
   ```

2. Remove your aliases from the global configuration file:

   ```console
   $ git unalias --global '*'
   ```

3. Tell Git where to find your aliases:

   ```console
   $ git config --global --add include.path ~/.gitconfig-aliases
   ```

   Afterward, verify that your Git aliases still work.

4. Tell git-alias where to find your aliases:

   ```console
   $ git config --global git-alias.config-file ~/.gitconfig-aliases
   ```

   Afterward, verify that git-alias can still find your aliases:

   ```console
   $ git alias
   ```

### Example: Using local aliases in a repository

Because Git gets its configuration from the most specific file available, it's
easy to use git-alias to manage local aliases for individual repositories but
still manage global ones elsewhere.

Inside a repository, run `git config git-alias.config-file --local` to tell
git-alias to use the local configuration file. Now, Git will recognize aliases
in both the global and local configuration files, but git-alias will manage only
the local ones by default.

If you ever need to manage global aliases while in that repository, you can
simply use the `--global` flag.

## Subcommands

### Common flags

- `--file <path>` — Store aliases in the specified file.

- `--global` (default when `git-alias.config-file` isn't set) — Store aliases in
  the global configuration file (usually `~/.gitconfig`).

- `--local` — Store aliases in the per-repository configuration file
  (`<repo root>/.git/config`).

- `--system` — Store aliases in the system configuration file (usually
  `/etc/gitconfig`, but can vary by system). Note that normal users may not have
  write permission to this file.

- `--worktree` — Store aliases in the worktree's configuration file, if
  worktrees are enabled. Otherwise, behaves like `--local`.

### `git alias`

This subcommand lets you define, redefine, and view Git aliases without having
to use the `git config` command directly. It works on your global Git
configuration (`~/.gitconfig`) by default, but this can be changed using the
`--local` flag.

You can invoke this subcommand with zero, one, or more than one positional
parameters.

Invoked without any parameters, it displays all defined Git aliases as either
`git alias …` commands (the default) or in the requested format (see the flags
below).

With a single parameter, only the alias with that name is displayed; if no such
alias exists, an error will be reported.

With more than one parameter, the first is taken to be an alias name and a new
alias with that name is defined as the remaining parameters (joined by spaces).
For example, these invocations create identical aliases:

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
  configuration file when displaying them, including the `[alias]` section
  header. Not applicable when creating an alias.

- `--config-no-header` — Format aliases as appropriate for including in a Git
  configuration file when displaying them, but do **not** include the `[alias]`
  section header or indent the definitions. Not applicable when creating an
  alias.

- `--json` — Format aliases as "pretty-printed" JSON when displaying them. Not
  applicable when creating an alias.

- `--json-compact` — Format aliases as JSON when displaying them, but do not
  include unnecessary whitespace (not even a trailing newline).

- `--shell` (default) — Format aliases as appropriate for execution via the
  shell when displaying them. Not applicable when creating an alias.

_See also the section on [common flags](#common-flags)._

### `git unalias`

This subcommand lets you remove defined aliases without having to use the
`git config` command directly. It works on your global Git configuration
(`~/.gitconfig`) by default, but this can be changed using the `--local` flag.

When you invoke it, you must supply at least one parameter. Each parameter is
then used as a matching pattern to determine which alias(es) to delete. When
using patterns, make sure to quote them on the command line, or your shell may
try to expand them! It can also be handy to use the `--dry-run` flag to test
them before you commit to removing anything.

The exact features of the pattern matching may vary from system to system,
though I would expect `?` (single-character wildcard) and `*` (multi-character
wildcard) to work anywhere. They will behave the same way patterns in `case`
statements do in your `/bin/sh` shell.

#### Flags

You can optionally provide flags to `git unalias` which modify its behavior.
Flags are interpreted in the order in which they appear, which means that flags
which appear later "override" flags which appear earlier. In other words,
`git unalias --local --global foo` will remove the alias "foo" from the global
Git configuration file, as that flag appeared last.

All flags must precede the alias name.

- `--dry-run` — Print the names of any aliases which _would_ be removed, but
  don't actually remove any of them. This is handy for testing your patterns
  before using them!

_See also the section on [common flags](#common-flags)._
