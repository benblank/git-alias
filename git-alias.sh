#!/bin/sh

if [ -n "$2" ]; then
  # Define an alias.

  name="$1"
  shift

  # Using "$*" here allows commands like `git alias cdiff diff --cached` to work
  # as expected by combining all the arguments after the alias name into a
  # single string.
  git config --global alias."$name" "$*"
else
  # Alias definition missing; display alias(es) instead.

  script_dir="$(dirname "$(readlink "$0")")"

  if [ -n "$1" ]; then
    # Display only the named alias.

    alias="$(git config --global --get alias."$1")"

    if [ -n "$alias" ]; then
      echo "$alias" | awk -v name="$1" -f "$script_dir/read-all.awk" -f "$script_dir/handle-shell.awk"
    else
      >&2 echo "No alias named \"$1\" exists."

      exit 1
    fi
  else
    # Alias name missing; display all aliases.

    git config --global --get-regex alias\\. | gawk -f "$script_dir/read-aliases.gawk" -f "$script_dir/handle-shell.awk"
  fi
fi
