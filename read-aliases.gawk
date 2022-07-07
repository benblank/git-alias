# Finds all alias definitions in the output of `git config --get-regex alias\\.`
# and calls a function named `handle` (which must be provided by a separate
# script) with the name and body of each one. Multiline aliases are supported.

match($0, /^alias\.(\w+) (.+)/, parts) {
  if (name != "") {
    handle(name, body)
  }

  name = parts[1]
  body = parts[2]
}

!/alias\./ {
  body = body "\n" $0
}

END {
  if (name != "") {
    handle(name, body)
  }
}
