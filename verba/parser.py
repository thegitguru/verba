from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .ast import (
    Ask,
    BinaryOp,
    BoolAnd,
    BoolExpr,
    BoolNot,
    BoolOr,
    Compare,
    Define,
    Decrease,
    ForEach,
    GiveBack,
    If,
    Increase,
    Let,
    LetResultOfRun,
    Literal,
    ListAdd,
    ListItemGet,
    ListRemove,
    LoadFile,
    Note,
    Repeat,
    Run,
    SaveToFile,
    Say,
    SetVar,
    Span,
    Stmt,
    VarRef,
    While,
    TryBlock,
    Import,
    AppendToFile,
    DeleteFile,
    FetchUrl,
    FreeVar,
    ClassDef,
    ObjectNew,
    ObjectPropGet,
    ObjectPropSet,
    MethodCall,
    LetResultOfMethod,
    AsyncDefine,
    AsyncRun,
    AwaitStmt,
)
from .errors import VerbaParseError
from .tokenize import LineTokens, tokenize_program


def _lc(tokens: list[str]) -> list[str]:
    return [t.lower() for t in tokens]


def _require_period(line: LineTokens, line_no: int) -> None:
    if not line.raw.strip().endswith(".") and not line.raw.strip().endswith(":"):
        raise VerbaParseError(
            "Every statement must end with a period (or a colon for block starters).",
            line_no=line_no,
            line=line.raw,
        )


def _join_name(words: list[str]) -> str:
    # Variable/function names are stored as normalized lowercase words joined by spaces.
    return " ".join([w.lower() for w in words]).strip()


_COMPARISONS: list[tuple[list[str], str]] = [
    (["is", "not"], "!="),
    (["does", "not", "equal"], "!="),
    (["!", "="], "!="),
    (["!="], "!="),
    (["<", ">"], "!="),
    (["is", "greater", "than"], ">"),
    (["is", "more", "than"], ">"),
    ([">"], ">"),
    (["is", "less", "than"], "<"),
    (["is", "fewer", "than"], "<"),
    (["<"], "<"),
    (["is", "at", "least"], ">="),
    ([">", "="], ">="),
    ([">="], ">="),
    (["is", "at", "most"], "<="),
    (["<", "="], "<="),
    (["<="], "<="),
    (["equals"], "=="),
    (["is"], "=="),
    (["=", "="], "=="),
    (["=="], "=="),
    (["="], "=="),
]


_MATH_OPS: list[tuple[list[str], str]] = [
    (["plus"], "+"),
    (["+"], "+"),
    (["minus"], "-"),
    (["-"], "-"),
    (["times"], "*"),
    (["*"], "*"),
    (["divided", "by"], "/"),
    (["/"], "/"),
    (["remainder", "after", "dividing", "by"], "%"),
]


def _try_match(tokens_lc: list[str], i: int, phrase: list[str]) -> bool:
    return tokens_lc[i : i + len(phrase)] == phrase


def _parse_number(tok: str) -> Optional[int | float]:
    # Accept integers and simple floats.
    try:
        if "." in tok:
            return float(tok)
        return int(tok)
    except ValueError:
        return None


def _parse_atom(tokens: list[str], tokens_lc: list[str], i: int, *, span: Span) -> tuple[object, int]:
    tok = tokens[i]
    tl = tokens_lc[i]

    if tl == "true":
        return Literal(span, True), i + 1
    if tl == "false":
        return Literal(span, False), i + 1

    num = _parse_number(tok)
    if num is not None:
        return Literal(span, num), i + 1

    if (tok.startswith('"') and tok.endswith('"')) or (tok.startswith("'") and tok.endswith("'")):
        return Literal(span, tok[1:-1]), i + 1
        
    if "." in tok and tok.count(".") == 1:
        idx = tok.index(".")
        if idx > 0 and idx < len(tok) - 1:
            return ObjectPropGet(span, tok[:idx].lower(), tok[idx+1:].lower()), i + 1

    # Word literals are bare single tokens (e.g. hello, Alice). Multi-word text uses "quote".
    return VarRef(span, _join_name([tok])), i + 1


def _scan_math_op(tokens_lc: list[str], i: int) -> tuple[Optional[str], int]:
    for phrase, op in _MATH_OPS:
        if _try_match(tokens_lc, i, phrase):
            return op, i + len(phrase)
    return None, i


def _precedence(op: str) -> int:
    return {"*": 2, "/": 2, "%": 2, "+": 1, "-": 1}.get(op, 0)


def parse_expr(tokens: list[str], *, line_no: int) -> object:
    if not tokens:
        raise VerbaParseError("I expected a value here.", line_no=line_no)
    span = Span(line_no)
    tokens_lc = _lc(tokens)

    if tokens_lc[0] == "new":
        if "with" in tokens_lc:
            with_i = tokens_lc.index("with")
            class_name = _join_name(tokens[1:with_i])
            args = [parse_expr(a, line_no=line_no) for a in _split_by_commas(tokens[with_i + 1 :])]
            return ObjectNew(span, class_name, args)
        class_name = _join_name(tokens[1:])
        return ObjectNew(span, class_name, [])

    # "quote ..." -> literal string (rest of tokens joined with spaces)
    if tokens_lc[0] == "quote":
        text = " ".join(tokens[1:]).strip()
        return Literal(span, text)

    # Multi-word variable names (e.g. "user age") are allowed. If there are no math
    # operator words present, treat the whole phrase as a single variable reference.
    if len(tokens) > 1 and not any(t in ["plus", "minus", "times", "divided", "remainder", "+", "-", "*", "/"] for t in tokens_lc):
        return VarRef(span, _join_name(tokens))

    # Shunting-yard to support precedence and multi-word operators.
    out: list[object] = []
    ops: list[str] = []

    i = 0
    expecting_value = True
    while i < len(tokens):
        if expecting_value:
            atom, i = _parse_atom(tokens, tokens_lc, i, span=span)
            out.append(atom)
            expecting_value = False
            continue

        op, next_i = _scan_math_op(tokens_lc, i)
        if op is None:
            # If there's no operator, this is an error for expressions; caller can choose to
            # treat it differently, but by default we fail loudly.
            raise VerbaParseError("I did not understand this math expression.", line_no=line_no)

        while ops and _precedence(ops[-1]) >= _precedence(op):
            out.append(ops.pop())
        ops.append(op)
        i = next_i
        expecting_value = True

    if expecting_value:
        raise VerbaParseError("I expected a value after the math operator.", line_no=line_no)

    while ops:
        out.append(ops.pop())

    # Build AST from RPN.
    stack: list[object] = []
    for item in out:
        if isinstance(item, str):
            if len(stack) < 2:
                raise VerbaParseError("I did not understand this math expression.", line_no=line_no)
            right = stack.pop()
            left = stack.pop()
            stack.append(BinaryOp(span, item, left, right))
        else:
            stack.append(item)
    if len(stack) != 1:
        raise VerbaParseError("I did not understand this math expression.", line_no=line_no)
    return stack[0]


def _scan_comparison(tokens_lc: list[str], i: int) -> tuple[Optional[str], int]:
    for phrase, op in _COMPARISONS:
        if _try_match(tokens_lc, i, phrase):
            return op, i + len(phrase)
    return None, i


def parse_condition(tokens: list[str], *, line_no: int) -> BoolExpr:
    if not tokens:
        raise VerbaParseError("I expected a condition here.", line_no=line_no)
    tokens_lc = _lc(tokens)
    span = Span(line_no)

    # Parse OR with lower precedence than AND. Support leading "not".
    def parse_term(j: int) -> tuple[BoolExpr, int]:
        if j < len(tokens_lc) and tokens_lc[j] == "not":
            inner, k = parse_term(j + 1)
            return BoolNot(span, inner), k

        # Compare: <expr> <comparison> <expr>
        # The right-hand side stops at the next 'and'/'or' token (if any).
        for k in range(j + 1, len(tokens_lc)):
            op, next_k = _scan_comparison(tokens_lc, k)
            if op is None:
                continue
            left_tokens = tokens[j:k]
            if not left_tokens:
                break

            end = len(tokens_lc)
            for m in range(next_k + 1, len(tokens_lc)):
                if tokens_lc[m] in ["and", "or"]:
                    end = m
                    break
            right_tokens = tokens[next_k:end]
            if not right_tokens:
                break

            left = parse_expr(left_tokens, line_no=line_no)
            right = parse_expr(right_tokens, line_no=line_no)
            return Compare(span, op, left, right), end

        raise VerbaParseError(
            "I did not understand this condition. Try 'if age is greater than 18, do the following.'",
            line_no=line_no,
        )

    def parse_and(j: int) -> tuple[BoolExpr, int]:
        left, k = parse_term(j)
        while k < len(tokens_lc) and tokens_lc[k] == "and":
            right, k2 = parse_term(k + 1)
            left = BoolAnd(span, left, right)
            k = k2
        return left, k

    def parse_or(j: int) -> tuple[BoolExpr, int]:
        left, k = parse_and(j)
        while k < len(tokens_lc) and tokens_lc[k] == "or":
            right, k2 = parse_and(k + 1)
            left = BoolOr(span, left, right)
            k = k2
        return left, k

    expr, end = parse_or(0)
    if end != len(tokens_lc):
        raise VerbaParseError("I did not understand the full condition.", line_no=line_no)
    return expr


@dataclass
class _Cursor:
    lines: list[LineTokens]
    i: int = 0


def parse(source: str) -> list[Stmt]:
    return parse_lines(tokenize_program(source))


def parse_lines(lines: list[LineTokens]) -> list[Stmt]:
    cur = _Cursor(lines=lines, i=0)
    return _parse_block(cur, expected_indent=0)


def _parse_block(cur: _Cursor, *, expected_indent: int) -> list[Stmt]:
    out: list[Stmt] = []
    while cur.i < len(cur.lines):
        lt = cur.lines[cur.i]
        line_no = cur.i + 1

        if not lt.tokens:
            cur.i += 1
            continue

        if lt.indent < expected_indent:
            break
        if lt.indent > expected_indent:
            raise VerbaParseError(
                "This line is indented more than expected. Check your block indentation.",
                line_no=line_no,
                line=lt.raw,
            )

        stmt = _parse_statement(cur, expected_indent=expected_indent)
        if stmt is not None:
            out.append(stmt)
    return out


def _parse_statement(cur: _Cursor, *, expected_indent: int) -> Optional[Stmt]:
    lt = cur.lines[cur.i]
    line_no = cur.i + 1
    tokens = lt.tokens
    tokens_lc = _lc(tokens)
    span = Span(line_no)

    # Comments / notes
    if tokens_lc[0] == "note":
        cur.i += 1
        return Note(span, " ".join(tokens[1:]))

    # Block endings
    if tokens_lc[0] == "end":
        _require_period(lt, line_no)
        # Any "end" can end any block (like standard end.)
        raise VerbaParseError(
            "I found an 'end' without a matching block to end.", line_no=line_no, line=lt.raw
        )

    # let ... be ...
    if tokens_lc[0] == "let":
        _require_period(lt, line_no)

        # Special: let <name> be item <number> of <list name>.
        if "item" in tokens_lc and "of" in tokens_lc:
            try:
                be_i = tokens_lc.index("be")
                item_i = tokens_lc.index("item", be_i + 1)
                of_i = tokens_lc.index("of", item_i + 1)
            except ValueError:
                be_i = -1
            else:
                target = _join_name(tokens[1:be_i])
                index_expr = parse_expr(tokens[item_i + 1 : of_i], line_no=line_no)
                list_name = _join_name(tokens[of_i + 1 :])
                cur.i += 1
                return ListItemGet(span, target, index_expr, list_name)

        # Special: let x be the result of running f with a, b.
        # let [var] be the result of running [function] with [value, value].
        if "result" in tokens_lc:
            # Find "be the result of running"
            # tokens: let <target...> be the result of running <fn...> [with <args...>]
            try:
                be_i = tokens_lc.index("be")
            except ValueError:
                try:
                    be_i = tokens_lc.index("=")
                except ValueError:
                    raise VerbaParseError("I expected 'be' or '=' in this let statement.", line_no=line_no, line=lt.raw)
            target = _join_name(tokens[1:be_i])
            expected = ["the", "result", "of", "running"]
            if tokens_lc[be_i] not in ["be", "="] or tokens_lc[be_i + 1 : be_i + 1 + len(expected)] != expected:
                # continue to normal let parsing
                pass
            else:
                j = be_i + 1 + len(expected)
                if j >= len(tokens):
                    raise VerbaParseError("I expected a function name after 'running'.", line_no=line_no)
                # Function name goes until optional "with"
                if "with" in tokens_lc[j:]:
                    with_i = tokens_lc.index("with", j)
                    fn = _join_name(tokens[j:with_i])
                    args_tokens = tokens[with_i + 1 :]
                    exprs = [parse_expr(a, line_no=line_no) for a in _split_by_commas(args_tokens)]
                    cur.i += 1
                    return LetResultOfRun(span, target, fn, exprs)
                else:
                    fn = _join_name(tokens[j:])
                    args_exprs = []
                
                if "." in fn:
                    parts = fn.split(".")
                    cur.i += 1
                    return LetResultOfMethod(span, target, parts[0], parts[1], args_exprs)
                else:
                    cur.i += 1
                    return LetResultOfRun(span, target, fn, args_exprs)

        # General let: let <name...> be [the number|the word|the flag] <value...>.
        try:
            be_i = tokens_lc.index("be")
        except ValueError:
            try:
                be_i = tokens_lc.index("=")
            except ValueError:
                raise VerbaParseError("I expected 'be' or '=' in this let statement.", line_no=line_no, line=lt.raw)
        name = _join_name(tokens[1:be_i])
        rest = tokens[be_i + 1 :]
        rest_lc = tokens_lc[be_i + 1 :]

        forced_type: Optional[str] = None

        # List literal: "a list of ..."
        if len(rest_lc) >= 3 and rest_lc[0:3] == ["a", "list", "of"]:
            forced_type = "list"
            items_tokens = rest[3:]
            items = [parse_expr(item, line_no=line_no) for item in _split_by_commas(items_tokens)]
            cur.i += 1
            return Let(span, name, Literal(span, items), forced_type=forced_type)

        if len(rest_lc) >= 2 and rest_lc[0] == "the" and rest_lc[1] in ["number", "word", "flag"]:
            forced_type = rest_lc[1]
            value_tokens = rest[2:]
            if forced_type == "flag":
                if not value_tokens:
                    raise VerbaParseError("I expected true or false after 'the flag'.", line_no=line_no)
                v = value_tokens[0].lower()
                if v not in ["true", "false"]:
                    raise VerbaParseError("A flag must be true or false.", line_no=line_no)
                cur.i += 1
                return Let(span, name, Literal(span, v == "true"), forced_type=forced_type)
            if forced_type == "word":
                if not value_tokens:
                    raise VerbaParseError("I expected a word after 'the word'.", line_no=line_no)
                if value_tokens[0].lower() == "quote":
                    value = parse_expr(value_tokens, line_no=line_no)
                else:
                    # A single token word
                    value = Literal(span, value_tokens[0])
                cur.i += 1
                return Let(span, name, value, forced_type=forced_type)
            # number
            value = parse_expr(value_tokens, line_no=line_no)
            cur.i += 1
            return Let(span, name, value, forced_type=forced_type)

        value = parse_expr(rest, line_no=line_no)
        cur.i += 1
        return Let(span, name, value)

    # set ... to ...
    if tokens_lc[0] == "set":
        _require_period(lt, line_no)
        try:
            to_i = tokens_lc.index("to")
        except ValueError:
            raise VerbaParseError("I expected 'to' in this set statement.", line_no=line_no, line=lt.raw)
        name = _join_name(tokens[1:to_i])
        value = parse_expr(tokens[to_i + 1 :], line_no=line_no)
        cur.i += 1
        return SetVar(span, name, value)

    # Check for math assignment: x += 5.
    for idx, t in enumerate(tokens_lc):
        if t in ["+=", "-=", "*=", "/="]:
            by_i = idx
            break
    else:
        by_i = -1
    
    if by_i != -1:
        name = _join_name(tokens[:by_i])
        value = parse_expr(tokens[by_i + 1 :], line_no=line_no)
        cur.i += 1
        op = tokens_lc[by_i]
        if op == "+=": return Increase(span, name, value)
        if op == "-=": return Decrease(span, name, value)
        if op == "*=": return SetVar(span, name, BinaryOp(span, "*", VarRef(span, name), value))
        if op == "/=": return SetVar(span, name, BinaryOp(span, "/", VarRef(span, name), value))

    # Check for concise definition: x = 5.
    try:
        eq_i = tokens_lc.index("=")
    except ValueError:
        eq_i = -1
        
    if eq_i != -1 and eq_i + 1 < len(tokens_lc) and tokens_lc[eq_i+1] != "=":
        # We don't want to parse `x == 5` here.
        name = _join_name(tokens[:eq_i])
        val_tc = tokens_lc[eq_i+1:]
        
        if val_tc and val_tc[0] == "await":
            cur.i += 1
            return AwaitStmt(span, name, _join_name(tokens[eq_i+2:]))
            
        if len(val_tc) >= 2 and val_tc[:2] == ["async", "run"]:
            with_i = val_tc.index("with") if "with" in val_tc else -1
            if with_i != -1:
                fn = _join_name(tokens[eq_i+3 : eq_i+1+with_i])
                args = [parse_expr(a, line_no=line_no) for a in _split_by_commas(tokens[eq_i+1+with_i+1:])]
            else:
                fn = _join_name(tokens[eq_i+3:])
                args = []
            cur.i += 1
            return AsyncRun(span, name, fn, args)
            
        if len(val_tc) >= 4 and val_tc[:4] == ["the", "result", "of", "running"]:
            if "with" in val_tc:
                with_i = val_tc.index("with")
                fn = _join_name(tokens[eq_i + 5 : eq_i + 1 + with_i])
                args = [parse_expr(a, line_no=line_no) for a in _split_by_commas(tokens[eq_i + 1 + with_i + 1 :])]
            else:
                fn = _join_name(tokens[eq_i + 5 :])
                args = []
            
            cur.i += 1
            if "." in fn:
                parts = fn.split(".")
                return LetResultOfMethod(span, name, parts[0], parts[1], args)
            return LetResultOfRun(span, name, fn, args)
            
        if len(val_tc) >= 3 and val_tc[:3] == ["a", "list", "of"]:
            items_tokens = tokens[eq_i + 4:]
            items = [parse_expr(item, line_no=line_no) for item in _split_by_commas(items_tokens)]
            cur.i += 1
            value = Literal(span, items)
            if "." in name:
                parts = name.split(".")
                return ObjectPropSet(span, parts[0], parts[1], value)
            return Let(span, name, value, forced_type="list")
            
        value = parse_expr(tokens[eq_i + 1 :], line_no=line_no)
        cur.i += 1
        
        if "." in name:
            parts = name.split(".")
            return ObjectPropSet(span, parts[0], parts[1], value)
            
        return Let(span, name, value)

    # increase/decrease
    if tokens_lc[0] in ["increase", "decrease"]:
        _require_period(lt, line_no)
        try:
            by_i = tokens_lc.index("by")
        except ValueError:
            raise VerbaParseError("I expected 'by' in this statement.", line_no=line_no, line=lt.raw)
        name = _join_name(tokens[1:by_i])
        value = parse_expr(tokens[by_i + 1 :], line_no=line_no)
        cur.i += 1
        if tokens_lc[0] == "increase":
            return Increase(span, name, value)
        return Decrease(span, name, value)

    # say/display
    if tokens_lc[0] in ["say", "display"]:
        _require_period(lt, line_no)
        
        # Helper: swap commas out for "and" behind the scenes to keep the logic running flawlessly
        args_t = [t if t != "," else "and" for t in tokens[1:]]
        
        parts = _split_by_word(args_t, word="and")
        values = [_parse_say_value(p, line_no=line_no) for p in parts if p]
        cur.i += 1
        return Say(span, values, newline=tokens_lc[0] == "say")

    # ask
    if tokens_lc[0] == "ask":
        _require_period(lt, line_no)
        # ask for <name>
        if tokens_lc[:2] == ["ask", "for"]:
            name = _join_name(tokens[2:])
            cur.i += 1
            return Ask(span, name)
        # ask the user for <name>
        if tokens_lc[:4] == ["ask", "the", "user", "for"]:
            name = _join_name(tokens[4:])
            cur.i += 1
            return Ask(span, name)
        # ask the user "prompt..." and save to <name>
        if tokens_lc[:3] == ["ask", "the", "user"]:
            if "save" in tokens_lc and "to" in tokens_lc:
                save_i = tokens_lc.index("save")
                to_i = tokens_lc.index("to", save_i)
                
                if tokens_lc[3] == "quote":
                    prompt_tokens = tokens[4:save_i]
                else:
                    prompt_tokens = tokens[3:save_i]
                    
                if not prompt_tokens:
                    raise VerbaParseError(
                        "I expected a prompt between 'user' and 'and save to'.",
                        line_no=line_no,
                        line=lt.raw,
                    )
                
                # Optional 'and' right before save
                if prompt_tokens and prompt_tokens[-1].lower() == "and":
                    prompt_tokens = prompt_tokens[:-1]
                prompt = " ".join(prompt_tokens).strip()

                if prompt.startswith('"') and prompt.endswith('"'):
                    prompt = prompt[1:-1]
                elif prompt.startswith("'") and prompt.endswith("'"):
                    prompt = prompt[1:-1]
                
                name = _join_name(tokens[to_i + 1 :])
                cur.i += 1
                return Ask(span, name, prompt=prompt)

        raise VerbaParseError(
            "I did not understand this ask line. Try 'ask for name.' or 'ask the user quote ... and save to name.'",
            line_no=line_no,
            line=lt.raw,
        )

    # file I/O: save/load
    if tokens_lc[0] == "save":
        _require_period(lt, line_no)
        # save [text] to file called [filename].
        try:
            to_i = tokens_lc.index("to", 1)
        except ValueError:
            raise VerbaParseError("I expected 'to file called' in this save line.", line_no=line_no, line=lt.raw)
        if tokens_lc[to_i + 1 : to_i + 3] != ["file", "called"]:
            raise VerbaParseError("A save line must say 'to file called'.", line_no=line_no, line=lt.raw)
        text_expr = parse_expr(tokens[1:to_i], line_no=line_no)
        filename_expr = parse_expr(tokens[to_i + 3 :], line_no=line_no)
        cur.i += 1
        return SaveToFile(span, text_expr, filename_expr)

    if tokens_lc[0] == "load":
        _require_period(lt, line_no)
        # load file called [filename] into [variable].
        if tokens_lc[1:3] != ["file", "called"]:
            raise VerbaParseError("A load line must start with 'load file called'.", line_no=line_no, line=lt.raw)
        if "into" not in tokens_lc[3:]:
            raise VerbaParseError("A load line must say 'into <variable>'.", line_no=line_no, line=lt.raw)
        into_i = tokens_lc.index("into", 3)
        filename_expr = parse_expr(tokens[3:into_i], line_no=line_no)
        target_name = _join_name(tokens[into_i + 1 :])
        cur.i += 1
        return LoadFile(span, filename_expr, target_name)
        
    if tokens_lc[0] == "append":
        _require_period(lt, line_no)
        to_i = tokens_lc.index("to")
        text_expr = parse_expr(tokens[1:to_i], line_no=line_no)
        filename_expr = parse_expr(tokens[to_i + 3 :], line_no=line_no)
        cur.i += 1
        return AppendToFile(span, text_expr, filename_expr)
        
    if tokens_lc[:2] == ["delete", "file"]:
        _require_period(lt, line_no)
        filename_expr = parse_expr(tokens[3:], line_no=line_no)
        cur.i += 1
        return DeleteFile(span, filename_expr)

    if tokens_lc[0] == "fetch":
        _require_period(lt, line_no)
        into_i = tokens_lc.index("into")
        url = parse_expr(tokens[1:into_i], line_no=line_no)
        target = _join_name(tokens[into_i + 1 :])
        cur.i += 1
        return FetchUrl(span, url, target)
        
    if tokens_lc[0] in ["free", "delete"]:
        _require_period(lt, line_no)
        cur.i += 1
        return FreeVar(span, _join_name(tokens[1:]))

    if tokens_lc[0] == "import":
        _require_period(lt, line_no)
        # import from file called [filename].
        if tokens_lc[1:4] != ["from", "file", "called"]:
            raise VerbaParseError("An import line must say 'import from file called'.", line_no=line_no, line=lt.raw)
        filename_expr = parse_expr(tokens[4:], line_no=line_no)
        cur.i += 1
        return Import(span, filename_expr)

    # list ops: add/remove
    if tokens_lc[0] == "add":
        _require_period(lt, line_no)
        try:
            to_i = tokens_lc.index("to")
        except ValueError:
            raise VerbaParseError("I expected 'to' in this add statement.", line_no=line_no, line=lt.raw)
        value = parse_expr(tokens[1:to_i], line_no=line_no)
        list_name = _join_name(tokens[to_i + 1 :])
        cur.i += 1
        return ListAdd(span, value, list_name)

    if tokens_lc[0] == "remove":
        _require_period(lt, line_no)
        try:
            from_i = tokens_lc.index("from")
        except ValueError:
            raise VerbaParseError("I expected 'from' in this remove statement.", line_no=line_no, line=lt.raw)
        value = parse_expr(tokens[1:from_i], line_no=line_no)
        list_name = _join_name(tokens[from_i + 1 :])
        cur.i += 1
        return ListRemove(span, value, list_name)

    # let x be item N of list
    if tokens_lc[0] == "let" and "item" in tokens_lc:
        # handled earlier in 'let' branch; keep unreachable
        pass

    # if ... , do the following. or if ... :
    if tokens_lc[0] == "if":
        _require_period(lt, line_no)
        
        cond_tokens = tokens[1:]
        if cond_tokens and cond_tokens[-1] == ":":
            cond_tokens = cond_tokens[:-1]
        elif len(cond_tokens) >= 3 and _lc(cond_tokens)[-3:] == ["do", "the", "following"]:
            cond_tokens = cond_tokens[:-3]
        else:
            raise VerbaParseError(
                "An if line must end with 'do the following.' or ':'",
                line_no=line_no,
                line=lt.raw,
            )
        
        if cond_tokens and cond_tokens[-1] == ",":
            cond_tokens = cond_tokens[:-1]
        condition = parse_condition(cond_tokens, line_no=line_no)
        cur.i += 1
        then_body = _parse_block(cur, expected_indent=expected_indent + 4)

        # optional otherwise do the following.
        else_body: Optional[list[Stmt]] = None
        if cur.i < len(cur.lines):
            nxt = cur.lines[cur.i]
            nxt_no = cur.i + 1
            nxt_lc = _lc(nxt.tokens)
            is_otherwise = (
                (len(nxt_lc) >= 4 and nxt_lc[:3] == ["otherwise", "do", "the"] and nxt_lc[-1] == "following") or
                (len(nxt_lc) >= 4 and nxt_lc[:3] == ["else", "do", "the"] and nxt_lc[-1] == "following") or
                nxt_lc == ["else", ":"] or
                nxt_lc == ["otherwise", ":"]
            )
            if nxt.indent == expected_indent and is_otherwise:
                _require_period(nxt, nxt_no)
                cur.i += 1
                else_body = _parse_block(cur, expected_indent=expected_indent + 4)

        # expect end if.
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or _lc(end_line.tokens)[0] != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return If(span, condition, then_body, else_body)

    # repeat N times, do the following.
    if tokens_lc[0] == "repeat":
        _require_period(lt, line_no)
        if not (len(tokens_lc) >= 4 and tokens_lc[-3:] == ["do", "the", "following"]):
            raise VerbaParseError(
                "A repeat line must end with 'do the following.'",
                line_no=line_no,
                line=lt.raw,
            )
        if "times" not in tokens_lc:
            raise VerbaParseError("I expected 'times' in this repeat line.", line_no=line_no, line=lt.raw)
        times_i = tokens_lc.index("times")
        times_expr = parse_expr([t for t in tokens[1:times_i] if t != ","], line_no=line_no)
        cur.i += 1
        body = _parse_block(cur, expected_indent=expected_indent + 4)
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end repeat.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or _lc(end_line.tokens)[:2] != ["end", "repeat"]:
            raise VerbaParseError("I expected 'end repeat.'", line_no=end_no, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return Repeat(span, times_expr, body)

    # keep doing the following while ...
    if tokens_lc[:4] == ["keep", "doing", "the", "following"]:
        _require_period(lt, line_no)
        if "while" not in tokens_lc:
            raise VerbaParseError("I expected 'while' in this keep line.", line_no=line_no, line=lt.raw)
        while_i = tokens_lc.index("while")
        cond = parse_condition(tokens[while_i + 1 :], line_no=line_no)
        cur.i += 1
        body = _parse_block(cur, expected_indent=expected_indent + 4)
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end keep.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or _lc(end_line.tokens)[0] != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return While(span, cond, body)

    # while ...:
    if tokens_lc[0] == "while":
        _require_period(lt, line_no)
        
        cond_tokens = tokens[1:]
        if cond_tokens and cond_tokens[-1] == ":":
            cond_tokens = cond_tokens[:-1]
        
        cond = parse_condition(cond_tokens, line_no=line_no)
        cur.i += 1
        body = _parse_block(cur, expected_indent=expected_indent + 4)
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or _lc(end_line.tokens)[0] != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return While(span, cond, body)

    # for each item in list, do the following.
    if tokens_lc[:2] == ["for", "each"]:
        _require_period(lt, line_no)
        if "in" not in tokens_lc:
            raise VerbaParseError("I expected 'in' in this for each line.", line_no=line_no, line=lt.raw)
        if not (len(tokens_lc) >= 4 and tokens_lc[-3:] == ["do", "the", "following"]):
            raise VerbaParseError("A for each line must end with 'do the following.'", line_no=line_no, line=lt.raw)
        in_i = tokens_lc.index("in")
        item_name = _join_name(tokens[2:in_i])
        list_tokens = tokens[in_i + 1 : -3]
        if list_tokens and list_tokens[-1] == ",":
            list_tokens = list_tokens[:-1]
        list_name = _join_name(list_tokens)
        cur.i += 1
        body = _parse_block(cur, expected_indent=expected_indent + 4)
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end for.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or _lc(end_line.tokens)[0] != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return ForEach(span, item_name, list_name, body)
        
    # for item in list:
    if tokens_lc[0] == "for" and "in" in tokens_lc and tokens_lc[1] != "each":
        _require_period(lt, line_no)
        if tokens_lc[-1] != ":":
            raise VerbaParseError("A for line must end with ':'", line_no=line_no, line=lt.raw)
        in_i = tokens_lc.index("in")
        item_name = _join_name(tokens[1:in_i])
        list_tokens = tokens[in_i + 1 : -1]
        list_name = _join_name(list_tokens)
        cur.i += 1
        body = _parse_block(cur, expected_indent=expected_indent + 4)
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or _lc(end_line.tokens)[0] != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return ForEach(span, item_name, list_name, body)

    if tokens_lc[0] == "class":
        _require_period(lt, line_no)
        name = _join_name(tokens[1:-1]) if tokens_lc[-1] == ":" else _join_name(tokens[1:])
        cur.i += 1
        body = _parse_block(cur, expected_indent=expected_indent + 4)
        methods = {}
        for s in body:
            if isinstance(s, Define) or isinstance(s, AsyncDefine):
                methods[s.name] = s
            elif isinstance(s, Note):
                pass
            else:
                raise VerbaParseError("Only 'define' methods and notes are allowed at the root of a 'class'.", line_no=line_no)
        
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or _lc(end_line.tokens)[0] != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return ClassDef(span, name, methods)

    # define function ...
    if tokens_lc[0] in ["define", "async"] and (tokens_lc[0] == "define" or (len(tokens_lc) > 1 and tokens_lc[1] == "define")):
        _require_period(lt, line_no)
        
        is_async = tokens_lc[0] == "async"
        offset = 1 if not is_async else 2
        
        # Trim `:` or `as follows` from the end to leave only the signature
        signature = tokens[offset:]
        sig_lc = tokens_lc[offset:]
        if sig_lc and sig_lc[-1] == ":":
            signature = signature[:-1]
            sig_lc = sig_lc[:-1]
            if len(sig_lc) >= 2 and sig_lc[-2:] == ["as", "follows"]:
                signature = signature[:-2]
                sig_lc = sig_lc[:-2]
        elif len(sig_lc) >= 2 and sig_lc[-2:] == ["as", "follows"]:
            signature = signature[:-2]
            sig_lc = sig_lc[:-2]
        else:
             raise VerbaParseError("A define line must end with 'as follows.' or ':'", line_no=line_no, line=lt.raw)
        
        if "needing" in sig_lc:
            needing_i = sig_lc.index("needing")
            name = _join_name(signature[:needing_i])
            params = [_join_name(p) for p in _split_by_commas(signature[needing_i + 1 :]) if p]
        else:
            name = _join_name(signature)
            params = []
            
        cur.i += 1
        body = _parse_block(cur, expected_indent=expected_indent + 4)
        # expect end define.
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end define.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or _lc(end_line.tokens)[0] != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return Define(span, name, params, body)

    # give ... or give back ...
    if tokens_lc[:2] == ["give", "back"] or tokens_lc[0] == "give":
        _require_period(lt, line_no)
        value_start = 2 if tokens_lc[:2] == ["give", "back"] else 1
        value = parse_expr(tokens[value_start:], line_no=line_no)
        cur.i += 1
        return GiveBack(span, value)

    # run function ...
    if tokens_lc[0] == "run":
        _require_period(lt, line_no)
        if "with" in tokens_lc:
            with_i = tokens_lc.index("with")
            fn = _join_name(tokens[1:with_i])
            args = [parse_expr(a, line_no=line_no) for a in _split_by_commas(tokens[with_i + 1 :])]
        else:
            fn = _join_name(tokens[1:])
            args = []
            
        cur.i += 1
        
        if "." in fn:
            parts = fn.split(".")
            return MethodCall(span, parts[0], parts[1], args)
        return Run(span, fn, args)

    # let x be item N of list.
    if tokens_lc[0] == "let" and "item" in tokens_lc and "of" in tokens_lc:
        # This branch is normally pre-empted by the general 'let' handler; we keep this
        # pattern here for clarity if you later prefer strict ordering.
        pass

    # try to do the following.
    if tokens_lc[:5] == ["try", "to", "do", "the", "following"]:
        _require_period(lt, line_no)
        cur.i += 1
        try_body = _parse_block(cur, expected_indent=expected_indent + 4)
        catch_body: Optional[list[Stmt]] = None
        error_name: Optional[str] = None
        
        if cur.i < len(cur.lines):
            nxt = cur.lines[cur.i]
            nxt_no = cur.i + 1
            nxt_lc = _lc(nxt.tokens)
            if nxt.indent == expected_indent and len(nxt_lc) >= 2 and nxt_lc[:2] == ["on", "error"]:
                clean_nxt_lc = [t for t in nxt_lc if t != ","]
                clean_nxt_tokens = [t for t in nxt.tokens if t != ","]
                if len(clean_nxt_lc) >= 3 and clean_nxt_lc[-3:] == ["do", "the", "following"]:
                    _require_period(nxt, nxt_no)
                    if "saving" in clean_nxt_lc and "to" in clean_nxt_lc:
                        sav_i = clean_nxt_lc.index("saving")
                        to_i = clean_nxt_lc.index("to")
                        if to_i == sav_i + 1:
                            do_i = len(clean_nxt_lc) - 3
                            error_name = _join_name(clean_nxt_tokens[to_i + 1 : do_i])
                    cur.i += 1
                    catch_body = _parse_block(cur, expected_indent=expected_indent + 4)
                else:
                    raise VerbaParseError("I expected 'on error, do the following.' or 'on error saving to [variable], do the following.'", line_no=nxt_no, line=nxt.raw)
        
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end try.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or _lc(end_line.tokens)[0] != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return TryBlock(span, try_body, catch_body, error_name)

    raise VerbaParseError(
        f"I did not understand line {line_no}. Did you mean to use say, let, set, if, repeat, keep, define, run, or ask?",
        line_no=line_no,
        line=lt.raw,
    )


def _split_by_commas(tokens: list[str]) -> list[list[str]]:
    # If there are no commas, treat the whole thing as one group (this allows
    # multi-word names like "user age" to stay together).
    if "," not in tokens:
        return [tokens] if tokens else []

    groups: list[list[str]] = []
    cur: list[str] = []
    for t in tokens:
        if t == ",":
            if cur:
                groups.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        groups.append(cur)
    return groups


def _split_by_word(tokens: list[str], *, word: str) -> list[list[str]]:
    out: list[list[str]] = []
    cur: list[str] = []
    for t in tokens:
        if t.lower() == word:
            out.append(cur)
            cur = []
        else:
            cur.append(t)
    out.append(cur)
    return out


def _parse_say_value(tokens: list[str], *, line_no: int) -> object:
    if not tokens:
        raise VerbaParseError("I expected something to say.", line_no=line_no)
    tokens_lc = _lc(tokens)
    # If it looks like math, parse as an expression. Otherwise:
    # - a single token can be a variable name OR a single-word literal (resolved at runtime in say-context)
    # - multiple tokens are treated as a literal phrase without requiring "quote"
    if any(t in ["+", "-", "*", "/", "plus", "minus", "times", "divided", "remainder"] for t in tokens_lc):
        return parse_expr(tokens, line_no=line_no)
    if len(tokens) == 1:
        return parse_expr(tokens, line_no=line_no)
    
    # If it is a string enclosed in double or single quotes without the 'quote' keyword mapping
    if (tokens[0].startswith('"') and tokens[-1].endswith('"')) or (tokens[0].startswith("'") and tokens[-1].endswith("'")):
        return Literal(Span(line_no), " ".join(tokens)[1:-1])

    return Literal(Span(line_no), " ".join(tokens))
