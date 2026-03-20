from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class Span:
    line_no: int
    col: int = 0
    line_content: Optional[str] = None


class Expr:
    span: Span


@dataclass(frozen=True)
class Literal(Expr):
    span: Span
    value: Any


@dataclass(frozen=True)
class VarRef(Expr):
    span: Span
    name: str


@dataclass(frozen=True)
class BinaryOp(Expr):
    span: Span
    op: str
    left: Expr
    right: Expr


class BoolExpr:
    span: Span


@dataclass(frozen=True)
class Compare(BoolExpr):
    span: Span
    op: str
    left: Expr
    right: Expr


@dataclass(frozen=True)
class BoolNot(BoolExpr):
    span: Span
    inner: BoolExpr


@dataclass(frozen=True)
class BoolAnd(BoolExpr):
    span: Span
    left: BoolExpr
    right: BoolExpr


@dataclass(frozen=True)
class BoolOr(BoolExpr):
    span: Span
    left: BoolExpr
    right: BoolExpr


@dataclass(frozen=True)
class BoolExprFromExpr(BoolExpr):
    """Wraps a regular Expr into a BoolExpr for use in conditions."""
    span: Span
    expr: Expr


class Stmt:
    span: Span


@dataclass(frozen=True)
class Help(Stmt):
    span: Span
    topic: Optional[str] = None

@dataclass(frozen=True)
class Note(Stmt):
    span: Span
    value: str


@dataclass(frozen=True)
class Let(Stmt):
    span: Span
    name: str
    value: Expr
    forced_type: Optional[str] = None  # "number" | "word" | "flag" | "list" | None


@dataclass(frozen=True)
class SetVar(Stmt):
    span: Span
    name: str
    value: Expr


@dataclass(frozen=True)
class Increase(Stmt):
    span: Span
    name: str
    by: Expr


@dataclass(frozen=True)
class Decrease(Stmt):
    span: Span
    name: str
    by: Expr


@dataclass(frozen=True)
class Say(Stmt):
    span: Span
    values: list[Expr]
    newline: bool = True


@dataclass(frozen=True)
class Ask(Stmt):
    span: Span
    name: str
    prompt: Optional[str] = None


@dataclass(frozen=True)
class If(Stmt):
    span: Span
    condition: BoolExpr
    then_body: list[Stmt]
    else_body: Optional[list[Stmt]] = None


@dataclass(frozen=True)
class WithStmt(Stmt):
    """with <expr> as <var>: ... end."""
    span: Span
    expr: Expr
    var_name: str
    body: list[Stmt]


@dataclass(frozen=True)
class Repeat(Stmt):
    span: Span
    times: Expr
    body: list[Stmt]
    index_name: Optional[str] = None


@dataclass(frozen=True)
class While(Stmt):
    span: Span
    condition: BoolExpr
    body: list[Stmt]


@dataclass(frozen=True)
class ForEach(Stmt):
    span: Span
    item_name: str
    list_name: str
    body: list[Stmt]


@dataclass(frozen=True)
class ForRange(Stmt):
    """for i from <start> to <end> [step <step>]:  ...body...  end."""
    span: Span
    var_name: str
    start: Expr
    end: Expr
    step: Optional[Expr]
    body: list["Stmt"]


@dataclass(frozen=True)
class ForEachIndexed(Stmt):
    span: Span
    item_name: str
    index_name: str
    list_name: str
    body: list[Stmt]


@dataclass(frozen=True)
class ListAdd(Stmt):
    span: Span
    value: Expr
    list_name: str


@dataclass(frozen=True)
class ListRemove(Stmt):
    span: Span
    value: Expr
    list_name: str


@dataclass(frozen=True)
class ListItemGet(Stmt):
    span: Span
    target_name: str
    index: Expr
    list_name: str


@dataclass(frozen=True)
class ListSort(Stmt):
    """sort <list> [descending]."""
    span: Span
    list_name: str
    descending: bool


@dataclass(frozen=True)
class ListSlice(Stmt):
    """first <n> of <list> into <target>. / last <n> of <list> into <target>."""
    span: Span
    target_name: str
    list_name: str
    count: Expr
    from_end: bool


@dataclass(frozen=True)
class ListLiteral(Expr):
    span: Span
    values: list[Expr]


@dataclass(frozen=True)
class ListLength(Expr):
    span: Span
    list_name: str


@dataclass(frozen=True)
class Define(Stmt):
    span: Span
    name: str
    params: list[str]
    body: list['Stmt']
    defaults: dict[str, Expr] = None
    doc: Optional[str] = None
    decorators: list[str] = None

    def __hash__(self):
        return hash((self.span, self.name, tuple(self.params)))


@dataclass(frozen=True)
class MultiAssign(Stmt):
    """low, high = the result of running func with args  — destructures a list return value."""
    span: Span
    names: list[str]
    value: "Expr"


@dataclass(frozen=True)
class GiveBack(Stmt):
    """give <expr> [, <expr>, ...]  — returns one value or a list for multi-return."""
    span: Span
    values: list["Expr"]


@dataclass(frozen=True)
class Run(Expr):
    span: Span
    name: str
    args: list[Expr]
    kwargs: Optional[dict[str, Expr]] = None


@dataclass(frozen=True)
class LetResultOfRun(Stmt):
    span: Span
    target_name: str
    func_name: str
    args: list[Expr]
    kwargs: Optional[dict[str, Expr]] = None


@dataclass(frozen=True)
class SaveToFile(Stmt):
    span: Span
    text: Expr
    filename: Expr


@dataclass(frozen=True)
class LoadFile(Stmt):
    span: Span
    filename: Expr
    target_name: str


@dataclass(frozen=True)
class TryBlock(Stmt):
    span: Span
    try_body: list[Stmt]
    catch_body: Optional[list[Stmt]] = None
    error_name: Optional[str] = None
    finally_body: Optional[list[Stmt]] = None


@dataclass(frozen=True)
class Yield(Stmt):
    span: Span
    value: Expr


@dataclass(frozen=True)
class Import(Stmt):
    span: Span
    filename: Expr
    alias: Optional[str] = None

@dataclass(frozen=True)
class AppendToFile(Stmt):
    span: Span
    text: Expr
    filename: Expr

@dataclass(frozen=True)
class DeleteFile(Stmt):
    span: Span
    filename: Expr

@dataclass(frozen=True)
class FetchUrl(Stmt):
    span: Span
    url: Expr
    target_name: str

@dataclass(frozen=True)
class FreeVar(Stmt):
    span: Span
    name: str

@dataclass(frozen=True)
class ClassDef(Stmt):
    span: Span
    name: str
    methods: dict[str, Define]
    parent_name: Optional[str] = None
    fields: dict = None  # class-level default field values: {name: Expr}
    doc: Optional[str] = None

@dataclass(frozen=True)
class ObjectNew(Expr):
    span: Span
    class_name: str
    args: list[Expr]
    kwargs: Optional[dict[str, Expr]] = None

@dataclass(frozen=True)
class ObjectPropGet(Expr):
    span: Span
    obj_name: str
    prop: str

@dataclass(frozen=True)
class ObjectPropSet(Stmt):
    span: Span
    obj_name: str
    prop: str
    value: Expr

@dataclass(frozen=True)
class MethodCall(Expr):
    span: Span
    obj_name: str
    method: str
    args: list[Expr]
    kwargs: Optional[dict[str, Expr]] = None

@dataclass(frozen=True)
class LetResultOfMethod(Stmt):
    span: Span
    target_name: str
    obj_name: str
    method: str
    args: list[Expr]
    kwargs: Optional[dict[str, Expr]] = None

@dataclass(frozen=True)
class AsyncDefine(Stmt):
    span: Span
    name: str
    params: list[str]
    body: list[Stmt]
    decorators: list[str] = None

@dataclass(frozen=True)
class AsyncRun(Stmt):
    span: Span
    target_name: str
    func_name: str
    args: list[Expr]
    kwargs: Optional[dict[str, Expr]] = None

@dataclass(frozen=True)
class AwaitStmt(Stmt):
    span: Span
    target_name: str
    task_name: str


# --- HTTP server nodes ---

@dataclass(frozen=True)
class ServeStart(Stmt):
    """serve on port <expr>[: ... end]."""
    span: Span
    port: Expr
    body: Optional[list["Stmt"]] = None


@dataclass(frozen=True)
class ServeRoute(Stmt):
    """on route <path_expr> with method <method_expr>:  ...body...  end."""
    span: Span
    path: Expr
    method: Expr
    body: list["Stmt"]


@dataclass(frozen=True)
class ServeRespond(Stmt):
    """respond with <part>, <part>, ... status <code_expr> type <mime_expr>."""
    span: Span
    parts: list[Expr]
    status: Expr
    mime: Expr


@dataclass(frozen=True)
class ServeRedirect(Stmt):
    """redirect to <url_expr> status <code_expr>."""
    span: Span
    url: Expr
    status: Expr


@dataclass(frozen=True)
class StringConcat(Expr):
    """join <part>, <part>, ... — concatenates values into a string."""
    span: Span
    parts: list[Expr]


# --- Pointer nodes ---

@dataclass(frozen=True)
class Ref(Expr):
    """ref x  /  point to x  — captures a mutable reference to a variable."""
    span: Span
    name: str


@dataclass(frozen=True)
class Deref(Expr):
    """deref ptr  /  value at ptr  — reads the value a pointer points to."""
    span: Span
    name: str


@dataclass(frozen=True)
class DerefSet(Stmt):
    """deref ptr = expr  /  set value at ptr to expr  — writes through a pointer."""
    span: Span
    name: str
    value: Expr


@dataclass(frozen=True)
class Raise(Stmt):
    """raise <message_expr>."""
    span: Span
    message: Expr


@dataclass(frozen=True)
class Break(Stmt):
    span: Span


@dataclass(frozen=True)
class Continue(Stmt):
    span: Span


@dataclass(frozen=True)
class MapLiteral(Expr):
    span: Span
    pairs: list[tuple[Expr, Expr]]


@dataclass(frozen=True)
class ListComprehension(Expr):
    """result_expr for var in list_expr [if cond_expr]"""
    span: Span
    result_expr: "Expr"
    var_name: str
    list_expr: "Expr"
    cond_expr: Optional["Expr"] = None


@dataclass(frozen=True)
class MapComprehension(Expr):
    """key_expr: val_expr for key_var, val_var in list_expr [if cond_expr]"""
    span: Span
    key_expr: "Expr"
    val_expr: "Expr"
    key_var: str
    val_var: str
    list_expr: "Expr"
    cond_expr: Optional["Expr"] = None


@dataclass(frozen=True)
class Test(Stmt):
    span: Span
    name: str
    body: list[Stmt]


@dataclass(frozen=True)
class Assert(Stmt):
    span: Span
    condition: "BoolExpr"
    message: Optional[str] = None


class MatchPattern:
    span: Span


@dataclass(frozen=True)
class ValuePattern(MatchPattern):
    span: Span
    value: Expr


@dataclass(frozen=True)
class VariablePattern(MatchPattern):
    span: Span
    name: str


@dataclass(frozen=True)
class ListPattern(MatchPattern):
    span: Span
    patterns: list[MatchPattern]


@dataclass(frozen=True)
class MapPattern(MatchPattern):
    span: Span
    pairs: list[tuple[str, MatchPattern]]


@dataclass(frozen=True)
class MatchBranch:
    pattern: MatchPattern
    body: list["Stmt"]


@dataclass(frozen=True)
class Match(Stmt):
    span: Span
    subject: "Expr"
    branches: list[MatchBranch]
    else_body: Optional[list["Stmt"]] = None

@dataclass(frozen=True)
class EnumDef(Stmt):
    span: Span
    name: str
    members: list[str]
