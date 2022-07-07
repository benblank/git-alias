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

  # This is a gawk function which wraps a string in single quotes, handling
  # single quotes within the string if necessary.
  quote_function='
    function quote(string,   single, quotedsingle, idx, parts, count, result) {
      if (string == "")
        return "\"\""

      single = "\x27"
      quotedsingle = "\"\x27\""
      count = split(string, parts, single)

      result = single parts[1] single

      for (idx = 2; idx <= count; idx++)
        result = result quotedsingle single parts[idx] single

      return result
    }
  '

  if [ -n "$1" ]; then
    # Display only the named alias.

    alias="$(git config --global --get alias."$1")"

    if [ -n "$alias" ]; then
      echo "$alias" | gawk "$quote_function { print \"git alias $1 \" quote(\$0) }"
    else
      >&2 echo "No alias named \"$1\" exists."

      exit 1
    fi
  else
    # Alias name missing; display all aliases.

    git config --global --get-regex alias\\. | gawk "$quote_function match(\$0, /^alias\.(\w+) (.+)/, parts) { print \"git alias \" parts[1] \" \" quote(parts[2]) }"
  fi
fi
