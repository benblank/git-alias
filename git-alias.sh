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
    --compact )
      if beginswith json- "$format"; then
        format=json-compact
      else
        >&2 echo "The --compact flag may only be used after --json."

        exit 1
      fi
    ;;

    --config ) format=config-header;;
    --default-file ) where=default;;
    --file ) where="--file $2"; shift;;
    --global | --local | --system | --worktree ) where=$1;;

    --header )
      if beginswith config- "$format"; then
        format=config-header
      else
        >&2 echo "The --header flag may only be used after --config."

        exit 1
      fi
    ;;

    --json ) format=json-pretty;;

    --no-header )
      if beginswith config- "$format"; then
        format=config-no-header
      else
        >&2 echo "The --no-header flag may only be used after --config."

        exit 1
      fi
    ;;

    --pretty )
      if beginswith json- "$format"; then
        format=json-pretty
      else
        >&2 echo "The --pretty flag may only be used after --json."

        exit 1
      fi
    ;;

    --shell ) format=shell;;
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

  case "$format" in
    default | shell )
      # Produce output suitable for use in/as a shell script.

      if [ $# -gt 0 ]; then
        # Display only the named alias.

        # `$where` is deliberately unquoted here, as it may contain multiple
        # parameters.
        #
        # shellcheck disable=2086
        alias="$(git config $where --get alias."$1")"

        if [ -n "$alias" ]; then
          echo "$alias" | awk -v name="$1" -f "$script_dir/read-all.awk" -f "$script_dir/handle-shell.awk"
        else
          >&2 echo "No alias named \"$1\" exists."

          exit 1
        fi
      else
        # Alias name missing; display all aliases.

        # `$where` is deliberately unquoted here, as it may contain multiple
        # parameters.
        #
        # shellcheck disable=2086
        git config $where --get-regex ^alias\\. | awk -f "$script_dir/read-aliases.awk" -f "$script_dir/handle-shell.awk"
      fi
    ;;

    config-header | config-no-header )
      # Produce output suitable for use in/as a Git configuration file.

      if [ "$format" = config-header ]; then
        echo "[alias]"

        indent="	"  # <- tab character
      else
        indent=
      fi

      if [ $# -gt 0 ]; then
        # Display only the named alias.

        # `$where` is deliberately unquoted here, as it may contain multiple
        # parameters.
        #
        # shellcheck disable=2086
        alias="$(git config $where --get alias."$1")"

        if [ -n "$alias" ]; then
          echo "$alias" | awk -v name="$1" -v indent="$indent" -f "$script_dir/read-all.awk" -f "$script_dir/handle-gitconfig.awk"
        else
          >&2 echo "No alias named \"$1\" exists."

          exit 1
        fi
      else
        # Alias name missing; display all aliases.

        # `$where` is deliberately unquoted here, as it may contain multiple
        # parameters.
        #
        # shellcheck disable=2086
        git config $where --get-regex ^alias\\. | awk -v indent="$indent" -f "$script_dir/read-aliases.awk" -f "$script_dir/handle-gitconfig.awk"
      fi
    ;;

    json-compact | json-pretty )
      # Produce JSON output.

      if [ "$format" = json-compact ]; then
        style=compact
      else
        style=pretty
      fi

      if [ $# -gt 0 ]; then
        # Display only the named alias.

        # `$where` is deliberately unquoted here, as it may contain multiple
        # parameters.
        #
        # shellcheck disable=2086
        alias="$(git config $where --get alias."$1")"

        if [ -n "$alias" ]; then
          echo "$alias" | awk -v name="$1" -v style="$style" -f "$script_dir/read-all.awk" -f "$script_dir/handle-json.awk"
        else
          >&2 echo "No alias named \"$1\" exists."

          exit 1
        fi
      else
        # Alias name missing; display all aliases.

        # `$where` is deliberately unquoted here, as it may contain multiple
        # parameters.
        #
        # shellcheck disable=2086
        git config $where --get-regex ^alias\\. | awk -v style="$style" -f "$script_dir/read-aliases.awk" -f "$script_dir/handle-json.awk"
      fi
    ;;

    * ) >&2 echo "Invalid format \"$format\". How did you do that?"; exit 1;;
  esac
fi
