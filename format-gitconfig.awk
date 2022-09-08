## Prints the supplied alias name and body as lines for a Git configuration
## file. The desired indent, if any, must be supplied.
function handle(name, body) {
  print indent name " = " quote(body)
}

## Turn any string into a gitconfig-style double-quoted string.
function quote(string) {
  # Values only need surrounded by quotes if they have leading/trailing
  # whitespace (which is otherwise stripped) or characters which would start a
  # comment. This appears to be how Git decides whether to quote a value.
  surrounding_quotes = string ~ /^\s|\s$|[#;]/ ? "\"" : ""

  gsub(/\\/, "\\\\", string)
  gsub(/\b/, "\\b", string)
  gsub(/\n/, "\\n", string)
  gsub(/\t/, "\\t", string)
  gsub(/"/, "\\\"", string)

  return surrounding_quotes string surrounding_quotes
}
