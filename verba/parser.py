from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .ast import (
    Assert,
    Ask,
    Match,
    Help,
    MatchBranch,
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
    ForEachIndexed,
    ForRange,
    GiveBack,
    If,
    Increase,
    EnumDef,
    Let,
    LetResultOfRun,
    Literal,
    ListAdd,
    ListItemGet,
    ListLiteral,
    ListRemove,
    ListSlice,
    ListSort,
    ListComprehension,
    MapLiteral,
    MapComprehension,
    WithStmt,
    ListLength,
    MatchPattern,
    ValuePattern,
    VariablePattern,
    ListPattern,
    MapPattern,
    BoolExprFromExpr,
    LoadFile,
    MultiAssign,
    Note,
    Repeat,
    Run,
    SaveToFile,
    Say,
    SetVar,
    Span,
    Stmt,
    Test,
    Unless,
    VarRef,
    While,
    TryBlock,
    Import,
    AppendToFile,
    DeleteFile,
    FetchUrl,
    FreeVar,
    Test,
    Yield,
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
    Break,
    Continue,
    Raise,
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
    (["not", "in"], "!in"),
    (["in"], "in"),
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
    (["*", "*"], "**"),
    (["**"], "**"),
    (["*"], "*"),
    (["divided", "by"], "/"),
    (["/", "/"], "//"),
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

    # the result of running <fn> [with <args>]
    if tl == "the" and i + 3 < len(tokens) and tokens_lc[i+1] == "result" and tokens_lc[i+2] == "of" and tokens_lc[i+3] == "running":
        # Check for 'with'
        if "with" in tokens_lc[i+4:]:
            with_i = i + 4 + tokens_lc[i+4:].index("with")
            fn = _join_name(tokens[i+4:with_i], line_no=span.line_no)
            rem = tokens[with_i+1:]
            parts = _split_by_commas(rem)
            args = []
            kwargs = {}
            for p in parts:
                if not p: continue
                # check for k=v
                eq_idx = -1
                for idx in range(len(p)):
                    if p[idx].value == "=":
                        eq_idx = idx
                        break
                if eq_idx != -1:
                    k = p[:eq_idx][-1].value.lower()
                    v = parse_expr(p[eq_idx+1:], line_no=span.line_no)
                    kwargs[k] = v
                else:
                    args.append(parse_expr(p, line_no=span.line_no))
        else:
            fn = _join_name(tokens[i+4:], line_no=span.line_no)
            args, kwargs = [], {}
        
        # Build Run node
        if "." in fn:
            p = fn.split(".")
            return MethodCall(span, p[0], p[1], args, kwargs), len(tokens)
        return Run(span, fn, args, kwargs), len(tokens)

    # length of <name>
    if tl == "length" and i + 2 <= len(tokens) and tokens_lc[i + 1] == "of":
        return ListLength(span, tokens[i + 2].value.lower()), i + 3

    num = _parse_number(t.value)
    if num is not None:
        return Literal(span, num), i + 1

    # unary minus: -<number> or -<var>
    if t.value == "-" and i + 1 < len(tokens):
        inner, next_i = _parse_atom(tokens, tokens_lc, i + 1, span=span)
        return BinaryOp(span, "*", Literal(span, -1), inner), next_i

    if (t.value.startswith('"') and t.value.endswith('"')) or (t.value.startswith("'") and t.value.endswith("'")):
        raw_str = t.value[1:-1].replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
        # Check for {var} interpolation ONLY if double-quoted
        if t.value.startswith('"') and '{' in raw_str:
            return _parse_interpolated(raw_str, span), i + 1
        return Literal(span, raw_str), i + 1

    if t.value == "(":
        # find matching )
        depth = 0
        end_idx = -1
        for j in range(i, len(tokens)):
            if tokens[j].value == "(": depth += 1
            elif tokens[j].value == ")":
                depth -= 1
                if depth == 0:
                    end_idx = j
                    break
        if end_idx == -1:
            raise VerbaParseError("I expected a closing parenthesis ')'.", line_no=span.line_no)
        # Parse the inside as an expression
        inner = parse_expr(tokens[i+1 : end_idx], line_no=span.line_no)
        return inner, end_idx + 1

    if "." in t.value and t.value.count(".") >= 1 and not t.value.startswith('"') and not t.value.startswith("'"):
        # Check that it's not JUST a dot or a decimal number
        # Already handled numbers earlier
        return ObjectPropGet(span, t.value[:t.value.index(".")].lower(),
                             t.value[t.value.index(".")+1:].lower()), i + 1
                             
    if t.value == "[":
        # find matching ]
        depth = 0
        end_idx = -1
        for j in range(i, len(tokens)):
            if tokens[j].value == "[": depth += 1
            elif tokens[j].value == "]":
                depth -= 1
                if depth == 0:
                    end_idx = j
                    break
        if end_idx == -1:
            raise VerbaParseError("I expected a closing bracket ']'.", line_no=span.line_no)
        parts = _split_by_commas(tokens[i+1 : end_idx])
        values = [parse_expr(p, line_no=span.line_no) for p in parts if p]
        return ListLiteral(span, values), end_idx + 1

    if t.value == "{":
        # find matching }
        depth = 0
        end_idx = -1
        for j in range(i, len(tokens)):
            if tokens[j].value == "{": depth += 1
            elif tokens[j].value == "}":
                depth -= 1
                if depth == 0:
                    end_idx = j
                    break
        if end_idx == -1:
            raise VerbaParseError("I expected a closing brace '}'.", line_no=span.line_no)
        parts = _split_by_commas(tokens[i+1 : end_idx])
        pairs = []
        for p in parts:
            if not p: continue
            colon_i = -1
            for k_idx in range(len(p)):
                if p[k_idx].value == ":":
                    colon_i = k_idx
                    break
            if colon_i == -1:
                raise VerbaParseError("Map item must be 'key: value'.", line_no=span.line_no)
            k_expr = parse_expr(p[:colon_i], line_no=span.line_no)
            v_expr = parse_expr(p[colon_i+1 :], line_no=span.line_no)
            pairs.append((k_expr, v_expr))
        return MapLiteral(span, pairs), end_idx + 1

    # a list of <expr>, <expr>, ...
    if tl == "a" and i + 2 < len(tokens) and tokens_lc[i+1] == "list" and tokens_lc[i+2] == "of":
        # Handle "a list of a, b, c."
        rem = tokens[i+3:]
        parts = _split_by_commas(rem)
        values = [parse_expr(p, line_no=span.line_no) for p in parts if p]
        return ListLiteral(span, values), len(tokens)

    # a map of key1: val1, key2: val2, ...
    if tl == "a" and i + 2 < len(tokens) and tokens_lc[i+1] == "map" and tokens_lc[i+2] == "of":
        # Handle "a map of k1: v1, k2: v2."
        rem = tokens[i+3:]
        parts = _split_by_commas(rem)
        pairs = []
        for p in parts:
            if not p: continue
            # Find colon
            colon_idx = -1
            for k in range(len(p)):
                if p[k].value == ":":
                    colon_idx = k
                    break
            if colon_idx == -1:
                raise VerbaParseError("Map item must be in the format 'key: value'.", line_no=span.line_no)
            k_expr = parse_expr(p[:colon_idx], line_no=span.line_no)
            v_expr = parse_expr(p[colon_idx+1:], line_no=span.line_no)
            pairs.append((k_expr, v_expr))
        return MapLiteral(span, pairs), len(tokens)

    # Word literals are bare single tokens (e.g. hello, Alice). Multi-word text uses "quote".
    return VarRef(span, _join_name([t])), i + 1


def _parse_interpolated(s: str, span: Span) -> object:
    """Turn 'Hello {name}!' into StringConcat([Literal('Hello '), VarRef('name'), Literal('!')])."""
    parts = []
    buf = ""
    i = 0
    while i < len(s):
        if s[i:i+2] == '{{':
            buf += '{'
            i += 2
        elif s[i:i+2] == '}}':
            buf += '}'
            i += 2
        elif s[i] == '{':
            if buf:
                parts.append(Literal(span, buf))
                buf = ""
            try:
                j = s.index('}', i + 1)
            except ValueError:
                raise VerbaParseError("Found an unclosed '{' in a string. To write a literal brace, use '{{'.", line_no=span.line_no)
            var = s[i+1:j].strip()
            if '.' in var:
                dot = var.index('.')
                parts.append(ObjectPropGet(span, var[:dot], var[dot+1:]))
            else:
                parts.append(VarRef(span, var))
            i = j + 1
        else:
            buf += s[i]
            i += 1
    if buf:
        parts.append(Literal(span, buf))
    if len(parts) == 1:
        return parts[0]
    return StringConcat(span, parts)


def _scan_math_op(tokens_lc: list[str], i: int) -> tuple[Optional[str], int]:
    for phrase, op in _MATH_OPS:
        if _try_match(tokens_lc, i, phrase):
            return op, i + len(phrase)
    return None, i


def _precedence(op: str) -> int:
    return {"**": 3, "*": 2, "/": 2, "//": 2, "%": 2, "+": 1, "-": 1}.get(op, 0)


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
            parts = _split_by_commas(tokens[with_i + 1 :])
            args = []
            kwargs = {}
            for p in parts:
                if not p: continue
                # check for k=v
                eq_idx = -1
                for idx in range(len(p)):
                    if p[idx].value == "=":
                        eq_idx = idx
                        break
                if eq_idx != -1:
                    k = p[:eq_idx][-1].value.lower()
                    v = parse_expr(p[eq_idx+1:], line_no=line_no)
                    kwargs[k] = v
                else:
                    args.append(parse_expr(p, line_no=line_no))
            return ObjectNew(span, class_name, args, kwargs)
        class_name = _join_name(tokens[1:], line_no=line_no)
        return ObjectNew(span, class_name, [], {})

    # Detect comprehension: result_expr for var in list_expr [if cond_expr]
    if "for" in tokens_lc and "in" in tokens_lc:
        for_i = tokens_lc.index("for")
        in_i = tokens_lc.index("in")
        if in_i > for_i + 1:
            res_toks = tokens[:for_i]
            var_name = tokens[for_i + 1 : in_i][-1].value.lower() # last word before 'in'
            # find 'if' for optional condition
            if "if" in tokens_lc[in_i + 1:]:
                if_i = tokens_lc.index("if", in_i + 1)
                list_toks = tokens[in_i + 1 : if_i]
                cond_toks = tokens[if_i + 1 :]
                cond_expr = parse_condition(cond_toks, line_no=line_no)
            else:
                list_toks = tokens[in_i + 1 :]
                cond_expr = None
            
            list_expr = parse_expr(list_toks, line_no=line_no)
            
            # Check if it's a map comprehension: has a colon in results
            colon_idx = -1
            for idx in range(len(res_toks)):
                if res_toks[idx].value == ":":
                    colon_idx = idx
                    break
            
            if colon_idx != -1:
                # k: v for k, v in list
                # handle k, v unpacking: "k, v" before "in"
                # wait, var_name was tokens[for_i+1:in_i][-1]
                # let's be more robust: "k, v"
                vars_before_in = [t.value.lower() for t in tokens[for_i+1:in_i] if t.value != ","]
                if len(vars_before_in) >= 2:
                    k_var = vars_before_in[0]
                    v_var = vars_before_in[1]
                else:
                    k_var = vars_before_in[0]
                    v_var = k_var # fallback
                
                k_expr = parse_expr(res_toks[:colon_idx], line_no=line_no)
                v_expr = parse_expr(res_toks[colon_idx+1:], line_no=line_no)
                return MapComprehension(span, k_expr, v_expr, k_var, v_var, list_expr, cond_expr)
            else:
                res_expr = parse_expr(res_toks, line_no=line_no)
                return ListComprehension(span, res_expr, var_name, list_expr, cond_expr)

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

        # No comparison found. Fallback: treat the whole term as a plain expression 
        # (e.g. 'if the result of running...')
        end = j
        while end < len(tokens_lc) and tokens_lc[end] not in ("and", "or"):
             end += 1
        
        chunk = tokens[j:end]
        if not chunk:
            raise VerbaParseError("I expected a condition here.", line_no=line_no)
        
        expr = parse_expr(chunk, line_no=line_no)
        return BoolExprFromExpr(span, expr), end

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
    decorators: list[str] = []
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

        if lt.tokens[0].value.startswith("@"):
            dec_name = lt.tokens[0].value[1:]
            if dec_name:
                decorators.append(dec_name)
            cur.i += 1
            continue

        stmt = _parse_statement(cur, expected_indent=expected_indent)
        if stmt is not None:
            if decorators and isinstance(stmt, (Define, AsyncDefine)):
                # Return a new instance with decorators attached
                from dataclasses import replace
                stmt = replace(stmt, decorators=decorators)
                decorators = []
            elif decorators:
                raise VerbaParseError("Decorators can only be applied to 'define' statements.", line_no=line_no, col=lt.tokens[0].col, line=lt.raw)
            out.append(stmt)
        else:
            # If _parse_statement returned None but didn't advance, it could loop.
            # However, the updated _parse_statement should always advance or raise.
            # We add a safety increment here just in case.
            if cur.lines[cur.i] == lt:
                cur.i += 1
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

    # Comments / notes (don't require period, but handle them if present)
    if first_val_orig == "note":
        cur.i += 1
        content = " ".join([t.value for t in original_tokens[1:]]).strip()
        if content.endswith("."):
            content = content[:-1].strip()
        if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
            content = content[1:-1]
        return Note(span, content)

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
        "await", "deref", "serve", "on", "respond", "stop", "skip", "assert", "match", "raise"
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
        raw_name = " ".join(t.value for t in tokens[:by_i])
        op = tokens_lc[by_i]
        value = parse_expr(tokens[by_i + 1 :], line_no=line_no)
        cur.i += 1
        if "." in raw_name:
            # obj.prop += val  =>  ObjectPropSet(obj, prop, current op val)
            dot_i = raw_name.index(".")
            obj_n = raw_name[:dot_i].lower()
            prop_n = raw_name[dot_i + 1:].lower()
            current = ObjectPropGet(span, obj_n, prop_n)
            if op == "+=": return ObjectPropSet(span, obj_n, prop_n, BinaryOp(span, "+", current, value))
            if op == "-=": return ObjectPropSet(span, obj_n, prop_n, BinaryOp(span, "-", current, value))
            if op == "*=": return ObjectPropSet(span, obj_n, prop_n, BinaryOp(span, "*", current, value))
            if op == "/=": return ObjectPropSet(span, obj_n, prop_n, BinaryOp(span, "/", current, value))
        else:
            name = _join_name(tokens[:by_i], line_no=line_no)
            if op == "+=": return Increase(span, name, value)
            if op == "-=": return Decrease(span, name, value)
            if op == "*=": return SetVar(span, name, BinaryOp(span, "*", VarRef(span, name), value))
            if op == "/=": return SetVar(span, name, BinaryOp(span, "/", VarRef(span, name), value))

    # Check for concise definition: x = 5.  OR  a, b = ...
    # First detect a multi-assign: comma-separated names left of '='
    eq_i = tokens_lc.index("=") if "=" in tokens_lc else -1
    
    # Detect multi-assign: "a , b = ..."
    if eq_i > 1 and not is_keyword_stmt:
        lhs_tokens = tokens[:eq_i]
        lhs_lc = tokens_lc[:eq_i]
        # Check if lhs is a comma-separated list of names (no keywords)
        if "," in lhs_lc:
            name_groups = _split_by_commas(lhs_tokens)
            if all(len(g) == 1 for g in name_groups):
                names = [g[0].value.lower() for g in name_groups]
                rhs_tokens = tokens[eq_i + 1:]
                rhs_lc = tokens_lc[eq_i + 1:]
                # Support: names = the result of running func with args
                if len(rhs_lc) >= 4 and rhs_lc[:4] == ["the", "result", "of", "running"]:
                    if "with" in rhs_lc:
                        with_i = rhs_lc.index("with")
                        fn = _join_name(rhs_tokens[4:with_i], line_no=line_no)
                        args = [parse_expr(a, line_no=line_no) for a in _split_by_commas(rhs_tokens[with_i + 1:])]
                    else:
                        fn = _join_name(rhs_tokens[4:], line_no=line_no)
                        args = []
                    cur.i += 1
                    if "." in fn:
                        parts = fn.split(".")
                        call_expr = LetResultOfMethod(span, "__multi__", parts[0], parts[1], args)
                        # Wrap as MultiAssign — runtime will unpack
                        return MultiAssign(span, names, Literal(span, call_expr))
                    return MultiAssign(span, names, Literal(span, LetResultOfRun(span, "__multi__", fn, args)))
                # Fallback: rhs is a plain expr (list)
                rhs_expr = parse_expr(rhs_tokens, line_no=line_no)
                cur.i += 1
                return MultiAssign(span, names, rhs_expr)
        
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
            
        if len(val_tc) >= 3 and val_tc[:3] == ["a", "list", "of"]:
            items = [parse_expr(item, line_no=line_no) for item in _split_by_commas(tokens[eq_i + 4:])]
            cur.i += 1
            value = Literal(span, items)
            if "." in name:
                parts = name.split(".")
                return ObjectPropSet(span, parts[0], parts[1], value)
            return Let(span, name, value, forced_type="list")

        if len(val_tc) >= 3 and val_tc[:3] == ["a", "map", "of"]:
            pair_tokens = _split_by_commas(tokens[eq_i + 4:])
            pairs = []
            for pt in pair_tokens:
                # each group should be: key : value
                pt_lc = [t.value for t in pt]
                if ":" in pt_lc:
                    colon_i = pt_lc.index(":")
                    key = pt[0].value.strip('"\'')
                    val_expr = parse_expr(pt[colon_i + 1:], line_no=line_no)
                    pairs.append((key, val_expr))
            cur.i += 1
            map_val = MapLiteral(span, pairs)
            if "." in name:
                parts = name.split(".")
                return ObjectPropSet(span, parts[0], ".".join(parts[1:]), map_val)
            return Let(span, name, map_val)
            
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
        # import from file called [filename] [as alias].
        if tokens_lc[1:4] != ["from", "file", "called"]:
            raise VerbaParseError("An import line must say 'import from file called'.", line_no=line_no, col=tokens[0].col + len(tokens[0].value), line=lt.raw)
        
        alias = None
        if "as" in tokens_lc:
            as_i = tokens_lc.index("as")
            filename_expr = parse_expr(tokens[4:as_i], line_no=line_no)
            alias = _join_name(tokens[as_i+1:], line_no=line_no)
        else:
            filename_expr = parse_expr(tokens[4:], line_no=line_no)
            
        cur.i += 1
        return Import(span, filename_expr, alias)

    # sort <list> [descending].
    if first_val == "sort":
        descending = "descending" in tokens_lc
        list_name = _join_name([t for t in tokens[1:] if t.value.lower() not in ("descending",)], line_no=line_no)
        cur.i += 1
        return ListSort(span, list_name, descending)

    # first <n> of <list> into <target>. / last <n> of <list> into <target>.
    if first_val in ("first", "last") and "of" in tokens_lc and "into" in tokens_lc:
        from_end = first_val == "last"
        of_i   = tokens_lc.index("of")
        into_i = tokens_lc.index("into")
        count_expr = parse_expr(tokens[1:of_i], line_no=line_no)
        list_name  = _join_name(tokens[of_i + 1 : into_i], line_no=line_no)
        target     = _join_name(tokens[into_i + 1 :], line_no=line_no)
        cur.i += 1
        return ListSlice(span, target, list_name, count_expr, from_end)

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
        else_if_consumed_end = False
        if cur.i < len(cur.lines):
            nxt = cur.lines[cur.i]
            nxt_no = cur.i + 1
            nxt_toks = _lc(nxt.tokens)
            is_otherwise = (
                nxt_toks == ["else", ":"] or
                nxt_toks == ["otherwise", ":"]
            )
            is_else_if = (
                nxt.indent == expected_indent and
                len(nxt_toks) >= 3 and
                nxt_toks[0] in ("else", "otherwise") and
                nxt_toks[1] == "if"
            )
            if nxt.indent == expected_indent and is_else_if:
                # Rewrite "else if <cond>:" -> "if <cond>:" and parse as a single If stmt.
                # The nested If will consume its own end., so we skip the outer end. check.
                from .tokenize import LineTokens
                fake_lt = LineTokens(indent=nxt.indent, raw=nxt.raw, tokens=nxt.tokens[1:])
                cur.lines[cur.i] = fake_lt
                nested_if = _parse_statement(cur, expected_indent=expected_indent)
                else_body = [nested_if] if nested_if is not None else []
                else_if_consumed_end = True
            elif nxt.indent == expected_indent and is_otherwise:
                _require_period(nxt, nxt_no)
                cur.i += 1
                else_body = _parse_block(cur, expected_indent=expected_indent + 4)

        # expect end. (only when else-if didn't already consume it)
        if not else_if_consumed_end:
            if cur.i >= len(cur.lines):
                raise VerbaParseError("I expected 'end.'", line_no=line_no)
            end_line = cur.lines[cur.i]
            end_no = cur.i + 1
            if end_line.indent != expected_indent or not end_line.tokens or end_line.tokens[0].value.lower() != "end":
                raise VerbaParseError("I expected 'end.'", line_no=end_no, col=end_line.indent, line=end_line.raw)
            _require_period(end_line, end_no)
            cur.i += 1
        return If(span, condition, then_body, else_body)

    # unless cond:
    if first_val == "unless":
        cond_tokens = tokens[1:]
        if not cond_tokens:
            raise VerbaParseError("I expected a condition after 'unless'.", line_no=line_no, col=tokens[0].col + len(tokens[0].value))
        if term_val != ":":
            raise VerbaParseError(
                "An unless line must end with ':'",
                line_no=line_no, col=cond_tokens[-1].col + len(cond_tokens[-1].value), line=lt.raw,
            )
        condition = parse_condition(cond_tokens, line_no=line_no)
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
        return Unless(span, condition, body)

    # repeat N times:
    if first_val == "repeat":
        if term_val != ":" and not (len(tokens_lc) >= 4 and tokens_lc[-3:] == ["do", "the", "following"]):
            raise VerbaParseError("A repeat line must end with ':'.", line_no=line_no, col=tokens[-1].col, line=lt.raw)
        if "times" not in tokens_lc:
            raise VerbaParseError("I expected 'times' in this repeat line.", line_no=line_no, col=tokens[0].col + len(tokens[0].value))
        times_i = tokens_lc.index("times")
        times_expr = parse_expr(tokens[1:times_i], line_no=line_no)
        # optional: repeat N times with i:
        index_name = None
        if "with" in tokens_lc[times_i:]:
            with_i = tokens_lc.index("with", times_i)
            index_name = _join_name(tokens[with_i + 1:], line_no=line_no)
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
        return Repeat(span, times_expr, body, index_name)

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

    # for i from <start> to <end> [step <step>]:
    if first_val == "for" and "from" in tokens_lc and "to" in tokens_lc:
        if term_val != ":":
            raise VerbaParseError("A for line must end with ':'", line_no=line_no, col=tokens[-1].col, line=lt.raw)
        var_name  = _join_name(tokens[1:tokens_lc.index("from")], line_no=line_no)
        from_i    = tokens_lc.index("from")
        to_i      = tokens_lc.index("to")
        step_i    = tokens_lc.index("step") if "step" in tokens_lc else -1
        start_expr = parse_expr(tokens[from_i + 1 : to_i], line_no=line_no)
        end_expr   = parse_expr(tokens[to_i + 1 : step_i if step_i != -1 else len(tokens)], line_no=line_no)
        step_expr  = parse_expr(tokens[step_i + 1 :], line_no=line_no) if step_i != -1 else None
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
        return ForRange(span, var_name, start_expr, end_expr, step_expr, body)

    # for item in list:  /  for item at index in list:
    if first_val == "for" and "in" in tokens_lc:
        if term_val != ":":
            raise VerbaParseError("A for line must end with ':'", line_no=line_no, col=tokens[-1].col, line=lt.raw)
        in_i = tokens_lc.index("in")
        # for item at index in list:
        if "at" in tokens_lc[:in_i]:
            at_i = tokens_lc.index("at")
            item_name = _join_name(tokens[1:at_i], line_no=line_no)
            index_name = _join_name(tokens[at_i + 1:in_i], line_no=line_no)
            list_name = _join_name(tokens[in_i + 1:], line_no=line_no)
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
            return ForEachIndexed(span, item_name, index_name, list_name, body)
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
        # class Name: or class Name extends Parent:
        parent_name = None
        if "extends" in tokens_lc:
            ext_i = tokens_lc.index("extends")
            name = _join_name(tokens[1:ext_i], line_no=line_no)
            parent_name = _join_name(tokens[ext_i + 1:], line_no=line_no)
        else:
            name = _join_name(tokens[1:], line_no=line_no)
        cur.i += 1
        body = _parse_block(cur, expected_indent=expected_indent + 4)
        doc = None
        if body and isinstance(body[0], Note):
            doc = body[0].value

        methods = {}
        fields: dict = {}
        for s in body:
            if isinstance(s, (Define, AsyncDefine)):
                methods[s.name] = s
            elif isinstance(s, Note):
                pass
            elif isinstance(s, Let):
                # Class-level field: count = 0.
                fields[s.name] = s.value
            else:
                raise VerbaParseError("Only 'define' methods, field assignments, and notes are allowed at the root of a 'class'.", line_no=line_no)

        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or not end_line.tokens or end_line.tokens[0].value.lower() != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, col=end_line.indent, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return ClassDef(span, name, methods, parent_name, fields, doc)

    # define function ...
    if first_val in ["define", "async"]:
        is_async = first_val == "async"
        doc = None
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
            raw_params = _split_by_commas(signature[needing_i + 1:])
            params = []
            defaults = {}
            for rp in raw_params:
                if not rp:
                    continue
                rp_lc = [t.value for t in rp]
                if "=" in rp_lc:
                    eq_i = rp_lc.index("=")
                    pname = _join_name(rp[:eq_i], line_no=line_no)
                    default_val = parse_expr(rp[eq_i + 1:], line_no=line_no)
                    params.append(pname)
                    defaults[pname] = default_val
                else:
                    params.append(_join_name(rp, line_no=line_no))
        else:
            name = _join_name(signature, line_no=line_no)
            params = []
            defaults = {}
        cur.i += 1
        body = _parse_block(cur, expected_indent=expected_indent + 4)
        doc = [s.value for s in body if isinstance(s, Note)][0] if body and isinstance(body[0], Note) else None
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
        return Define(span, name, params, body, defaults, doc)

    # match <expr>:
    if first_val == "match":
        if term_val != ":":
            raise VerbaParseError("A match line must end with ':'", line_no=line_no, col=tokens[-1].col, line=lt.raw)
        subject = parse_expr(tokens[1:], line_no=line_no)
        cur.i += 1
        branches: list[MatchBranch] = []
        else_body = None
        inner_indent = expected_indent + 4
        while cur.i < len(cur.lines):
            wl = cur.lines[cur.i]
            wl_no = cur.i + 1
            if not wl.tokens:
                cur.i += 1
                continue
            if wl.indent < inner_indent:
                break
            wl_lc = _lc(wl.tokens)
            _require_period(wl, wl_no)
            if wl_lc[0] in ("when", "on"):
                # when/on <pattern>: ...
                if wl.tokens[-1].value != ":":
                    raise VerbaParseError("A match branch must end with ':'", line_no=wl_no, line=wl.raw)
                pattern = _parse_pattern(wl.tokens[1:-1], line_no=wl_no)
                cur.i += 1
                branch_body = _parse_block(cur, expected_indent=inner_indent + 4)
                branches.append(MatchBranch(pattern, branch_body))
            elif wl_lc[0] in ("else", "otherwise") and wl_lc[-1] == ":":
                cur.i += 1
                else_body = _parse_block(cur, expected_indent=inner_indent + 4)
            else:
                break
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or not end_line.tokens or end_line.tokens[0].value.lower() != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, col=end_line.indent, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return Match(span, subject, branches, else_body)

    # with <expr> as <var>:
    if first_val == "with":
        if term_val != ":":
             raise VerbaParseError("A 'with' line must end with ':'", line_no=line_no)
        if "as" not in tokens_lc:
             raise VerbaParseError("A 'with' line must say 'as <variable>'.", line_no=line_no)
        as_i = tokens_lc.index("as")
        expr_parts = tokens[1:as_i]
        var_name = _join_name(tokens[as_i+1:], line_no=line_no)
        expr = parse_expr(expr_parts, line_no=line_no)
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
        return WithStmt(span, expr, var_name, body)

    # test "math addition": assert 1 + 1 == 2. end.
    if first_val == "test":
        if term_val != ":":
             raise VerbaParseError("A test line must end with ':'", line_no=line_no)
        name = tokens[1].value.strip('"\'')
        cur.i += 1
        body = _parse_block(cur, expected_indent=expected_indent+4)
        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or not end_line.tokens or end_line.tokens[0].value.lower() != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, col=end_line.indent, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return Test(span, name, body)

    # assert <condition> [saying <message>].
    if first_val == "assert":
        msg = None
        cond_end = len(tokens)
        if "saying" in tokens_lc:
            saying_i = tokens_lc.index("saying")
            msg_tok = tokens[saying_i + 1]
            msg = msg_tok.value.strip('"\'')
            cond_end = saying_i
        condition = parse_condition(tokens[1:cond_end], line_no=line_no)
        cur.i += 1
        return Assert(span, condition, msg)

    # raise <message>.
    if first_val == "raise":
        msg_expr = parse_expr(tokens[1:], line_no=line_no)
        cur.i += 1
        return Raise(span, msg_expr)

    # stop (break)
    if first_val == "stop":
        cur.i += 1
        return Break(span)

    # skip (continue)
    if first_val == "skip":
        cur.i += 1
        return Continue(span)

    # give
    if first_val == "give":
        # Support multi-value: give 1, 100.
        parts = _split_by_commas(tokens[1:])
        if len(parts) == 1:
            values = [parse_expr(parts[0], line_no=line_no)]
        else:
            values = [parse_expr(p, line_no=line_no) for p in parts if p]
        cur.i += 1
        return GiveBack(span, values)

    # help [topic].
    if first_val == "help":
        _require_period(lt, line_no)
        topic = None
        if len(tokens) > 1:
             topic = " ".join([t.value for t in tokens[1:]]).strip(".")
        cur.i += 1
        return Help(span, topic)

    # run function ...
    if first_val == "run":
        _require_period(lt, line_no)
        if "with" in tokens_lc:
            with_i = tokens_lc.index("with")
            fn = _join_name(tokens[1:with_i], line_no=line_no)
            parts = _split_by_commas(tokens[with_i + 1 :])
            args = []
            kwargs = {}
            for p in parts:
                if not p: continue
                # check for k=v
                eq_idx = -1
                for idx in range(len(p)):
                    if p[idx].value == "=":
                        eq_idx = idx
                        break
                if eq_idx != -1:
                    k = p[:eq_idx][-1].value.lower()
                    v = parse_expr(p[eq_idx+1:], line_no=line_no)
                    kwargs[k] = v
                else:
                    args.append(parse_expr(p, line_no=line_no))
        else:
            fn = _join_name(tokens[1:], line_no=line_no)
            args, kwargs = [], {}
            
        cur.i += 1
        if "." in fn:
            parts = fn.split(".")
            return MethodCall(span, parts[0], parts[1], args, kwargs)
        return Run(span, fn, args, kwargs)

# deref ptr = expr.  — write through pointer (concise)
    if first_val == "deref" and "=" in tokens_lc:
        eq_i = tokens_lc.index("=")
        ptr_name = _join_name(tokens[1:eq_i], line_no=line_no)
        value = parse_expr(tokens[eq_i + 1:], line_no=line_no)
        cur.i += 1
        return DerefSet(span, ptr_name, value)

    # enum <name>: ... end.
    if first_val == "enum":
        name = _join_name(tokens[1:], line_no=line_no)
        cur.i += 1
        members = []
        if term_val == ":":
            inner_indent = expected_indent + 4
            while cur.i < len(cur.lines):
                cur_line = cur.lines[cur.i]
                cur_no = cur.i + 1
                if not cur_line.tokens:
                    cur.i += 1
                    continue
                if cur_line.indent < inner_indent:
                    break
                if cur_line.tokens[0].value.lower() == "end":
                    break
                
                # Each line can be "A, B, C."
                line_tokens = cur_line.tokens
                # strip . if present
                if line_tokens[-1].value == ".":
                     line_tokens = line_tokens[:-1]
                
                if line_tokens:
                    parts = _split_by_commas(line_tokens)
                    for p in parts:
                        if p:
                            members.append(_join_name(p, line_no=cur_no))
                cur.i += 1
            
            if cur.i >= len(cur.lines) or not cur.lines[cur.i].tokens or cur.lines[cur.i].tokens[0].value.lower() != "end":
                raise VerbaParseError("I expected 'end.' for this enum block.", line_no=line_no)
            _require_period(cur.lines[cur.i], cur.i + 1)
            cur.i += 1
        return EnumDef(span, name, members)

    # help <name>.
    if first_val == "help":
        target = _join_name(tokens[1:], line_no=line_no)
        cur.i += 1
        return Help(span, target)

    # yield <expr>.
    if first_val == "yield":
        val = parse_expr(tokens[1:], line_no=line_no)
        cur.i += 1
        return Yield(span, val)

    # serve on port <expr>[: ... end].
    if tokens_lc[:3] == ["serve", "on", "port"]:
        port_expr = parse_expr(tokens[3:], line_no=line_no)
        cur.i += 1
        body = None
        if term_val == ":":
            body = _parse_block(cur, expected_indent=expected_indent + 4)
            if cur.i >= len(cur.lines):
                raise VerbaParseError("I expected 'end.' for this serve block.", line_no=line_no)
            end_line = cur.lines[cur.i]
            end_no = cur.i + 1
            if end_line.indent != expected_indent or not end_line.tokens or end_line.tokens[0].value.lower() != "end":
                raise VerbaParseError("I expected 'end.' at this indent.", line_no=end_no, col=end_line.indent)
            _require_period(end_line, end_no)
            cur.i += 1
        return ServeStart(span, port_expr, body)

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
            # print(f"DEBUG: expected={expected_indent}, actual={end_line.indent}, tok={end_line.tokens[0].value if end_line.tokens else 'NONE'}")
            raise VerbaParseError("I expected 'end.' at indent " + str(expected_indent), line_no=end_no, col=end_line.indent, line=end_line.raw)
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
        finally_body: Optional[list[Stmt]] = None

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

        # optional finally:
        if cur.i < len(cur.lines):
            nxt = cur.lines[cur.i]
            nxt_no = cur.i + 1
            nxt_lc = _lc(nxt.tokens)
            if nxt.indent == expected_indent and nxt_lc == ["finally", ":"]:
                _require_period(nxt, nxt_no)
                cur.i += 1
                finally_body = _parse_block(cur, expected_indent=expected_indent + 4)

        if cur.i >= len(cur.lines):
            raise VerbaParseError("I expected 'end.'", line_no=line_no)
        end_line = cur.lines[cur.i]
        end_no = cur.i + 1
        if end_line.indent != expected_indent or not end_line.tokens or end_line.tokens[0].value.lower() != "end":
            raise VerbaParseError("I expected 'end.'", line_no=end_no, col=end_line.indent, line=end_line.raw)
        _require_period(end_line, end_no)
        cur.i += 1
        return TryBlock(span, try_body, catch_body, error_name, finally_body)

def _parse_pattern(tokens: list[Token], line_no: int) -> MatchPattern:
    # Use tokens[0] for span if available
    span = Span(tokens[0].line_no, col=tokens[0].col, line_content=tokens[0].raw_line) if tokens else Span(line_no, 0)
    
    # [x, y] -> ListPattern
    if tokens and tokens[0].value == "[" and tokens[-1].value == "]":
        inner = tokens[1:-1]
        parts = _split_by_commas(inner)
        patterns = [_parse_pattern(p, line_no) for p in parts if p]
        return ListPattern(span, patterns)
        
    # { "a": 1, "b": x } -> MapPattern (Verba Map Literal style)
    if tokens and tokens[0].value == "{" and tokens[-1].value == "}":
        inner = tokens[1:-1]
        parts = _split_by_commas(inner)
        pairs = []
        for p in parts:
            if not p: continue
            # find colon
            colon_i = -1
            for k, t in enumerate(p):
                if t.value == ":":
                    colon_i = k
                    break
            if colon_i == -1:
                raise VerbaParseError("Map pattern must be 'key: pattern'.", line_no=line_no)
            # key can be bare name or string
            raw_key = p[:colon_i][-1].value.strip('"\'').lower()
            pat = _parse_pattern(p[colon_i+1:], line_no=line_no)
            pairs.append((raw_key, pat))
        return MapPattern(span, pairs)
    
    # if it's a single word and not a literal -> VariablePattern
    if len(tokens) == 1:
        val = tokens[0].value
        low = val.lower()
        if "." in val or low in ("true", "false", "null") or val.startswith('"') or val.startswith("'") or _parse_number(val) is not None:
            return ValuePattern(span, parse_expr(tokens, line_no=line_no))
        return VariablePattern(span, low)

    # default: evaluate as expression for ValuePattern
    return ValuePattern(span, parse_expr(tokens, line_no=line_no))

    # Standalone expression (e.g. run logic, method call)
    if not is_keyword_stmt:
        # We've already checked for assignment and math above.
        # If it's a simple name or method call, let it be a statement.
        try:
            expr = parse_expr(tokens, line_no=line_no)
            cur.i += 1
            return expr
        except VerbaParseError:
            # If expr parsing failed, fall through to keyword suggestion
            pass

    _KNOWN_KEYWORDS = [
        "say", "display", "ask", "if", "for", "while", "repeat", "define",
        "async", "run", "give", "return", "sort", "first", "last", "add",
        "remove", "save", "load", "import", "class", "free", "delete",
        "fetch", "append", "note", "try", "match", "raise", "stop", "skip",
        "assert", "serve", "on", "respond", "redirect", "await", "deref", "with", "help", "enum"
    ]

    def _suggest(word: str, candidates: list[str], threshold: float = 0.6) -> str | None:
        import difflib
        matches = difflib.get_close_matches(word, candidates, n=1, cutoff=threshold)
        return matches[0] if matches else None

    # Fallback for unrecognized statements
    cur.i += 1 
    suggestion = _suggest(first_val, _KNOWN_KEYWORDS)
    hint = f"Did you mean '{suggestion}'?" if suggestion else None
    raise VerbaParseError(
        f"I did not understand this line. Did you mean to use say, let, set, if, repeat, keep, define, run, or ask?",
        line_no=line_no,
        col=tokens[0].col,
        line=lt.raw,
        hint=hint,
    )


def _split_by_commas(tokens: list[Token]) -> list[list[Token]]:
    groups: list[list[Token]] = []
    cur: list[Token] = []
    depth = 0
    for t in tokens:
        if t.value in ("[", "{", "("):
            depth += 1
            cur.append(t)
        elif t.value in ("]", "}", ")"):
            depth -= 1
            cur.append(t)
        elif t.value == "," and depth == 0:
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
