from __future__ import annotations


def str_length(s: str) -> int:
    return len(s)

def str_upper(s: str) -> str:
    return s.upper()

def str_lower(s: str) -> str:
    return s.lower()

def str_contains(s: str, sub: str) -> str:
    return "true" if sub in s else "false"

def str_starts_with(s: str, prefix: str) -> str:
    return "true" if s.startswith(prefix) else "false"

def str_ends_with(s: str, suffix: str) -> str:
    return "true" if s.endswith(suffix) else "false"

def str_trim(s: str) -> str:
    return s.strip()

def str_replace(s: str, old: str, new: str) -> str:
    return s.replace(old, new)

def str_split(s: str, sep: str = " ") -> list:
    return s.split(sep)

def str_index_of(s: str, sub: str) -> int:
    return s.find(sub)

def str_slice(s: str, start: str, end: str = "") -> str:
    a = int(float(start))
    if end == "":
        return s[a:]
    return s[a:int(float(end))]

def str_to_number(s: str) -> float:
    try:
        return int(s) if "." not in s else float(s)
    except ValueError:
        raise RuntimeError(f"Cannot convert '{s}' to a number.")

def str_repeat(s: str, times: str) -> str:
    return s * int(float(times))


FUNCTIONS: dict[str, tuple] = {
    "length":      (str_length,      ["s"]),
    "upper":       (str_upper,       ["s"]),
    "lower":       (str_lower,       ["s"]),
    "contains":    (str_contains,    ["s", "sub"]),
    "starts_with": (str_starts_with, ["s", "prefix"]),
    "ends_with":   (str_ends_with,   ["s", "suffix"]),
    "trim":        (str_trim,        ["s"]),
    "replace":     (str_replace,     ["s", "old", "new"]),
    "split":       (str_split,       ["s", "sep"]),
    "index_of":    (str_index_of,    ["s", "sub"]),
    "slice":       (str_slice,       ["s", "start", "end"]),
    "to_number":   (str_to_number,   ["s"]),
    "repeat":      (str_repeat,      ["s", "times"]),
}
