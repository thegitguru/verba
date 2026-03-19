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
    Expr,
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
    Ref,
    Deref,
    DerefSet,
    ServeStart,
    ServeRoute,
    ServeRespond,
    ServeRedirect,
    StringConcat,
)
from .errors import VerbaParseError
from .tokenize import LineTokens, tokenize_program, Token


def _lc(tokens: list[Token]) -> list[str]:
    return [t.value.lower() for t in tokens]


def _require_period(line: LineTokens, line_no: int) -> None:
    if not line.tokens:
        return
    last = line.tokens[-1]
    if last.value not in [".", ":"]:
        raise VerbaParseError(
            "Every statement must end with a period (or a colon for block starters).",
            line_no=line_no,
            col=last.col + len(last.value),
            line=line.raw,
        )


def _join_name(tokens: list[Token], *, line_no: int = 0) -> str:
    if len(tokens) > 1:
        # Check if they are separated by spaces (which they are if multiple tokens)
        vals = [t.value for t in tokens]
        raise VerbaParseError(
            f"I found a multi-word name: '{' '.join(vals)}'. Names must be a single word without spaces.",
            line_no=line_no,
            col=tokens[0].col,
            line=tokens[0].raw_line
        )
    return tokens[0].value.lower() if tokens else ""


_COMPARISONS: list[tuple[list[str], str]] = [
    (["is", "not", "null"], "!null"),
    (["is", "null"], "null"),
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
    (["%"], "%"),
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


def _parse_atom(tokens: list[Token], tokens_lc: list[str], i: int, *, span: Span) -> tuple[object, int]:
    t = tokens[i]
    tl = tokens_lc[i]

    if tl == "true":
        return Literal(span, True), i + 1
    if tl == "false":
        return Literal(span, False), i + 1
    if tl == "null":
        return Literal(span, None), i + 1

    # &x  — concise ref
    if t.value == "&" and i + 1 < len(tokens):
        return Ref(span, tokens[i + 1].value.lower()), i + 2

    # deref ptr — dereference read
    if tl == "deref" and i + 1 < len(tokens):
        return Deref(span, tokens[i + 1].value.lower()), i + 2

    # join <part>, <part>, ... — string concatenation expression
    if tl == "join":
        parts = [parse_expr(p, line_no=span.line_no) for p in _split_by_commas(tokens[i + 1:]) if p]
        return StringConcat(span, parts), len(tokens)

    num = _parse_number(t.value)
    if num is not None:
        return Literal(span, num), i + 1

    if (t.value.startswith('"') and t.value.endswith('"')) or (t.value.startswith("'") and t.value.endswith("'")):
        return Literal(span, t.value[1:-1]), i + 1
        
    if "." in t.value and t.value.count(".") == 1:
        idx = t.value.index(".")
        if idx > 0 and idx < len(t.value) - 1:
            return ObjectPropGet(span, t.value[:idx].lower(), t.value[idx+1:].lower()), i + 1

    # Word literals are bare single tokens (e.g. hello, Alice). Multi-word text uses "quote".
    return VarRef(span, _join_name([t])), i + 1


def _scan_math_op(tokens_lc: list[str], i: int) -> tuple[Optional[str], int]:
    for phrase, op in _MATH_OPS:
        if _try_match(tokens_lc, i, phrase):
            return op, i + len(phrase)
    return None, i


def _precedence(op: str) -> int:
    return {"*": 2, "/": 2, "%": 2, "+": 1, "-": 1}.get(op, 0)


def parse_expr(tokens: list[Token], *, line_no: int) -> Expr:
    if not tokens:
        raise VerbaParseError("I expected a value here.", line_no=line_no)
    
    # Use the first token to make a rich span if possible
    # We don't have the LineTokens here, but the tokens themselves have raw_line.
    span = Span(tokens[0].line_no, col=tokens[0].col, line_content=tokens[0].raw_line)
    
    tokens_lc = _lc(tokens)

    if tokens_lc[0] == "new":
        if "with" in tokens_lc:
            with_i = tokens_lc.index("with")
            class_name = _join_name(tokens[1:with_i], line_no=line_no)
            args = [parse_expr(a, line_no=line_no) for a in _split_by_commas(tokens[with_i + 1 :])]
            return ObjectNew(span, class_name, args)
        class_name = _join_name(tokens[1:], line_no=line_no)
        return ObjectNew(span, class_name, [])

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
            # Reached end of possible math expression.
            # In Verba, we might have multiple expressions on a line, but parse_expr 
            # usually expects the whole list to be one expression.
            raise VerbaParseError(
                f"I did not understand this math expression. I found '{tokens[i].value}' where I expected an operator.",
                line_no=line_no,
                col=tokens[i].col,
                line=tokens[i].raw_line
            )

        while ops and _precedence(ops[-1]) >= _precedence(op):
            out.append(ops.pop())
        ops.append(op)
        i = next_i
        expecting_value = True

    if expecting_value:
        raise VerbaParseError("I expected a value after the math operator.", line_no=line_no, col=tokens[-1].col + len(tokens[-1].value), line=tokens[-1].raw_line)

    while ops:
        out.append(ops.pop())

    # Build AST from RPN.
    stack: list[object] = []
    for item in out:
        if isinstance(item, str):
            if len(stack) < 2:
                # Should not happen if shunting-yard logic is correct
                raise VerbaParseError("Internal math error: not enough values for operator.", line_no=line_no)
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


def parse_condition(tokens: list[Token], *, line_no: int) -> BoolExpr:
    if not tokens:
        raise VerbaParseError("I expected a condition here.", line_no=line_no)
    tokens_lc = _lc(tokens)
    span = Span(tokens[0].line_no, col=tokens[0].col, line_content=tokens[0].raw_line)

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

            # null / !null comparisons have no right-hand side
            if op in ("null", "!null"):
                left = parse_expr(left_tokens, line_no=line_no)
                return Compare(span, op, left, Literal(span, None)), next_k

            end = len(tokens_lc)
            for m in range(next_k, len(tokens_lc)):
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
            col=tokens[j].col,
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


def _make_span(lt: LineTokens, tokens: list[Token]) -> Span:
    """Creates a Span object representing the start of these tokens."""
    if not tokens:
        return Span(lt.line_no, col=lt.indent, line_content=lt.raw)
    return Span(tokens[0].line_no, col=tokens[0].col, line_content=tokens[0].raw_line)


def _parse_statement(cur: _Cursor, *, expected_indent: int) -> Optional[Stmt]:
    lt = cur.lines[cur.i]
    line_no = cur.i + 1
    original_tokens = lt.tokens
    if not original_tokens:
        cur.i += 1
        return None

    span = _make_span(lt, original_tokens)
    first_val_orig = original_tokens[0].value.lower()

    # Comments / notes (don't require period)
    if first_val_orig == "note":
        cur.i += 1
        return Note(span, " ".join([t.value for t in original_tokens[1:]]))

    # Every other statement must have a terminator (. or :)
    _require_period(lt, line_no)
    
    # Strip the terminator for parsing content
    term_token = original_tokens[-1]
    term_val = term_token.value
    
    tokens = original_tokens[:-1]
    if not tokens:
        # Line was just "." or ":"
        raise VerbaParseError("I found a stray symbol without a statement.", line_no=line_no, col=term_token.col)
    
    tokens_lc = _lc(tokens)
    first_val = tokens_lc[0]

    # Block endings
    if first_val == "end":
        raise VerbaParseError(
            "I found an 'end.' without a matching block to end.", 
            line_no=line_no, 
            col=tokens[0].col,
            line=lt.raw
        )

    # let is no longer supported — use x = value.
    if first_val == "let":
        raise VerbaParseError(
            "'let' is not supported. Use concise assignment: x = value.",
            line_no=line_no, col=tokens[0].col, line=lt.raw
        )

    # set is no longer supported — use x = value or deref ptr = value.
    if first_val == "set":
        raise VerbaParseError(
            "'set' is not supported. Use concise assignment: x = value. or deref ptr = value.",
            line_no=line_no, col=tokens[0].col, line=lt.raw
        )

    # Prevent keywords from being evaluated as LHS of a concise assignment
    _STATEMENT_KEYWORDS = {
        "say", "print", "display", "ask", "if", "for", "while",
        "repeat", "define", "async", "run", "let", "set", "increase",
        "decrease", "save", "load", "import", "class", "free", "delete",
        "fetch", "append", "note", "try", "otherwise", "else", "end", "give", "return",
        "await", "deref", "serve", "on", "respond"
    }
    is_keyword_stmt = first_val in _STATEMENT_KEYWORDS

    if first_val == "await":
        if "=" in tokens_lc:
            eq_i = tokens_lc.index("=")
            target = _join_name(tokens[1:eq_i], line_no=line_no)
            task = _join_name(tokens[eq_i + 1 :], line_no=line_no)
            cur.i += 1
            return AwaitStmt(span, target, task)
        raise VerbaParseError("I expected 'await [target] = [task].'", line_no=line_no, col=tokens[0].col + len(tokens[0].value))

    # Check for math assignment: x += 5.
    by_i = -1
    for idx, t in enumerate(tokens_lc):
        if t in ["+=", "-=", "*=", "/="]:
            by_i = idx
            break
    
    if by_i != -1 and not is_keyword_stmt:
        name = _join_name(tokens[:by_i], line_no=line_no)
        value = parse_expr(tokens[by_i + 1 :], line_no=line_no)
        cur.i += 1
        op = tokens_lc[by_i]
        if op == "+=": return Increase(span, name, value)
        if op == "-=": return Decrease(span, name, value)
        if op == "*=": return SetVar(span, name, BinaryOp(span, "*", VarRef(span, name), value))
        if op == "/=": return SetVar(span, name, BinaryOp(span, "/", VarRef(span, name), value))

    # Check for concise definition: x = 5.
    eq_i = tokens_lc.index("=") if "=" in tokens_lc else -1
        
    if eq_i != -1 and eq_i + 1 < len(tokens_lc) and tokens_lc[eq_i+1] != "=" and not is_keyword_stmt:
        name = _join_name(tokens[:eq_i], line_no=line_no)
        val_tc = tokens_lc[eq_i+1:]
        
        if val_tc and val_tc[0] == "await":
            cur.i += 1
            return AwaitStmt(span, name, _join_name(tokens[eq_i+2:], line_no=line_no))
            
        if len(val_tc) >= 2 and val_tc[:2] == ["async", "run"]:
            with_i = val_tc.index("with") if "with" in val_tc else -1
            if with_i != -1:
                fn = _join_name(tokens[eq_i+3 : eq_i+1+with_i], line_no=line_no)
                args = [parse_expr(a, line_no=line_no) for a in _split_by_commas(tokens[eq_i+1+with_i+1:])]
            else:
                fn = _join_name(tokens[eq_i+3:], line_no=line_no)
                args = []
            cur.i += 1
            return AsyncRun(span, name, fn, args)
            
        if len(val_tc) >= 4 and val_tc[:4] == ["the", "result", "of", "running"]:
            if "with" in val_tc:
                with_i = val_tc.index("with")
                fn = _join_name(tokens[eq_i + 5 : eq_i + 1 + with_i], line_no=line_no)
                args = [parse_expr(a, line_no=line_no) for a in _split_by_commas(tokens[eq_i + 1 + with_i + 1 :])]
            else:
                fn = _join_name(tokens[eq_i + 5 :], line_no=line_no)
                args = []
            
            cur.i += 1
            if "." in fn:
                parts = fn.split(".")
                return LetResultOfMethod(span, name, parts[0], parts[1], args)
            return LetResultOfRun(span, name, fn, args)
            
        if len(val_tc) >= 3 and val_tc[:3] == ["a", "list", "of"]:
            items = [parse_expr(item, line_no=line_no) for item in _split_by_commas(tokens[eq_i + 4:])]
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

    # increase/decrease are no longer supported — use += / -=.
    if first_val in ["increase", "decrease"]:
        raise VerbaParseError(
            "'increase'/'decrease' are not supported. Use x += value. or x -= value.",
            line_no=line_no, col=tokens[0].col, line=lt.raw
        )

    # say/display
    if first_val in ["say", "display"]:
        parts = _split_by_commas(tokens[1:])
        values = [_parse_say_value(p, line_no=line_no) for p in parts if p]
        cur.i += 1
        return Say(span, values, newline=first_val == "say")

    # ask
    if first_val == "ask":
        # ask for <name>
        if tokens_lc[:2] == ["ask", "for"]:
            name = _join_name(tokens[2:], line_no=line_no)
            cur.i += 1
            return Ask(span, name)
        # ask the user for <name>
        if tokens_lc[:4] == ["ask", "the", "user", "for"]:
            name = _join_name(tokens[4:], line_no=line_no)
            cur.i += 1
            return Ask(span, name)
        # ask the user "prompt..." and save to <name>
        if tokens_lc[:3] == ["ask", "the", "user"]:
            if "save" in tokens_lc and "to" in tokens_lc:
                save_i = tokens_lc.index("save")
                to_i = tokens_lc.index("to", save_i)
                prompt_tokens = tokens[3:save_i]
                if not prompt_tokens:
                    raise VerbaParseError("I expected a prompt between 'user' and 'and save to'.", line_no=line_no, col=tokens[2].col + len(tokens[2].value), line=lt.raw)
                if prompt_tokens and prompt_tokens[-1].value.lower() == "and":
                    prompt_tokens = prompt_tokens[:-1]
                prompt = " ".join([t.value for t in prompt_tokens]).strip()
                if (prompt.startswith('"') and prompt.endswith('"')) or (prompt.startswith("'") and prompt.endswith("'")):
                    prompt = prompt[1:-1]
                name = _join_name(tokens[to_i + 1 :], line_no=line_no)
                cur.i += 1
                return Ask(span, name, prompt=prompt)

        raise VerbaParseError(
            "I did not understand this ask line. Try 'ask the user \"prompt\" and save to name.'",
            line_no=line_no, col=tokens[0].col, line=lt.raw,
        )

    # file I/O: save/load
    if first_val == "save":
        # save [text] to file called [filename].
        try:
            to_i = tokens_lc.index("to", 1)
        except ValueError:
            raise VerbaParseError("I expected 'to file called' in this save line.", line_no=line_no, col=tokens[0].col + len(tokens[0].value), line=lt.raw)
        if tokens_lc[to_i + 1 : to_i + 3] != ["file", "called"]:
            raise VerbaParseError("A save line must say 'to file called'.", line_no=line_no, col=tokens[to_i].col + len(tokens[to_i].value), line=lt.raw)
        text_expr = parse_expr(tokens[1:to_i], line_no=line_no)
        filename_expr = parse_expr(tokens[to_i + 3 :], line_no=line_no)
        cur.i += 1
        return SaveToFile(span, text_expr, filename_expr)

    if first_val == "load":
        # load file called [filename] into [variable].
        if tokens_lc[1:3] != ["file", "called"]:
            raise VerbaParseError("A load line must start with 'load file called'.", line_no=line_no, col=tokens[0].col + len(tokens[0].value), line=lt.raw)
        if "into" not in tokens_lc[3:]:
            raise VerbaParseError("A load line must say 'into <variable>'.", line_no=line_no, col=tokens[-1].col + len(tokens[-1].value), line=lt.raw)
        into_i = tokens_lc.index("into", 3)
        filename_expr = parse_expr(tokens[3:into_i], line_no=line_no)
        target_name = _join_name(tokens[into_i + 1 :], line_no=line_no)
        cur.i += 1
        return LoadFile(span, filename_expr, target_name)
        
    if first_val == "append":
        try:
            to_i = tokens_lc.index("to")
        except ValueError:
            raise VerbaParseError("I expected 'to' in this append statement.", line_no=line_no, col=tokens[0].col + len(tokens[0].value))
        text_expr = parse_expr(tokens[1:to_i], line_no=line_no)
        # handle assuming "to file called" or just "to filename"
        if tokens_lc[to_i + 1 : to_i + 3] == ["file", "called"]:
            filename_expr = parse_expr(tokens[to_i + 3 :], line_no=line_no)
        else:
            filename_expr = parse_expr(tokens[to_i + 1 :], line_no=line_no)
        cur.i += 1
        return AppendToFile(span, text_expr, filename_expr)
        
    if tokens_lc[:2] == ["delete", "file"]:
        if len(tokens_lc) > 2 and tokens_lc[2] == "called":
            filename_expr = parse_expr(tokens[3:], line_no=line_no)
        else:
            filename_expr = parse_expr(tokens[2:], line_no=line_no)
        cur.i += 1
        return DeleteFile(span, filename_expr)

    if first_val == "fetch":
        if "into" not in tokens_lc:
            raise VerbaParseError("A fetch line must say 'into <variable>'.", line_no=line_no, col=tokens[-1].col + len(tokens[-1].value))
        into_i = tokens_lc.index("into")
        url = parse_expr(tokens[1:into_i], line_no=line_no)
        target = _join_name(tokens[into_i + 1 :], line_no=line_no)
        cur.i += 1
        return FetchUrl(span, url, target)
        
    if first_val in ["free", "delete"]:
        cur.i += 1
        return FreeVar(span, _join_name(tokens[1:], line_no=line_no))

    if first_val == "import":
        # import from file called [filename].
        if tokens_lc[1:4] != ["from", "file", "called"]:
            raise VerbaParseError("An import line must say 'import from file called'.", line_no=line_no, col=tokens[0].col + len(tokens[0].value), line=lt.raw)
        filename_expr = parse_expr(tokens[4:], line_no=line_no)
        cur.i += 1
        return Import(span, filename_expr)

    # list ops: add/remove
    if first_val == "add":
        _require_period(lt, line_no)
        try:
            to_i = tokens_lc.index("to")
        except ValueError:
            raise VerbaParseError("I expected 'to' in this add statement.", line_no=line_no, col=tokens[0].col + len(tokens[0].value), line=lt.raw)
        value = parse_expr(tokens[1:to_i], line_no=line_no)
        list_name = _join_name(tokens[to_i + 1 :], line_no=line_no)
        cur.i += 1
        return ListAdd(span, value, list_name)

    if first_val == "remove":
        try:
            from_i = tokens_lc.index("from")
        except ValueError:
            raise VerbaParseError("I expected 'from' in this remove statement.", line_no=line_no, col=tokens[0].col + len(tokens[0].value), line=lt.raw)
        value = parse_expr(tokens[1:from_i], line_no=line_no)
        list_name = _join_name(tokens[from_i + 1 :], line_no=line_no)
        cur.i += 1
        return ListRemove(span, value, list_name)

    # if ...:
    if first_val == "if":
        cond_tokens = tokens[1:]
        if not cond_tokens:
            raise VerbaParseError("I expected a condition after 'if'.", line_no=line_no, col=tokens[0].col + len(tokens[0].value))
        if term_val != ":":
            raise VerbaParseError(
                "An if line must end with ':'",
                line_no=line_no, col=cond_tokens[-1].col + len(cond_tokens[-1].value), line=lt.raw,
            )
        condition = parse_condition(cond_tokens, line_no=line_no)
        cur.i += 1
        then_body = _parse_block(cur, expected_indent=expected_indent + 4)

        else_body: Optional[list[Stmt]] = None
        if cur.i < len(cur.lines):
            nxt = cur.lines[cur.i]
            nxt_no = cur.i + 1
            nxt_toks = _lc(nxt.tokens)
            is_otherwise = (
                nxt_toks == ["else", ":"] or
                nxt_toks == ["otherwise", ":"]
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
        if end_line.indent != expected_indent or not end_line.tokens or end_line.tokens[0].value.lower() != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, col=end_line.indent, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return If(span, condition, then_body, else_body)

    # repeat N times:
    if first_val == "repeat":
        if term_val != ":" and not (len(tokens_lc) >= 4 and tokens_lc[-3:] == ["do", "the", "following"]):
            raise VerbaParseError("A repeat line must end with ':'.", line_no=line_no, col=tokens[-1].col, line=lt.raw)
        if "times" not in tokens_lc:
            raise VerbaParseError("I expected 'times' in this repeat line.", line_no=line_no, col=tokens[0].col + len(tokens[0].value))
        times_i = tokens_lc.index("times")
        times_expr = parse_expr(tokens[1:times_i], line_no=line_no)
        cur.i += 1
        body = _parse_block(cur, expected_indent=expected_indent + 4)
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or not end_line.tokens or end_line.tokens[0].value.lower() != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, col=end_line.indent, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return Repeat(span, times_expr, body)

# while ...:
    if first_val == "while":
        if term_val != ":":
             raise VerbaParseError("A while line must end with ':'", line_no=line_no, col=tokens[-1].col, line=lt.raw)
        
        cond = parse_condition(tokens[1:], line_no=line_no)
        cur.i += 1
        body = _parse_block(cur, expected_indent=expected_indent + 4)
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or not end_line.tokens or end_line.tokens[0].value.lower() != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, col=end_line.indent, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return While(span, cond, body)

    # for item in list:
    if first_val == "for" and "in" in tokens_lc:
        if term_val != ":":
            raise VerbaParseError("A for line must end with ':'", line_no=line_no, col=tokens[-1].col, line=lt.raw)
        in_i = tokens_lc.index("in")
        item_name = _join_name(tokens[1:in_i], line_no=line_no)
        list_name = _join_name(tokens[in_i + 1 :], line_no=line_no)
        cur.i += 1
        body = _parse_block(cur, expected_indent=expected_indent + 4)
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or not end_line.tokens or end_line.tokens[0].value.lower() != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, col=end_line.indent, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return ForEach(span, item_name, list_name, body)

    if first_val == "class":
        if term_val != ":":
             raise VerbaParseError("Class definition must end with ':'", line_no=line_no, col=tokens[-1].col)
        name = _join_name(tokens[1:], line_no=line_no)
        cur.i += 1
        body = _parse_block(cur, expected_indent=expected_indent + 4)
        methods = {}
        for s in body:
            if isinstance(s, (Define, AsyncDefine)):
                methods[s.name] = s
            elif isinstance(s, Note):
                pass
            else:
                raise VerbaParseError("Only 'define' methods and notes are allowed at the root of a 'class'.", line_no=line_no)
        
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or not end_line.tokens or end_line.tokens[0].value.lower() != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, col=end_line.indent, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return ClassDef(span, name, methods)

    # define function ...
    if first_val in ["define", "async"]:
        if first_val == "define" or (len(tokens_lc) > 1 and tokens_lc[1] == "define"):
            is_async = first_val == "async"
            offset = 1 if not is_async else 2
            signature = tokens[offset:]
            sig_lc = tokens_lc[offset:]
            if term_val != ":":
                raise VerbaParseError("A define line must end with ':'", line_no=line_no, col=tokens[-1].col, line=lt.raw)
            if sig_lc[-2:] == ["as", "follows"]:
                signature = signature[:-2]
                sig_lc = sig_lc[:-2]
            if "needing" in sig_lc:
                needing_i = sig_lc.index("needing")
                name = _join_name(signature[:needing_i], line_no=line_no)
                params = [_join_name(p, line_no=line_no) for p in _split_by_commas(signature[needing_i + 1 :]) if p]
            else:
                name = _join_name(signature, line_no=line_no)
                params = []
            cur.i += 1
            body = _parse_block(cur, expected_indent=expected_indent + 4)
            if cur.i >= len(cur.lines):
                raise VerbaParseError("I expected 'end.'", line_no=line_no)
            end_line = cur.lines[cur.i]
            end_no = cur.i + 1
            if end_line.indent != expected_indent or not end_line.tokens or end_line.tokens[0].value.lower() != "end":
                raise VerbaParseError("I expected 'end.'", line_no=end_no, col=end_line.indent, line=end_line.raw)
            _require_period(end_line, end_no)
            cur.i += 1
            if is_async:
                return AsyncDefine(span, name, params, body)
            return Define(span, name, params, body)

    # give
    if first_val == "give":
        value = parse_expr(tokens[1:], line_no=line_no)
        cur.i += 1
        return GiveBack(span, value)

    # run function ...
    if first_val == "run":
        _require_period(lt, line_no)
        if "with" in tokens_lc:
            with_i = tokens_lc.index("with")
            fn = _join_name(tokens[1:with_i], line_no=line_no)
            args = [parse_expr(a, line_no=line_no) for a in _split_by_commas(tokens[with_i + 1 :])]
        else:
            fn = _join_name(tokens[1:], line_no=line_no)
            args = []
            
        cur.i += 1
        if "." in fn:
            parts = fn.split(".")
            return MethodCall(span, parts[0], parts[1], args)
        return Run(span, fn, args)

# deref ptr = expr.  — write through pointer (concise)
    if first_val == "deref" and "=" in tokens_lc:
        eq_i = tokens_lc.index("=")
        ptr_name = _join_name(tokens[1:eq_i], line_no=line_no)
        value = parse_expr(tokens[eq_i + 1:], line_no=line_no)
        cur.i += 1
        return DerefSet(span, ptr_name, value)

    # serve on port <expr>.
    if tokens_lc[:3] == ["serve", "on", "port"]:
        port_expr = parse_expr(tokens[3:], line_no=line_no)
        cur.i += 1
        return ServeStart(span, port_expr)

    # on route <path> with method <method>:
    if tokens_lc[0] == "on" and "route" in tokens_lc:
        if term_val != ":":
            raise VerbaParseError("An 'on route' block must end with ':'", line_no=line_no, col=tokens[-1].col, line=lt.raw)
        route_i = tokens_lc.index("route")
        if "with" in tokens_lc and "method" in tokens_lc:
            with_i = tokens_lc.index("with")
            method_i = tokens_lc.index("method")
            path_expr = parse_expr(tokens[route_i + 1 : with_i], line_no=line_no)
            method_expr = parse_expr(tokens[method_i + 1 :], line_no=line_no)
        else:
            path_expr = parse_expr(tokens[route_i + 1 :], line_no=line_no)
            method_expr = Literal(span, "GET")
        cur.i += 1
        body = _parse_block(cur, expected_indent=expected_indent + 4)
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or not end_line.tokens or end_line.tokens[0].value.lower() != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, col=end_line.indent, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return ServeRoute(span, path_expr, method_expr, body)

    # redirect to <url> status <code>.
    if tokens_lc[:2] == ["redirect", "to"]:
        status_i = tokens_lc.index("status") if "status" in tokens_lc else -1
        url_end = status_i if status_i != -1 else len(tokens)
        url_expr = parse_expr(tokens[2:url_end], line_no=line_no)
        status_expr = parse_expr(tokens[status_i + 1:], line_no=line_no) if status_i != -1 else Literal(span, 302)
        cur.i += 1
        return ServeRedirect(span, url_expr, status_expr)

    # respond with <part>, <part>, ... status <code> type <mime>.
    if tokens_lc[0] == "respond" and "with" in tokens_lc:
        with_i = tokens_lc.index("with")
        # find optional 'status' and 'type' keywords (only outside quoted strings)
        status_i = -1
        type_i   = -1
        for _ki, _kt in enumerate(tokens_lc):
            if _ki <= with_i:
                continue
            if _kt == "status" and status_i == -1:
                # make sure it's not inside a string token
                if not (tokens[_ki].value.startswith('"') or tokens[_ki].value.startswith("'")):
                    status_i = _ki
            elif _kt == "type" and type_i == -1:
                if not (tokens[_ki].value.startswith('"') or tokens[_ki].value.startswith("'")):
                    type_i = _ki
        body_end = min(i for i in [status_i, type_i, len(tokens)] if i > with_i)
        # comma-split the body parts
        body_tokens = tokens[with_i + 1 : body_end]
        body_parts = [parse_expr(p, line_no=line_no) for p in _split_by_commas(body_tokens) if p]
        if not body_parts:
            body_parts = [Literal(span, "")]
        status_expr = parse_expr(tokens[status_i + 1 : (type_i if type_i != -1 and type_i > status_i else len(tokens))], line_no=line_no) if status_i != -1 else Literal(span, 200)
        mime_expr   = parse_expr(tokens[type_i + 1 :], line_no=line_no) if type_i != -1 else Literal(span, "text/html")
        cur.i += 1
        return ServeRespond(span, body_parts, status_expr, mime_expr)

    # try:
    if tokens_lc == ["try"]:
        cur.i += 1
        try_body = _parse_block(cur, expected_indent=expected_indent + 4)
        catch_body: Optional[list[Stmt]] = None
        error_name: Optional[str] = None

        if cur.i < len(cur.lines):
            nxt = cur.lines[cur.i]
            nxt_no = cur.i + 1
            nxt_lc = _lc(nxt.tokens)
            if nxt.indent == expected_indent and len(nxt_lc) >= 2 and nxt_lc[:2] == ["on", "error"]:
                _require_period(nxt, nxt_no)
                # on error saving to <name>:
                if "saving" in nxt_lc and "to" in nxt_lc:
                    sav_i = nxt_lc.index("saving")
                    to_i = nxt_lc.index("to", sav_i)
                    # tokens up to the colon terminator (already stripped by _require_period check)
                    end_tok = nxt_lc.index(":") if ":" in nxt_lc else len(nxt_lc)
                    error_name = _join_name(nxt.tokens[to_i + 1 : end_tok], line_no=nxt_no)
                elif nxt_lc[-1] != ":":
                    raise VerbaParseError(
                        "I expected 'on error:' or 'on error saving to name:'",
                        line_no=nxt_no, col=nxt.tokens[0].col, line=nxt.raw
                    )
                cur.i += 1
                catch_body = _parse_block(cur, expected_indent=expected_indent + 4)
        
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or not end_line.tokens or end_line.tokens[0].value.lower() != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, col=end_line.indent, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return TryBlock(span, try_body, catch_body, error_name)

    raise VerbaParseError(
        f"I did not understand this line. Did you mean to use say, let, set, if, repeat, keep, define, run, or ask?",
        line_no=line_no,
        col=tokens[0].col,
        line=lt.raw,
    )


def _split_by_commas(tokens: list[Token]) -> list[list[Token]]:
    if not any(t.value == "," for t in tokens):
        return [tokens] if tokens else []

    groups: list[list[Token]] = []
    cur: list[Token] = []
    for t in tokens:
        if t.value == ",":
            if cur:
                groups.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        groups.append(cur)
    return groups


def _parse_say_value(tokens: list[Token], *, line_no: int) -> object:
    if not tokens:
        raise VerbaParseError("I expected something to say.", line_no=line_no)
    return parse_expr(tokens, line_no=line_no)
