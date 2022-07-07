#!/bin/sh

beginswith() {
  case "$2" in
    "$1"* ) return 0;;
  esac

  return 1
}

format=default
where=--global

while true; do
  case "$1" in
    --config ) format=config-header;;
    --global | --local ) where=$1;;

    --header )
      if beginswith config- "$format"; then
        format=config-header
      else
        >&2 echo "The --header flag may only be used after --config."

        exit 1
      fi
    ;;

    --no-header )
      if beginswith config- "$format"; then
        format=config-no-header
      else
        >&2 echo "The --no-header flag may only be used after --config."

        exit 1
      fi
    ;;

    --shell ) format=shell;;
    -- ) shift; break;;
    *) break;;
  esac

  shift
done

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
  git config $where alias."$name" "$*"
else
  # Alias definition missing; display alias(es) instead.

  script_dir="$(dirname "$(readlink "$0")")"

  case "$format" in
    default | shell )
      # Produce output suitable for use in/as a shell script.

      if [ $# -gt 0 ]; then
        # Display only the named alias.

        alias="$(git config $where --get alias."$1")"

        if [ -n "$alias" ]; then
          echo "$alias" | awk -v name="$1" -f "$script_dir/read-all.awk" -f "$script_dir/handle-shell.awk"
        else
          >&2 echo "No alias named \"$1\" exists."

          exit 1
        fi
      else
        # Alias name missing; display all aliases.

        git config $where --get-regex alias\\. | gawk -f "$script_dir/read-aliases.gawk" -f "$script_dir/handle-shell.awk"
      fi
    ;;

    config-header | config-no-header )
      # Produce output suitable for use in/as a Git configuration file.

      if [ "$format" = config-header ]; then
        echo "[alias]"

        indent="	"  # <- tab character
      fi

      if [ $# -gt 0 ]; then
        # Display only the named alias.

        alias="$(git config $where --get alias."$1")"

        if [ -n "$alias" ]; then
          echo "$alias" | awk -v name="$1" -v indent="$indent" -f "$script_dir/read-all.awk" -f "$script_dir/handle-gitconfig.awk"
        else
          >&2 echo "No alias named \"$1\" exists."

          exit 1
        fi
      else
        # Alias name missing; display all aliases.

        git config $where --get-regex alias\\. | gawk -v indent="$indent" -f "$script_dir/read-aliases.gawk" -f "$script_dir/handle-gitconfig.awk"
      fi
    ;;

    * ) >&2 echo "Invalid format \"$format\". How did you do that?"; exit 1;;
  esac
fi
