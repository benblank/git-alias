#!/bin/sh

where=--global

while true; do
  case "$1" in
    --global | --local ) where=$1;;
    -- ) shift; break;;
    *) break;;
  esac

  shift
done

if [ -n "$1" ]; then
  # TODO: wildcards?

  if ! git config "$where" --unset alias."$1"; then
      >&2 echo "No alias named \"$1\" exists."

      exit 1
  fi
else
  >&2 echo "Usage: git unalias {alias-name}"

  exit 1
fi
