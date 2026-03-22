from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
from . import ast

class Pointer:
    def __init__(self, name: str, env: "Environment"):
        self.name = name
        self.env = env
    def get(self) -> object:
        return self.env.get(self.name)
    def set(self, value: object) -> None:
        self.env.set(self.name, value)
    def __repr__(self) -> str:
        return f"<ptr -> {self.name}>"

@dataclass
class Function:
    name: str
    params: list[str]
    body: list[ast.Stmt]
    decorators: list[str] = None
    defaults: dict = None
    doc: Optional[str] = None
    defining_env: Optional["Environment"] = None
    def __post_init__(self):
        if self.defaults is None: self.defaults = {}
        if self.decorators is None: self.decorators = []

@dataclass
class ClassObj:
    name: str
    methods: dict[str, ast.Define]
    parent: Optional["ClassObj"] = None
    field_defaults: dict = None
    doc: Optional[str] = None
    def __post_init__(self):
        if self.field_defaults is None: self.field_defaults = {}

class Instance:
    def __init__(self, cls: ClassObj):
        self.cls = cls
        self.props = {}


class OptionValue:
    def __init__(self, value: Any = None, *, has_value: bool = False):
        self.value = value
        self.has_value = has_value
        self.cls = None
        self.props = {
            "is_some": has_value,
            "is_none": not has_value,
            "value": value if has_value else None,
        }

    @classmethod
    def some(cls, value: Any) -> "OptionValue":
        return cls(value, has_value=True)

    @classmethod
    def none(cls) -> "OptionValue":
        return cls(None, has_value=False)

    def __bool__(self) -> bool:
        return self.has_value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, OptionValue):
            return False
        return self.has_value == other.has_value and self.value == other.value

    def __repr__(self) -> str:
        if self.has_value:
            return f"some({self.value!r})"
        return "none"

    def __str__(self) -> str:
        if self.has_value:
            return f"some({self.value})"
        return "none"

@dataclass
class NativeFunction:
    name: str
    params: list[str]
    fn: object
    needs_interp: bool = False

class NativeInstance:
    def __init__(self, name: str, methods: dict[str, NativeFunction]):
        self.name = name
        self.methods = methods
        self.cls = None
        self.props: dict[str, Any] = {}

class _ReturnSignal(Exception):
    def __init__(self, value: Any): self.value = value
class _BreakSignal(Exception): pass
class _ContinueSignal(Exception): pass
class _RespondSignal(Exception):
    def __init__(self, body: str, status: int, mime: str):
        self.body, self.status, self.mime = body, status, mime
class _RedirectSignal(Exception):
    def __init__(self, url: str, status: int):
        self.url, self.status = url, status

class _VerbaRequest:
    def __init__(self, method: str, path: str, query: dict, form: dict, raw_body: str, headers: dict):
        self.cls = None
        self.props = {"method": method, "path": path, "body": raw_body}
        for k, v in query.items(): self.props[f"query_{k}"] = v[0] if v else ""
        for k, v in form.items(): self.props[f"form_{k}"] = v[0] if v else ""

class Environment:
    def __init__(self, parent: Optional["Environment"] = None):
        self.parent = parent
        self.values: dict[str, Any] = {}
        self.functions: dict[str, "Function"] = {}
        self.classes: dict[str, "ClassObj"] = {}

    def contains(self, name: str) -> bool:
        if name in self.values: return True
        return self.parent.contains(name) if self.parent else False

    def get(self, name: str) -> Any:
        if name in self.values: return self.values[name]
        if self.parent: return self.parent.get(name)
        raise KeyError(name)

    def set(self, name: str, value: Any, local: bool = False) -> None:
        if local: self.values[name] = value; return
        if name in self.values: self.values[name] = value; return
        if self.parent and self.parent.contains(name): self.parent.set(name, value); return
        self.values[name] = value

    def get_function(self, name: str) -> Optional["Function"]:
        if name in self.functions: return self.functions[name]
        if self.parent: return self.parent.get_function(name)
        return None

    def get_class(self, name: str) -> Optional["ClassObj"]:
        if name in self.classes: return self.classes[name]
        if self.parent: return self.parent.get_class(name)
        return None

class Module:
    def __init__(self, name: str, env: Environment):
        self.name = name
        self.env = env
        self.cls = None
        self.props = env.values  # Expose variables as properties
        self.methods = env.functions # Expose functions as methods
