# Gathers all input into a single string and feeds it to a function named
# `handle` (which must be provided by a separate script), along with the
# variable `name`.

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
