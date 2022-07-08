# Finds all alias definitions in the output of `git config --get-regex alias\\.`
# and calls a function named `handle` (which must be provided by a separate
# script) with the name and body of each one. Multiline aliases are supported.

/alias\./ {
  if (name != "") {
    handle(name, body)
  }

  name = $1
  body = $0

  # When passing a string as the first argument to `sub`, it is interpreted as a
  # regular expression. Rather than trying to quote the dot always present in
  # `$1`, it is first removed from `name` and then an already-escaped string is
  # concatenated back in when removing the configuration name from `body`.
  sub("alias\\.", "", name)
  sub("alias\\." name " ", "", body)
}

!/alias\./ {
  body = body "\n" $0
}

END {
  if (name != "") {
    handle(name, body)
  }
}
