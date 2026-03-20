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
        if ch in ",+-*/=<>!():[]{}%&.":
            # Check for 2-char tokens
            if i + 1 < len(s):
                pair = ch + s[i+1]
                if pair == "/-":
                    # Single-line comment — discard everything from here onward
                    break
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
            if ch.isspace() or ch in ",+-*/=<>!():[]{}%&":
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


def _strip_comments(source: str) -> str:
    """Remove /- single-line and /-- ... --/ block comments from source."""
    out: list[str] = []
    i = 0
    in_block = False
    while i < len(source):
        # Check for block comment open: /--
        if not in_block and source[i:i+3] == "/--":
            in_block = True
            i += 3
            continue
        # Check for block comment close: --/
        if in_block and source[i:i+3] == "--/":
            in_block = False
            i += 3
            continue
        # Inside block comment: preserve newlines for line number accuracy
        if in_block:
            if source[i] == "\n":
                out.append("\n")
            i += 1
            continue
        # Check for single-line comment: /- or #
        if (source[i:i+2] == "/-") or (source[i] == "#"):
            skipped = 0
            # If it's "/-", we've consumed nothing yet by i, but we will skip from i.
            # Handle both cases: # (1 char) and /- (2 chars)
            while i < len(source) and source[i] != "\n":
                out.append(" ")
                i += 1
            continue
        out.append(source[i])
        i += 1
    return "".join(out)


def tokenize_program(source: str) -> list[LineTokens]:
    # Preliminary walk to handle multi-line brackets/parens
    raw_lines = _strip_comments(source).splitlines()
    final_lines: list[str] = []
    
    buf = ""
    target_line_no = 1
    depth = 0
    for idx, line in enumerate(raw_lines):
        if not buf:
            target_line_no = idx + 1
            
        # Count open vs close in THIS line
        line_depth_change = 0
        in_str = None
        for ch in line:
            if ch in "\"'" and (not in_str or in_str == ch):
                in_str = None if in_str else ch
            if not in_str:
                if ch in "([{": line_depth_change += 1
                elif ch in ")]}": line_depth_change -= 1
        
        if not buf:
            buf = line
        else:
            buf += " " + line.strip()
            
        depth += line_depth_change
        if depth <= 0:
            final_lines.append(buf)
            buf = ""
            depth = 0
            
    if buf:
        final_lines.append(buf)
        
    # We lose strict line numbers here if we just use idx + 1 
    # but for error reporting we really want the START of the block.
    # However, tokenize_line takes line_no. 
    # Let's just use the current index for now.
    return [tokenize_line(line, idx + 1) for idx, line in enumerate(final_lines)]
