#!/bin/sh

dry_run=
where=--global

while true; do
  case "$1" in
    --dry-run ) dry_run="[dry-run] ";;
    --global | --local ) where=$1;;
    -- ) shift; break;;
    *) break;;
  esac

  shift
done

if [ $# -eq 0 ]; then
  >&2 echo "Usage: git unalias [flags] <pattern>..."

  exit 1
fi

# This variable controls the script's exit code.
status=

## Unset any aliases which match the provided pattern.
##
## The parameter is the pattern to match against.
##
## Alias names are read from the global `name` variable and any which were not
## unset are stored back to it.
##
## If a pattern fails to match any remaining aliases, an error is printed and
## the script's exit code is set to 1.
unset_matching_aliases() {
  found=
  remaining=
  pattern="$1"

  # `$names` is deliberately unquoted so that its words (the names of the
  # aliases) can be spread into positional parameters.
  # shellcheck disable=2086
  set -- $names

  while [ $# -gt 0 ]; do
    # `$pattern` is deliberately unquoted so that it can act as a pattern.
    # shellcheck disable=2254
    case "$1" in
      $pattern )
        if [ -n "$dry_run" ] || git config "$where" --unset alias."$1";then
          echo "${dry_run}'unset $1'"

          found=1
        else
          >&2 echo "Failed to unset alias $1, which matched pattern '$pattern'."

          # Assume that a non-zero status from Git means the alias still
          # exists.
          remaining="$remaining $1"
        fi
      ;;

      * ) remaining="$remaining $1";;
    esac

    shift
  done

  if [ -z "$found" ]; then
    >&2 echo "${dry_run}No aliases matching \"$pattern\" were found."

    status=1
  fi

  names="$remaining"
}

# This variable stores the names of aliases which have been discovered, but not
# yet unset. It is updated by `unset_matching_aliases` to remove the names of
# any aliases which were unset. This allows us to prevent trying to unset the
# same alias multiple times if it matches multiple patterns without having to
# re-query `git config` after every iteration.
names="$(git config "$where" --get-regex ^alias\\. | awk '{ sub("alias.", "", $1); print $1 }')"

while [ $# -gt 0 ]; do
  unset_matching_aliases "$1"

  shift
done

exit $status
