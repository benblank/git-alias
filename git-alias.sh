#!/bin/sh

beginswith() {
  case "$2" in
    "$1"* ) return 0;;
  esac

  return 1
}

format=default
where=default

while true; do
  case "$1" in
    --config | --config-no-header | --json | --json-compact | --shell ) format=$1;;
    --file ) where="--file $2"; shift;;
    --global | --local | --system | --worktree ) where=$1;;
    -- ) shift; break;;
    *) break;;
  esac

  shift
done

# Convert the default file location into a valid command-line flag for Git. If a
# flag or custom file is configured, use that. Otherwise, fall back to the
# global file.
if [ "$where" = default ]; then
  configured_location="$(git config --get git-alias.config-file)"

  case "$configured_location" in
    "" ) where=--global;;
    "--file "* | --global | --local | --system | --worktree ) where="$configured_location";;
    * ) where="--file $configured_location"
  esac
fi

if [ $# -gt 1 ]; then
  # Define an alias.

  if [ "$format" != default ]; then
    >&2 echo "Format flags have no meaning when creating an alias."
  fi

  name="$1"
  shift

  # Using "$*" here allows commands like `git alias cdiff diff --cached` to work
  # as expected by combining all the arguments after the alias name into a
  # single string.
  #
  # `$where` is deliberately unquoted here, as it may contain multiple
  # parameters.
  #
  # shellcheck disable=2086
  git config $where alias."$name" "$*"
else
  # Alias definition missing; display alias(es) instead.


  # I can't believe there's no *actually* portable way to do this other than to
  # implement (hack) it yourself. Might not work in all cases.
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

      cd -- "$dirname" || abort "Couldn't cd to \"$dirname\"."

      if [ -h "$basename" ]; then
        current="$(readlink "$basename" || abort "Couldn't resolve \"$dirname/$basename\" while canonicalizing \"$original\".")"
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

    * ) >&2 echo "Invalid format \"$format\". How did you do that?"; exit 1;;
  esac

  if [ $# -gt 0 ]; then
    # Display only the named alias.

    # `$where` is deliberately unquoted here, as it may contain multiple
    # parameters.
    #
    # shellcheck disable=2086
    aliases="$(git config $where --get-regexp "^alias\\.$1\$")"

    if [ -z "$aliases" ]; then
      >&2 echo "No alias named \"$1\" exists."

      exit 1
    fi
  else
    # Alias name missing; display all aliases.

    # `$where` is deliberately unquoted here, as it may contain multiple
    # parameters.
    #
    # shellcheck disable=2086
    aliases="$(git config $where --get-regexp ^alias\\.)"
  fi

  echo "$aliases" | awk "BEGIN { $awk_extra_init } $(cat "$script_dir/parse-aliases.awk") $(cat "$script_dir/$formatter")"
fi
