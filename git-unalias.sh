#!/bin/sh

if [ -n "$1" ]; then
  # TODO: wildcards?

  if ! git config --global --unset alias."$1"; then
      >&2 echo "No alias named \"$1\" exists."

      exit 1
  fi
else
  >&2 echo "Usage: git unalias {alias-name}"

  exit 1
fi
