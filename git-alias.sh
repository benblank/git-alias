#!/bin/sh

status=0
where=default

show_help_and_exit() {
  case "$1" in
    add )
      >&2 echo
      >&2 echo "  Usage: git alias [location flag] add <name> <body>"
      >&2 echo
      >&2 echo "See \`git alias help\` for information about location flags."
      >&2 echo
      >&2 echo "You may supply the alias body as either a single parameter (recommended) or as a"
      >&2 echo "sequence of parameters, which will automatically be joined by spaces."
    ;;

    remove )
      >&2 echo
      >&2 echo "  Usage: git alias [location flag] remove [--dry-run] <pattern...>"
      >&2 echo
      >&2 echo "See \`git alias help\` for information about location flags."
      >&2 echo
      >&2 echo "--dry-run  Don't actually remove any aliases, just print what would be removed."
      >&2 echo
      >&2 echo "Patterns may incude the characters '?' and '*', which have the same meaning as"
      >&2 echo "they do in file pattern-matching."
    ;;

    show )
      >&2 echo
      >&2 echo "  Usage: git alias [location flag] show [pattern...]"
      >&2 echo
      >&2 echo "See \`git alias help\` for information about location flags."
      >&2 echo
      >&2 echo "Patterns may incude the characters '?' and '*', which have the same meaning as"
      >&2 echo "they do in file pattern-matching. If you don't provide any patterns, all aliases"
      >&2 echo "defined in the specified location will be displayed."
    ;;

    "" )
      >&2 echo
      >&2 echo "  Usage: git alias [location flag] <add|remove|show> [command-specific args]"
      >&2 echo
      >&2 echo "Location flags: (optional, same meaning as for \`git config\`)"
      >&2 echo "  --file <filename>  Operate on aliases in the named file."
      >&2 echo "  --global           Operate on aliases in the user's global config file."
      >&2 echo "  --local            Operate on aliases in the local repo's config file."
      >&2 echo "  --system           Operate on aliases in the system-wide config file."
      >&2 echo "  --worktree         Operate on aliases in the current worktree's config file."
      >&2 echo
      >&2 echo "If no location flag is provided on the command line, \`git alias\` will try to"
      >&2 echo "read it from the Git config setting 'git-alias.config-file'. If not set, it"
      >&2 echo "defaults to \`--global\`."
    ;;

    * )
      >&2 echo "Internal error! '$1' is not a valid help type!"

      status=127
    ;;
  esac

  exit $status
}

case "$1" in
  --file )
    if [ -z "$2" ]; then
      >&2 echo "\`--file\` requires a filename."

      status=1

      show_help_and_exit
    fi

    where="$2"
    shift 2
  ;;

  --global | --local | --system | --worktree ) where=$1; shift;;
esac

# Convert the default file location into a valid command-line flag for Git. If a
# flag or custom file is configured, use that. Otherwise, fall back to the
# global file.
if [ "$where" = default ]; then
  configured_location="$(git config --get git-alias.config-file)"

  case "$configured_location" in
    "" ) where=--global;;
    --global | --local | --system | --worktree ) where="$configured_location";;
    "--file "* ) where="$(echo "$configured_location" | cut -c 8-)";;
    * ) where="$configured_location";;
  esac
fi

## Run a command on all aliases matching a pattern.
##
## The first parameter is the pattern to match against; the second is the
## command to run.
##
## Alias names are read from the global `names` variable and any which were not
## matched are stored back to it. If the command results in a non-zero exit code
## for a name, that name will be considered "unusued" and remain in `names`.
##
## If a pattern fails to match any remaining aliases, an error is printed and
## the script's exit code is set to 1.
match_aliases() {
  found=
  remaining=
  pattern="$1"
  command="$2"

  # `$names` is deliberately unquoted so that its words (the names of the
  # aliases) can be spread into positional parameters.
  #
  # shellcheck disable=2086
  set -- $names

  while [ $# -gt 0 ]; do
    # `$pattern` is deliberately unquoted so that it can act as a pattern.
    #
    # shellcheck disable=2254
    case "$1" in
      $pattern )
        if "$command" "$1"; then
          found=1
        else
          # Assume that a non-zero status means the alias was not successfully
          # processed.
          remaining="$remaining $1"
        fi
      ;;

      * ) remaining="$remaining $1";;
    esac

    shift
  done

  if [ -n "$found" ]; then
    names="$remaining"
  else
    >&2 echo "${dry_run}No aliases matching \"$pattern\" were found."

    status=1
  fi
}

populate_names() {
    # This variable stores the names of aliases which have been discovered, but
    # not yet acted upon. It is updated by `match_aliases` to remove the names
    # of any aliases which were passed to the associated command. This allows us
    # to prevent trying to process the same alias multiple times if it matches
    # multiple patterns without having to re-query `git config` after every
    # iteration.
    case "$where" in
      --* ) names="$(git config "$where" --name-only --get-regexp ^alias\\. | cut -d . -f 2)";;
      * ) names="$(git config --file "$where" --name-only --get-regexp ^alias\\. | cut -d . -f 2)";;
    esac
}

case "$1" in
  add )
    if [ $# -lt 3 ]; then
      >&2 echo "You must provide both a name and a body to define an alias."

      status=1

      show_help_and_exit add
    fi

    name="$2"
    shift 2

    # Using "$*" here allows commands like `git alias cdiff diff --cached` to work
    # as expected by combining all the arguments after the alias name into a
    # single string.
    if ! case "$where" in
        --* ) git config "$where" alias."$name" "$*";;
        * ) git config --file "$where" alias."$name" "$*";;
      esac
    then
      status=1
    fi
  ;;

  remove )
    shift

    dry_run=

    if [ "$1" = "--dry-run" ]; then
      dry_run="[dry-run] "

      shift
    fi

    if [ $# -eq 0 ]; then
      >&2 echo "You must provide at least one name or pattern to remove."

      status=1

      show_help_and_exit remove
    fi

    unset_alias() {
      if [ -n "$dry_run" ] || (
        case "$where" in
          --* ) git config "$where" --unset alias."$1";;
          * ) git config --file "$where" --unset alias."$1";;
        esac
      ); then
        echo "${dry_run}'unset $1'"
      else
        >&2 echo "Failed to unset alias $1, which matched pattern '$pattern'."

        return 1
      fi
    }

    populate_names

    while [ $# -gt 0 ]; do
      match_aliases "$1" unset_alias

      shift
    done
  ;;

  show )
    shift

    format=--config

    case "$1" in
      --config | --config-no-header | --json | --json-compact | --names-only | --shell ) format=$1; shift;;
    esac

    # I was unable to find a portable way to do this other than to implement it
    # myself. Might not work in all cases.
    canonicalize_path() {
      # Keep a copy of the original path for error reporting.
      original="$1"

      previous=
      current="$1"

      while [ "$previous" != "$current" ]; do
        previous="$current"
        dirname="$(dirname "$current")"
        basename="$(basename "$current")"

        # If basename is ".", we're done. Discard it and "return" just dirname.
        if [ "$basename" = . ]; then
          echo "$dirname"

          return
        fi

        # If basename is "..", the only way to resolve it is to move it into
        # dirname.
        if [ "$basename" = ".." ]; then
          dirname="$dirname/.."
          basename="."
        fi

        cd -- "$dirname" || { >&2 echo "Couldn't cd to \"$dirname\"."; exit 127; }

        if [ -h "$basename" ]; then
          current="$(readlink "$basename")" || {
            >&2 echo "Couldn't resolve \"$dirname/$basename\" while canonicalizing \"$original\"."

            exit 127
          }
        else
          current="$(pwd)/$basename"
        fi
      done

      echo "$current"
    }

    script_dir="$(dirname "$(canonicalize_path "$0")")"

    # Extra variables needed by the awk scripts are set via a BEGIN block on the
    # command line rather than via command-line arguments because it's awkward at
    # best to pass multiple arguments through a single shell variable without
    # mangling the whitespace.
    awk_extra_init=

    case "$format" in
      default | --shell ) formatter="format-shell.awk";;

      --config | --config-no-header )
        formatter="format-gitconfig.awk"

        if [ "$format" = --config ]; then
          awk_extra_init="${awk_extra_init}print \"[alias]\";indent=\"\\t\";"
        fi
      ;;

      --json | --json-compact )
        formatter="format-json.awk"

        if [ "$format" = --json-compact ]; then
          awk_extra_init="${awk_extra_init}style=\"compact\";"
        else
          awk_extra_init="${awk_extra_init}style=\"pretty\";"
        fi
      ;;

      --names-only ) formatter="format-names.awk";;

      * ) >&2 echo "Invalid format \"$format\". How did you do that?"; exit 127;;
    esac

    if [ $# -gt 0 ]; then
      # Display only matching aliases.

      populate_names

      matching=

      add_match() {
        # Git doesn't allow alias names which contain characters which would
        # need escaped in a regex.

        if [ -z "$matching" ]; then
          matching="$1"
        else
          matching="$matching|$1"
        fi
      }

      while [ $# -gt 0 ]; do
        match_aliases "$1" add_match

        shift
      done

      if [ -n "$matching" ]; then
        case "$where" in
          --* ) aliases="$(git config "$where" --get-regexp "^alias\\.$matching\$")";;
          * ) aliases="$(git config --file "$where" --get-regexp "^alias\\.$matching\$")";;
        esac
      fi

      # No need to set `status` if nothing was matched; it will have already
      # been set by `match_aliases`.
    else
      # Alias name missing; display all aliases.

      case "$where" in
        --* ) aliases="$(git config "$where" --get-regexp ^alias\\.)";;
        * ) aliases="$(git config --file "$where" --get-regexp ^alias\\.)";;
      esac
    fi

    if [ -n "$aliases" ]; then
      echo "$aliases" | awk "BEGIN { $awk_extra_init } $(cat "$script_dir/parse-aliases.awk") $(cat "$script_dir/$formatter")"
    fi
  ;;

  * )
    if [ -z "$1" ]; then
      status=1
    elif [ "$1" != --help ] && [ "$1" != help ]; then
      >&2 echo "Unrecognized command '$1'."

      status=1
    fi

    case "$2" in
      "" ) show_help_and_exit;;

      add | remove | show )
        if [ -n "$3" ]; then
          >&2 echo "Unrecognized parameter '$3'."

          status=1
        fi

        show_help_and_exit "$2"
     ;;

      * )
        >&2 echo "Unrecognized command '$2'."
        status=1

        show_help_and_exit
      ;;
    esac
  ;;
esac

exit $status
