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
## is set to exactly "compact", no optional whitespace before or after elements
# will be emitted. Any other value will be treated as "pretty", and produce more
# human-friendly output.
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
  gsub(/\001/, "\\u0001", string)
  gsub(/\002/, "\\u0002", string)
  gsub(/\003/, "\\u0003", string)
  gsub(/\004/, "\\u0004", string)
  gsub(/\005/, "\\u0005", string)
  gsub(/\006/, "\\u0006", string)
  gsub(/\007/, "\\u0007", string)
  gsub(/\b/, "\\b", string)
  gsub(/\t/, "\\t", string)
  gsub(/\n/, "\\n", string)
  gsub(/\013/, "\\u000b", string)
  gsub(/\f/, "\\f", string)
  gsub(/\r/, "\\r", string)
  gsub(/\016/, "\\u000e", string)
  gsub(/\017/, "\\u000f", string)
  gsub(/\020/, "\\u0010", string)
  gsub(/\021/, "\\u0011", string)
  gsub(/\022/, "\\u0012", string)
  gsub(/\023/, "\\u0013", string)
  gsub(/\024/, "\\u0014", string)
  gsub(/\025/, "\\u0015", string)
  gsub(/\026/, "\\u0016", string)
  gsub(/\027/, "\\u0017", string)
  gsub(/\030/, "\\u0018", string)
  gsub(/\031/, "\\u0019", string)
  gsub(/\032/, "\\u001a", string)
  gsub(/\033/, "\\u001b", string)
  gsub(/\034/, "\\u001c", string)
  gsub(/\035/, "\\u001d", string)
  gsub(/\036/, "\\u001e", string)
  gsub(/\037/, "\\u001f", string)

  return "\"" string "\""
}
