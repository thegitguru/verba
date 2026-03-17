from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class Span:
    line_no: int


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


class Stmt:
    span: Span


@dataclass(frozen=True)
class Note(Stmt):
    span: Span
    text: str


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
class Repeat(Stmt):
    span: Span
    times: Expr
    body: list[Stmt]


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
class Define(Stmt):
    span: Span
    name: str
    params: list[str]
    body: list[Stmt]


@dataclass(frozen=True)
class GiveBack(Stmt):
    span: Span
    value: Expr


@dataclass(frozen=True)
class Run(Stmt):
    span: Span
    name: str
    args: list[Expr]


@dataclass(frozen=True)
class LetResultOfRun(Stmt):
    span: Span
    target_name: str
    func_name: str
    args: list[Expr]


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


@dataclass(frozen=True)
class Import(Stmt):
    span: Span
    filename: Expr
