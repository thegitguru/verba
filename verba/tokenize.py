from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Token:
    value: str
    line_no: int
    col: int
    raw_line: str


@dataclass(frozen=True)
class LineTokens:
    indent: int
    raw: str
    tokens: List[Token]


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


def tokenize_line(line: str, line_no: int) -> LineTokens:
    raw_line = line.rstrip("\r\n")
    indent, rest = _count_indent(raw_line)
    
    # Calculate column offset from indent
    # Note: _count_indent returns the rest of the line, but we need the actual physical 
    # position for column reporting.
    current_col = len(raw_line) - len(rest)
    
    s = rest
    tokens: List[Token] = []
    
    i = 0
    while i < len(s):
        ch = s[i]
        
        # Skip spaces but keep track of column
        if ch == " ":
            i += 1
            continue
            
        start_col = current_col + i
        
        # Handle strings
        if ch in "\"'":
            quote = ch
            buf = [ch]
            start_i = i
            i += 1
            while i < len(s) and s[i] != quote:
                buf.append(s[i])
                i += 1
            if i < len(s):
                buf.append(quote)
                i += 1
            tokens.append(Token("".join(buf), line_no, start_col, raw_line))
            continue
            
        # Handle symbols
        if ch in ",+-*/=<>!():[].":
            # Check for 2-char tokens
            if i + 1 < len(s):
                pair = ch + s[i+1]
                if pair in ["+=", "-=", "*=", "/=", "==", "!=", "<=", ">="]:
                    tokens.append(Token(pair, line_no, start_col, raw_line))
                    i += 2
                    continue
            tokens.append(Token(ch, line_no, start_col, raw_line))
            i += 1
            continue
            
        # Handle words/numbers
        buf = []
        while i < len(s):
            ch = s[i]
            if ch.isspace() or ch in ",+-*/=<>!():[]":
                break
            if ch == ".":
                # Split at dot ONLY if it is at the end of the line or followed by a space
                if i + 1 >= len(s) or s[i+1].isspace():
                    break
            buf.append(ch)
            i += 1
        if buf:
            tokens.append(Token("".join(buf), line_no, start_col, raw_line))
            
    return LineTokens(indent=indent, raw=raw_line, tokens=tokens)


def tokenize_program(source: str) -> list[LineTokens]:
    lines = source.splitlines()
    return [tokenize_line(line, idx + 1) for idx, line in enumerate(lines)]
