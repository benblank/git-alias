## Prints the supplied alias name and body as lines for a Git configuration
## file. The desired indent, if any, must be supplied.
function handle(name, body) {
  print indent name " = " quote(body)
}

## Turn any string into a gitconfig-style double-quoted string.
function quote(string) {
  gsub(/\\/, "\\\\", string)
  gsub(/\n/, "\\n", string)
  gsub(/"/, "\\\"", string)

  return "\"" string "\""
}
