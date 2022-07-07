# Gathers all input into a single string and feeds it to a function named
# `handle` (which must be provided by a separate script), along with the
# variable `name` (which must be provided on the command line).

{
  if (body == "") {
    body = $0
  } else {
    body = body "\n" $0
  }
}

END {
  handle(name, body)
}
