from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LineTokens:
    indent: int
    raw: str
    tokens: list[str]


def _count_indent(line: str) -> tuple[int, str]:
    if not line:
        return 0, line
    i = 0
    indent = 0
    while i < len(line):
        ch = line[i]
        if ch == " ":
            indent += 1
            i += 1
        elif ch == "\t":
            indent += 4
            i += 1
        else:
            break
    return indent, line[i:]


def tokenize_line(line: str) -> LineTokens:
    raw_line = line.rstrip("\r\n")
    indent, rest = _count_indent(raw_line)
    rest_stripped = rest.strip()
    if not rest_stripped:
        return LineTokens(indent=indent, raw=raw_line, tokens=[])

    # Split by spaces; keep commas as separator tokens; keep periods only as terminators
    # (removed from tokens).
    # Verba's only allowed symbols are comma and period, so we treat any other punctuation
    # as plain characters inside tokens (but programs should not use them).
    s = rest_stripped
    if s.endswith("."):
        s = s[:-1].rstrip()

    parts: list[str] = []
    buf: list[str] = []
    in_string = False
    string_char = ""
    for ch in s:
        if in_string:
            buf.append(ch)
            if ch == string_char:
                parts.append("".join(buf))
                buf = []
                in_string = False
            continue

        if ch in "\"'":
            if buf:
                parts.append("".join(buf))
                buf = []
            in_string = True
            string_char = ch
            buf.append(ch)
            continue

        if ch == " ":
            if buf:
                parts.append("".join(buf))
                buf = []
            continue
        if ch in ",+-*/=<>!():[]":
            if buf:
                parts.append("".join(buf))
                buf = []
            parts.append(ch)
            continue
        buf.append(ch)
    if buf:
        parts.append("".join(buf))

    # Recombine obvious 2-char tokens (+=, -=, ==, !=, <=, >=, *=, /=)
    final_parts: list[str] = []
    i = 0
    while i < len(parts):
        if i + 1 < len(parts):
            pair = parts[i] + parts[i+1]
            if pair in ["+=", "-=", "*=", "/=", "==", "!=", "<=", ">="]:
                final_parts.append(pair)
                i += 2
                continue
        final_parts.append(parts[i])
        i += 1
            
    # Preserve original spelling (including case). The parser does case-insensitive
    # keyword matching.
    return LineTokens(indent=indent, raw=raw_line, tokens=final_parts)


def tokenize_program(source: str) -> list[LineTokens]:
    return [tokenize_line(line) for line in source.splitlines()]
