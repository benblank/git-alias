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

  # This is an awk function which wraps a string in single quotes, handling
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

    # This is an awk script which accumulates all lines of input into a single
    # variable, quotes it, and prints it as the body of an invokation of the
    # `git alias` command. The alias name must be privided via the `name`
    # variable. The `$0`s in it refer to the awk variable, not the shell
    # variable.
    # shellcheck disable=2016
    accumulate_script='
      {
        if (body == "") {
          body = $0
        } else {
          body = body "\n" $0
        }
      }

      END {
        print "git alias " name " " quote(body)
      }
    '

    alias="$(git config --global --get alias."$1")"

    if [ -n "$alias" ]; then
      echo "$alias" | awk -v name="$1" "$quote_function $accumulate_script"
    else
      >&2 echo "No alias named \"$1\" exists."

      exit 1
    fi
  else
    # Alias name missing; display all aliases.

    # This is a gawk script which accumulates the bodies of aliases into single
    # strings, quotes them, and prints them as invokations of the `git alias`
    # command. The `$0`s in it refer to the awk variable, not the shell
    # variable.
    # shellcheck disable=2016
    aliases_script='
      match($0, /^alias\.(\w+) (.+)/, parts) {
        if (name != "") {
          print "git alias " name " " quote(body)
        }

        name = parts[1]
        body = parts[2]
      }

      !/alias\./ {
        body = body "\n" $0
      }

      END {
        if (name != "") {
          print "git alias " name " " quote(body)
        }
      }
    '

    git config --global --get-regex alias\\. | gawk "$quote_function $aliases_script"
  fi
fi
