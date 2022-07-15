BEGIN {
  printf "{"

  is_first = 1
}

## Stores the supplied alias name and body as an array index and element, to be
## processed by the END block just below it. It also tracks the size of the
## array in `alias_count`.
function handle(name, body) {
  if (is_first) {
    is_first = 0
  } else {
    printf ","
  }

  if (is_pretty()) printf "\n  "

  # Git doesn't allow configuration keys to contain any characters which must
  # be escaped in JSON strings, so there's no point in feeding them to
  # `quote()`.
  printf "\"" name "\":"

  if (is_pretty()) printf " "

  printf quote(body)
}

## Determines whether to pretty-print the JSON output. If the variable `style`
## is provided on the command line and set to exactly "compact", no whitespace
## before or after elements will be emitted. Any other value will be treated as
## "pretty", and produce more human-friendly output.
function is_pretty() {
  return style != "compact"
}

END {
  if (is_pretty() && !is_first) {
    printf "\n"
  }

  printf "}"

  if (is_pretty()) {
    printf "\n"
  }
}

## Turn any string into a valid JSON double-quoted string.
function quote(string) {
  gsub(/\\/, "\\\\", string)
  gsub(/"/, "\\\"", string)

  # I'm sure there's a smarter way to do this, but I spent two hours getting
  # more and more annoyed at awk while trying to figure it out before giving up
  # and doing it the easy way.
  gsub(/\x00/, "\\u0000", string)
  gsub(/\x01/, "\\u0001", string)
  gsub(/\x02/, "\\u0002", string)
  gsub(/\x03/, "\\u0003", string)
  gsub(/\x04/, "\\u0004", string)
  gsub(/\x05/, "\\u0005", string)
  gsub(/\x06/, "\\u0006", string)
  gsub(/\x07/, "\\u0007", string)
  gsub(/\b/, "\\b", string)
  gsub(/\t/, "\\t", string)
  gsub(/\n/, "\\n", string)
  gsub(/\x0b/, "\\u000b", string)
  gsub(/\f/, "\\f", string)
  gsub(/\r/, "\\r", string)
  gsub(/\x0e/, "\\u000e", string)
  gsub(/\x0f/, "\\u000f", string)
  gsub(/\x10/, "\\u0010", string)
  gsub(/\x11/, "\\u0011", string)
  gsub(/\x12/, "\\u0012", string)
  gsub(/\x13/, "\\u0013", string)
  gsub(/\x14/, "\\u0014", string)
  gsub(/\x15/, "\\u0015", string)
  gsub(/\x16/, "\\u0016", string)
  gsub(/\x17/, "\\u0017", string)
  gsub(/\x18/, "\\u0018", string)
  gsub(/\x19/, "\\u0019", string)
  gsub(/\x1a/, "\\u001a", string)
  gsub(/\x1b/, "\\u001b", string)
  gsub(/\x1c/, "\\u001c", string)
  gsub(/\x1d/, "\\u001d", string)
  gsub(/\x1e/, "\\u001e", string)
  gsub(/\x1f/, "\\u001f", string)

  return "\"" string "\""
}
