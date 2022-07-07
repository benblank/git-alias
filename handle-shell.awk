## Prints the supplied alias name and body as an invokation of `git alias`.
function handle(name, body) {
  print "git alias " name " " quote(body)
}

## Turn any string into a shell-style single-quoted string.
function quote(string,   single, quotedsingle, idx, parts, count, result) {
  if (string == "")
    return "\"\""

  single = "'"
  quotedsingle = "\"'\""
  count = split(string, parts, single)

  result = single parts[1] single

  for (idx = 2; idx <= count; idx++)
    result = result quotedsingle single parts[idx] single

  return result
}
