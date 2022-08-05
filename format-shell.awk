## Prints the supplied alias name and body as an invocation of `git alias`.
function handle(name, body) {
  print "git alias add " name " " quote(body)
}

## Turn any string into a shell-style single-quoted string.
function quote(string) {
  gsub(/'/, "'\\''", string)

  return "'" string "'"
}
