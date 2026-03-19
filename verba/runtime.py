from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from . import ast
from .errors import VerbaRuntimeError


class Pointer:
    """A mutable cell. ref x wraps the variable name + its environment."""
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
    defaults: dict = None

    def __post_init__(self):
        if self.defaults is None:
            self.defaults = {}


@dataclass
class ClassObj:
    name: str
    methods: dict[str, ast.Define]
    parent: Optional["ClassObj"] = None
    field_defaults: dict = None  # {field_name: evaluated_default_value}

    def __post_init__(self):
        if self.field_defaults is None:
            self.field_defaults = {}


class Instance:
    def __init__(self, cls: ClassObj):
        self.cls = cls
        self.props = {}


@dataclass
class NativeFunction:
    """A Python callable exposed as a Verba function."""
    name: str
    params: list[str]
    fn: object          # callable
    needs_interp: bool = False


class NativeInstance:
    """
    An object whose methods are NativeFunctions.
    Exposed in Verba as a variable (e.g. `http`, `browser`, `express`).
    """
    def __init__(self, name: str, methods: dict[str, NativeFunction]):
        self.name    = name
        self.methods = methods
        self.cls     = None
        self.props: dict[str, Any] = {}


class _ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value


class _BreakSignal(Exception):
    pass


class _ContinueSignal(Exception):
    pass


class _RespondSignal(Exception):
    """Raised by ServeRespond to unwind back to the HTTP handler."""
    def __init__(self, body: str, status: int, mime: str):
        self.body   = body
        self.status = status
        self.mime   = mime


class _RedirectSignal(Exception):
    """Raised by ServeRedirect to issue an HTTP redirect."""
    def __init__(self, url: str, status: int):
        self.url    = url
        self.status = status


class _VerbaRequest:
    """Injected as `request` inside every route handler block."""
    def __init__(self, method: str, path: str, query: dict, form: dict,
                 raw_body: str, headers: dict):
        self._query = query
        self._form  = form
        self._headers = headers
        # Expose as Instance-compatible so request.method etc. work via ObjectPropGet
        self.cls   = None
        self.props = {
            "method": method,
            "path":   path,
            "body":   raw_body,
        }
        # Also pre-populate query and form keys directly
        for k, v in query.items():
            self.props[f"query_{k}"] = v[0] if v else ""
        for k, v in form.items():
            self.props[f"form_{k}"] = v[0] if v else ""


class Environment:
    def __init__(self, parent: Optional["Environment"] = None):
        self.parent = parent
        self.values: dict[str, Any] = {}

    def has_local(self, name: str) -> bool:
        return name in self.values

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise KeyError(name)

    def set(self, name: str, value: Any) -> None:
        # Set walks upward if variable already exists.
        if name in self.values:
            self.values[name] = value
            return
        if self.parent is not None and self.parent.contains(name):
            self.parent.set(name, value)
            return
        self.values[name] = value

    def contains(self, name: str) -> bool:
        if name in self.values:
            return True
        if self.parent is not None:
            return self.parent.contains(name)
        return False


class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self.functions: dict[str, Function] = {}
        self.classes: dict[str, ClassObj] = {}
        self._http_routes: dict[tuple[str, str], tuple] = {}
        self._inject_stdlib()

    # ── stdlib injection ──────────────────────────────────────────────────────

    def _inject_stdlib(self) -> None:
        from verba.stdlib import http as _http_mod
        from verba.stdlib import browser as _browser_mod
        from verba.stdlib import express as _express_mod
        from verba.stdlib import strings as _strings_mod
        from verba.stdlib import math as _math_mod
        from verba.stdlib import json as _json_mod
        from verba.stdlib import os as _os_mod
        from verba.stdlib import time as _time_mod
        from verba.stdlib import env as _env_mod
        for mod_name, mod in [
            ("http",    _http_mod),
            ("browser", _browser_mod),
            ("express", _express_mod),
            ("strings", _strings_mod),
            ("math",    _math_mod),
            ("json",    _json_mod),
            ("os",      _os_mod),
            ("time",    _time_mod),
            ("env",     _env_mod),
        ]:
            needs_interp: set = getattr(mod, "NEEDS_INTERP", set())
            methods = {}
            for fn_name, (fn, params) in mod.FUNCTIONS.items():
                methods[fn_name] = NativeFunction(
                    name=fn_name, params=params, fn=fn,
                    needs_interp=(fn_name in needs_interp),
                )
            self.globals.set(mod_name, NativeInstance(mod_name, methods))

    def run(self, program: list[ast.Stmt]) -> Any:
        return self._exec_block(program, env=self.globals)

    def _exec_block(self, stmts: list[ast.Stmt], *, env: Environment) -> Any:
        for s in stmts:
            self._exec_stmt(s, env=env)
        return None

    def _exec_stmt(self, s: ast.Stmt, *, env: Environment) -> None:
        ln = s.span.line_no
        col = s.span.col
        raw = s.span.line_content

        if isinstance(s, ast.DerefSet):
            ptr = env.get(s.name) if env.contains(s.name) else None
            if not isinstance(ptr, Pointer):
                raise VerbaRuntimeError(f"The variable called {s.name} is not a pointer.", line_no=ln, col=col, line=raw)
            value = self._eval_expr(s.value, env=env, context="general")
            ptr.set(value)
            return

        if isinstance(s, ast.Note):
            return

        if isinstance(s, ast.Raise):
            msg = self._to_word(self._eval_expr(s.message, env=env, context="general"))
            raise VerbaRuntimeError(msg, line_no=ln, col=col, line=raw)

        if isinstance(s, ast.Break):
            raise _BreakSignal()

        if isinstance(s, ast.Continue):
            raise _ContinueSignal()

        if isinstance(s, ast.Assert):
            ok = self._eval_bool(s.condition, env=env)
            if not ok:
                msg = s.message if s.message else "Assertion failed."
                raise VerbaRuntimeError(msg, line_no=ln, col=col, line=raw)
            return

        if isinstance(s, ast.Match):
            subject = self._eval_expr(s.subject, env=env, context="general")
            for branch in s.branches:
                val = self._eval_expr(branch.value, env=env, context="general")
                if subject == val:
                    self._exec_block(branch.body, env=env)
                    return
            if s.else_body is not None:
                self._exec_block(s.else_body, env=env)
            return

        if isinstance(s, ast.Let):
            value = self._eval_expr(s.value, env=env, context="general")
            if s.forced_type == "number":
                value = self._to_number(value, ln)
            elif s.forced_type == "flag":
                value = bool(value)
            elif s.forced_type == "word":
                value = self._to_word(value)
            elif s.forced_type == "list":
                # parser stores list literals as Literal(list[Expr]) already evaluated to python values
                if isinstance(value, list):
                    # Treat unknown bare words as literal words (so "a list of red, green" works),
                    # but still resolve real variables if they already exist.
                    value = [self._eval_expr(v, env=env, context="say") if isinstance(v, ast.Expr) else v for v in value]
            env.set(s.name, value)
            return

        if isinstance(s, ast.SetVar):
            if not env.contains(s.name):
                raise VerbaRuntimeError(f"The variable called {s.name} has not been defined yet.", line_no=ln, col=col, line=raw)
            value = self._eval_expr(s.value, env=env, context="general")
            env.set(s.name, value)
            return

        if isinstance(s, ast.Increase):
            if not env.contains(s.name):
                raise VerbaRuntimeError(f"The variable called {s.name} has not been defined yet.", line_no=ln, col=col, line=raw)
            cur = env.get(s.name)
            by = self._to_number(self._eval_expr(s.by, env=env, context="general"), ln)
            env.set(s.name, self._to_number(cur, ln) + by)
            return

        if isinstance(s, ast.Decrease):
            if not env.contains(s.name):
                raise VerbaRuntimeError(f"The variable called {s.name} has not been defined yet.", line_no=ln, col=col, line=raw)
            cur = env.get(s.name)
            by = self._to_number(self._eval_expr(s.by, env=env, context="general"), ln)
            env.set(s.name, self._to_number(cur, ln) - by)
            return

        if isinstance(s, ast.Say):
            outs: list[str] = []
            for v in s.values:
                val = self._eval_expr(v, env=env, context="say")
                outs.append(self._format_value(val))
            print("".join(outs), end="\n" if s.newline else "")
            return

        if isinstance(s, ast.Ask):
            prompt = s.prompt if s.prompt is not None else f"{s.name}"
            raw = input(prompt + " ")
            # Try to store numbers as numbers when the user clearly entered one.
            num = None
            try:
                num = int(raw)
            except ValueError:
                try:
                    num = float(raw) if raw.strip() else None
                except ValueError:
                    num = None
            env.set(s.name, num if num is not None else raw)
            return

        if isinstance(s, ast.If):
            ok = self._eval_bool(s.condition, env=env)
            if ok:
                self._exec_block(s.then_body, env=env)
            elif s.else_body is not None:
                self._exec_block(s.else_body, env=env)
            return

        if isinstance(s, ast.Repeat):
            n = int(self._to_number(self._eval_expr(s.times, env=env, context="general"), ln))
            for i in range(n):
                loop_env = Environment(parent=env)
                if s.index_name:
                    loop_env.set(s.index_name, i + 1)
                try:
                    self._exec_block(s.body, env=loop_env)
                except _ContinueSignal:
                    continue
                except _BreakSignal:
                    break
            return

        if isinstance(s, ast.While):
            guard = 0
            while self._eval_bool(s.condition, env=env):
                try:
                    self._exec_block(s.body, env=env)
                except _ContinueSignal:
                    pass
                except _BreakSignal:
                    break
                guard += 1
                if guard > 10_000_000:
                    raise VerbaRuntimeError("This loop ran for too long. Did you forget to update the condition?", line_no=ln, col=col, line=raw)
            return

        if isinstance(s, ast.ForRange):
            start = self._to_number(self._eval_expr(s.start, env=env, context="general"), ln)
            end   = self._to_number(self._eval_expr(s.end,   env=env, context="general"), ln)
            step  = self._to_number(self._eval_expr(s.step,  env=env, context="general"), ln) if s.step else (1 if start <= end else -1)
            i = start
            while (step > 0 and i <= end) or (step < 0 and i >= end):
                loop_env = Environment(parent=env)
                loop_env.set(s.var_name, int(i) if float(i).is_integer() else i)
                try:
                    self._exec_block(s.body, env=loop_env)
                except _ContinueSignal:
                    pass
                except _BreakSignal:
                    break
                i += step
            return

        if isinstance(s, ast.ForEach):
            if not env.contains(s.list_name):
                raise VerbaRuntimeError(f"The list called {s.list_name} has not been defined yet.", line_no=ln, col=col, line=raw)
            lst = env.get(s.list_name)
            if not isinstance(lst, list):
                raise VerbaRuntimeError(f"The variable called {s.list_name} is not a list.", line_no=ln, col=col, line=raw)
            for item in lst:
                inner = Environment(parent=env)
                inner.set(s.item_name, item)
                try:
                    self._exec_block(s.body, env=inner)
                except _ContinueSignal:
                    continue
                except _BreakSignal:
                    break
            return

        if isinstance(s, ast.ForEachIndexed):
            if not env.contains(s.list_name):
                raise VerbaRuntimeError(f"The list called {s.list_name} has not been defined yet.", line_no=ln, col=col, line=raw)
            lst = env.get(s.list_name)
            if not isinstance(lst, list):
                raise VerbaRuntimeError(f"The variable called {s.list_name} is not a list.", line_no=ln, col=col, line=raw)
            for idx, item in enumerate(lst, start=1):
                inner = Environment(parent=env)
                inner.set(s.item_name, item)
                inner.set(s.index_name, idx)
                try:
                    self._exec_block(s.body, env=inner)
                except _ContinueSignal:
                    continue
                except _BreakSignal:
                    break
            return

        if isinstance(s, ast.ListSort):
            if not env.contains(s.list_name):
                raise VerbaRuntimeError(f"The list called {s.list_name} has not been defined yet.", line_no=ln, col=col, line=raw)
            lst = env.get(s.list_name)
            if not isinstance(lst, list):
                raise VerbaRuntimeError(f"The variable called {s.list_name} is not a list.", line_no=ln, col=col, line=raw)
            try:
                lst.sort(reverse=s.descending)
            except TypeError:
                lst.sort(key=str, reverse=s.descending)
            return

        if isinstance(s, ast.ListSlice):
            if not env.contains(s.list_name):
                raise VerbaRuntimeError(f"The list called {s.list_name} has not been defined yet.", line_no=ln, col=col, line=raw)
            lst = env.get(s.list_name)
            if not isinstance(lst, list):
                raise VerbaRuntimeError(f"The variable called {s.list_name} is not a list.", line_no=ln, col=col, line=raw)
            n = int(self._to_number(self._eval_expr(s.count, env=env, context="general"), ln))
            sliced = lst[-n:] if s.from_end else lst[:n]
            env.set(s.target_name, sliced)
            return

        if isinstance(s, ast.ListAdd):
            if not env.contains(s.list_name):
                raise VerbaRuntimeError(f"The list called {s.list_name} has not been defined yet.", line_no=ln, col=col, line=raw)
            lst = env.get(s.list_name)
            if not isinstance(lst, list):
                raise VerbaRuntimeError(f"The variable called {s.list_name} is not a list.", line_no=ln, col=col, line=raw)
            val = self._eval_expr(s.value, env=env, context="say")
            lst.append(val)
            return

        if isinstance(s, ast.ListRemove):
            if not env.contains(s.list_name):
                raise VerbaRuntimeError(f"The list called {s.list_name} has not been defined yet.", line_no=ln, col=col, line=raw)
            lst = env.get(s.list_name)
            if not isinstance(lst, list):
                raise VerbaRuntimeError(f"The variable called {s.list_name} is not a list.", line_no=ln, col=col, line=raw)
            val = self._eval_expr(s.value, env=env, context="say")
            try:
                lst.remove(val)
            except ValueError:
                # No-op (novice friendly)
                return
            return

        if isinstance(s, ast.ListItemGet):
            if not env.contains(s.list_name):
                raise VerbaRuntimeError(f"The list called {s.list_name} has not been defined yet.", line_no=ln, col=col, line=raw)
            lst = env.get(s.list_name)
            if not isinstance(lst, list):
                raise VerbaRuntimeError(f"The variable called {s.list_name} is not a list.", line_no=ln, col=col, line=raw)
            idx = int(self._to_number(self._eval_expr(s.index, env=env, context="general"), ln))
            if idx < 1 or idx > len(lst):
                raise VerbaRuntimeError(f"Item {idx} does not exist in the list called {s.list_name}.", line_no=ln, col=col, line=raw)
            env.set(s.target_name, lst[idx - 1])
            return

        if isinstance(s, ast.Define):
            fn = Function(s.name, s.params, s.body)
            fn.defaults = {k: self._eval_expr(v, env=env, context="general") for k, v in (s.defaults or {}).items()}
            self.functions[s.name] = fn
            return

        if isinstance(s, ast.GiveBack):
            if len(s.values) == 1:
                value = self._eval_expr(s.values[0], env=env, context="general")
            else:
                value = [self._eval_expr(v, env=env, context="general") for v in s.values]
            raise _ReturnSignal(value)

        if isinstance(s, ast.Run):
            self._call(s.name, s.args, caller_env=env, line_no=ln)
            return

        if isinstance(s, ast.MultiAssign):
            # Evaluate RHS
            rhs = s.value
            # rhs is either a Literal wrapping a LetResultOfRun/LetResultOfMethod AST node
            # or a plain Expr (list)
            from .ast import Literal as _Lit, LetResultOfRun as _LROR, LetResultOfMethod as _LROM
            if isinstance(rhs, _Lit) and isinstance(rhs.value, (_LROR, _LROM)):
                inner = rhs.value
                if isinstance(inner, _LROR):
                    result = self._call(inner.func_name, inner.args, caller_env=env, line_no=ln)
                else:
                    obj = env.get(inner.obj_name) if env.contains(inner.obj_name) else None
                    if isinstance(obj, NativeInstance):
                        result = self._call_native_method(obj, inner.method, inner.args, caller_env=env, line_no=ln)
                    else:
                        result = self._call_method(obj, inner.method, inner.args, caller_env=env, line_no=ln)
            else:
                result = self._eval_expr(rhs, env=env, context="general")
            # Unpack
            if not isinstance(result, list):
                result = [result]
            for i, name in enumerate(s.names):
                env.set(name, result[i] if i < len(result) else None)
            return

        if isinstance(s, ast.LetResultOfRun):
            value = self._call(s.func_name, s.args, caller_env=env, line_no=ln)
            env.set(s.target_name, value)
            return

        if isinstance(s, ast.SaveToFile):
            text = self._eval_expr(s.text, env=env, context="general")
            filename = self._eval_expr(s.filename, env=env, context="general")
            try:
                path = str(filename)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self._to_word(text))
            except OSError:
                raise VerbaRuntimeError(f"I could not save to the file called {filename}.", line_no=ln, col=col, line=raw)
            return

        if isinstance(s, ast.LoadFile):
            filename = self._eval_expr(s.filename, env=env, context="general")
            try:
                path = str(filename)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except OSError:
                raise VerbaRuntimeError(f"I could not open the file called {filename}.", line_no=ln, col=col, line=raw)
            env.set(s.target_name, content)
            return

        if isinstance(s, ast.TryBlock):
            caught = False
            try:
                self._exec_block(s.try_body, env=env)
            except VerbaRuntimeError as e:
                caught = True
                if s.catch_body is not None:
                    err_env = Environment(parent=env)
                    if s.error_name:
                        err_env.set(s.error_name, str(e))
                    self._exec_block(s.catch_body, env=err_env)
            finally:
                if s.finally_body is not None:
                    self._exec_block(s.finally_body, env=env)
            return

        if isinstance(s, ast.Import):
            filename = self._eval_expr(s.filename, env=env, context="general")
            try:
                path = str(filename)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except OSError:
                raise VerbaRuntimeError(f"I could not open the file called {filename}.", line_no=ln, col=col, line=raw)
            from .parser import parse
            from .errors import VerbaParseError
            try:
                prog = parse(content)
                self._exec_block(prog, env=env)
            except VerbaParseError as e:
                raise VerbaRuntimeError(f"Error parsing imported file {filename}: {e}", line_no=ln, col=col, line=raw)
            return

        if isinstance(s, ast.AppendToFile):
            text = self._eval_expr(s.text, env=env, context="general")
            filename = self._eval_expr(s.filename, env=env, context="general")
            try:
                with open(str(filename), "a", encoding="utf-8") as f:
                    f.write(self._to_word(text))
            except OSError:
                raise VerbaRuntimeError(f"I could not save to the file called {filename}.", line_no=ln)
            return

        if isinstance(s, ast.DeleteFile):
            filename = self._eval_expr(s.filename, env=env, context="general")
            import os
            try:
                os.remove(str(filename))
            except OSError:
                pass
            return

        if isinstance(s, ast.FetchUrl):
            import urllib.request
            url = self._eval_expr(s.url, env=env, context="general")
            try:
                with urllib.request.urlopen(str(url)) as response:
                    html = response.read().decode()
                env.set(s.target_name, html)
            except Exception:
                raise VerbaRuntimeError(f"I could not fetch the URL: {url}.", line_no=ln, col=col, line=raw)
            return

        if isinstance(s, ast.FreeVar):
            if env.contains(s.name):
                curr = env
                while curr is not None:
                    if s.name in curr.values:
                        del curr.values[s.name]
                        return
                    curr = curr.parent
            return

        if isinstance(s, ast.ClassDef):
            parent = self.classes.get(s.parent_name) if s.parent_name else None
            if s.parent_name and parent is None:
                raise VerbaRuntimeError(f"Parent class {s.parent_name} has not been defined.", line_no=ln)
            # Inherit parent methods, child overrides take precedence
            merged = dict(parent.methods) if parent else {}
            merged.update(s.methods)
            # Merge fields: parent fields first, then child fields override
            merged_fields = dict(parent.field_defaults or {}) if parent else {}
            merged_fields.update(s.fields or {})
            cls_obj = ClassObj(s.name, merged, parent)
            # Evaluate field default expressions and store values
            cls_obj.field_defaults = {
                k: self._eval_expr(v, env=env, context="general")
                for k, v in merged_fields.items()
            }
            self.classes[s.name] = cls_obj
            return

        if isinstance(s, ast.ObjectPropSet):
            obj = env.get(s.obj_name)
            if isinstance(obj, dict):
                val = self._eval_expr(s.value, env=env, context="general")
                obj[s.prop] = val
                return
            if not isinstance(obj, Instance):
                raise VerbaRuntimeError(f"Variable {s.obj_name} is not an object.", line_no=ln, col=col, line=raw)
            val = self._eval_expr(s.value, env=env, context="general")
            obj.props[s.prop] = val
            return

        if isinstance(s, ast.MethodCall):
            obj = env.get(s.obj_name) if env.contains(s.obj_name) else None
            if isinstance(obj, NativeInstance):
                self._call_native_method(obj, s.method, s.args, caller_env=env, line_no=ln)
                return
            if not isinstance(obj, Instance):
                raise VerbaRuntimeError(f"Variable {s.obj_name} is not an object.", line_no=ln, col=col, line=raw)
            self._call_method(obj, s.method, s.args, caller_env=env, line_no=ln)
            return

        if isinstance(s, ast.LetResultOfMethod):
            obj = env.get(s.obj_name) if env.contains(s.obj_name) else None
            if isinstance(obj, NativeInstance):
                val = self._call_native_method(obj, s.method, s.args, caller_env=env, line_no=ln)
                env.set(s.target_name, val)
                return
            if not isinstance(obj, Instance):
                raise VerbaRuntimeError(f"Variable {s.obj_name} is not an object.", line_no=ln, col=col, line=raw)
            val = self._call_method(obj, s.method, s.args, caller_env=env, line_no=ln)
            env.set(s.target_name, val)
            return

        if isinstance(s, ast.AsyncDefine):
            self.functions[s.name] = s
            return

        if isinstance(s, ast.AsyncRun):
            import threading
            task_env = Environment(parent=self.globals)
            for p, a in zip(self.functions[s.func_name].params, s.args):
                task_env.set(p, self._eval_expr(a, env=env, context="general"))
                
            task = {"result": None, "done": False, "error": None}
            def _async_worker():
                try:
                    res = None
                    try:
                        self._exec_block(self.functions[s.func_name].body, env=task_env)
                    except _ReturnSignal as r:
                         res = r.value
                    task["result"] = res
                except Exception as e:
                    task["error"] = e
                finally:
                    task["done"] = True
                    
            env.set(s.target_name, task)
            threading.Thread(target=_async_worker).start()
            return
            
        if isinstance(s, ast.AwaitStmt):
            import time
            task = env.get(s.task_name)
            if not isinstance(task, dict) or "done" not in task:
                raise VerbaRuntimeError(f"Variable {s.task_name} is not a valid async task.", line_no=ln, col=col, line=raw)
            while not task["done"]:
                time.sleep(0.01)
            if task["error"]:
                raise VerbaRuntimeError(f"Async error: {task['error']}", line_no=ln, col=col, line=raw)
            env.set(s.target_name, task["result"])
            return

        if isinstance(s, ast.ServeRoute):
            path   = self._to_word(self._eval_expr(s.path,   env=env, context="general"))
            method = self._to_word(self._eval_expr(s.method, env=env, context="general")).upper()
            self._http_routes[(method, path)] = (s.body, env)
            return

        if isinstance(s, ast.ServeStart):
            import http.server, threading
            port = int(self._to_number(self._eval_expr(s.port, env=env, context="general"), ln))
            interp = self

            class _VerbaHandler(http.server.BaseHTTPRequestHandler):
                def log_message(self, *_): pass

                def _dispatch(self, method: str):
                    import urllib.parse
                    parsed   = urllib.parse.urlparse(self.path)
                    path     = parsed.path
                    qs       = urllib.parse.parse_qs(parsed.query)
                    length   = int(self.headers.get("Content-Length", 0))
                    raw_body = self.rfile.read(length).decode("utf-8", errors="replace") if length else ""
                    form     = urllib.parse.parse_qs(raw_body)

                    # Build the request object visible to Verba code as `request`
                    req_obj = _VerbaRequest(method, path, qs, form, raw_body,
                                            dict(self.headers))

                    key = (method, path)
                    if key not in interp._http_routes:
                        key = (method, "*")  # wildcard fallback
                    if key not in interp._http_routes:
                        self._raw_respond(404, "text/plain", "404 Not Found")
                        return

                    body_stmts, route_env = interp._http_routes[key]
                    handler_env = Environment(parent=route_env)
                    handler_env.set("request", req_obj)

                    interp._http_response = None
                    try:
                        interp._exec_block(body_stmts, env=handler_env)
                    except _RespondSignal as r:
                        self._raw_respond(r.status, r.mime, r.body)
                        return
                    except _RedirectSignal as r:
                        self.send_response(r.status)
                        self.send_header("Location", r.url)
                        self.send_header("Content-Length", "0")
                        self.end_headers()
                        return
                    # If no respond statement was hit, send empty 200
                    self._raw_respond(200, "text/html", "")

                def _raw_respond(self, status: int, mime: str, body: str):
                    data = body.encode("utf-8")
                    self.send_response(status)
                    self.send_header("Content-Type", mime)
                    self.send_header("Content-Length", len(data))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(data)

                def do_GET(self):    self._dispatch("GET")
                def do_POST(self):   self._dispatch("POST")
                def do_PUT(self):    self._dispatch("PUT")
                def do_DELETE(self): self._dispatch("DELETE")

            server = http.server.HTTPServer(("", port), _VerbaHandler)
            print(f"Verba HTTP server listening on http://localhost:{port}")
            threading.Thread(target=server.serve_forever, daemon=True).start()
            # Block the main thread so the script keeps running
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                server.shutdown()
            return

        if isinstance(s, ast.ServeRedirect):
            url    = self._to_word(self._eval_expr(s.url,    env=env, context="general"))
            status = int(self._to_number(self._eval_expr(s.status, env=env, context="general"), ln))
            raise _RedirectSignal(url, status)

        if isinstance(s, ast.ServeRespond):
            parts  = [self._to_word(self._eval_expr(p, env=env, context="say")) for p in s.parts]
            body   = "".join(parts)
            status = int(self._to_number(self._eval_expr(s.status, env=env, context="general"), ln))
            mime   = self._to_word(self._eval_expr(s.mime,   env=env, context="general"))
            raise _RespondSignal(body, status, mime)

        raise VerbaRuntimeError("I reached a statement I cannot execute yet.", line_no=ln)

    def _eval_expr(self, e: ast.Expr, *, env: Environment, context: str) -> Any:
        ln = e.span.line_no
        col = e.span.col
        raw = e.span.line_content

        if isinstance(e, ast.StringConcat):
            return "".join(self._to_word(self._eval_expr(p, env=env, context="say")) for p in e.parts)

        if isinstance(e, ast.ListLength):
            if not env.contains(e.list_name):
                raise VerbaRuntimeError(f"The variable called {e.list_name} has not been defined yet.", line_no=ln)
            lst = env.get(e.list_name)
            if not isinstance(lst, list):
                raise VerbaRuntimeError(f"The variable called {e.list_name} is not a list.", line_no=ln)
            return len(lst)

        if isinstance(e, ast.Ref):
            if not env.contains(e.name):
                raise VerbaRuntimeError(f"The variable called {e.name} has not been defined yet.", line_no=ln, col=col, line=raw)
            return Pointer(e.name, env)

        if isinstance(e, ast.Deref):
            ptr = env.get(e.name) if env.contains(e.name) else None
            if not isinstance(ptr, Pointer):
                raise VerbaRuntimeError(f"The variable called {e.name} is not a pointer.", line_no=ln, col=col, line=raw)
            return ptr.get()

        if isinstance(e, ast.ObjectNew):
            if e.class_name not in self.classes:
                raise VerbaRuntimeError(f"Class {e.class_name} has not been defined.", line_no=ln)
            cls = self.classes[e.class_name]
            inst = Instance(cls)
            # Initialize class-level field defaults (already evaluated, so copy them)
            import copy
            for fname, fval in cls.field_defaults.items():
                # Deep-copy mutable defaults (lists, dicts) so instances don't share them
                inst.props[fname] = copy.deepcopy(fval)
            if "init" in cls.methods:
                self._call_method(inst, "init", e.args, caller_env=env, line_no=ln)
            elif e.args:
                raise VerbaRuntimeError(f"Class {e.class_name} does not have an init method but arguments were passed.", line_no=ln)
            return inst

        if isinstance(e, ast.MapLiteral):
            return {k: self._eval_expr(v, env=env, context="general") for k, v in e.pairs}

        if isinstance(e, ast.ObjectPropGet):
            if e.obj_name == "self":
                obj = env.get("self")
            else:
                obj = env.get(e.obj_name) if env.contains(e.obj_name) else None
            # Walk chained props: e.prop may be "address.city"
            for prop_part in e.prop.split("."):
                if isinstance(obj, NativeInstance):
                    obj = obj.props.get(prop_part)
                elif isinstance(obj, dict):
                    obj = obj.get(prop_part)
                elif isinstance(obj, (Instance, _VerbaRequest)):
                    obj = obj.props.get(prop_part)
                else:
                    raise VerbaRuntimeError(f"Cannot access property '{prop_part}' on a non-object.", line_no=ln)
            return obj

        if isinstance(e, ast.Literal):
            return e.value

        if isinstance(e, ast.VarRef):
            if env.contains(e.name):
                return env.get(e.name)
            if context == "say":
                # In output, undefined names are treated as literal words (so "say hello." works).
                return e.name
            # "Did you mean?" suggestion for undefined variables
            import difflib
            known = list(env.values.keys())
            if env.parent:
                curr = env.parent
                while curr:
                    known.extend(curr.values.keys())
                    curr = curr.parent
            matches = difflib.get_close_matches(e.name, known, n=1, cutoff=0.7)
            hint = f"Did you mean '{matches[0]}'?" if matches else None
            raise VerbaRuntimeError(
                f"The variable called {e.name} has not been defined yet.",
                line_no=ln, col=col, line=raw, hint=hint
            )

        if isinstance(e, ast.BinaryOp):
            left = self._eval_expr(e.left, env=env, context=context)
            right = self._eval_expr(e.right, env=env, context=context)
            if e.op in ["+", "-", "*", "/", "%", "**", "//"]:
                a = self._to_number(left, ln)
                b = self._to_number(right, ln)
                if e.op == "+":  return a + b
                if e.op == "-":  return a - b
                if e.op == "*":  return a * b
                if e.op == "**": return a ** b
                if e.op == "/":
                    if b == 0:
                        raise VerbaRuntimeError("I cannot divide by zero.", line_no=ln, col=col, line=raw)
                    return a / b
                if e.op == "//":
                    if b == 0:
                        raise VerbaRuntimeError("I cannot divide by zero.", line_no=ln, col=col, line=raw)
                    return float(int(a // b))
                if e.op == "%":
                    if b == 0:
                        raise VerbaRuntimeError("I cannot divide by zero.", line_no=ln, col=col, line=raw)
                    return a % b
            raise VerbaRuntimeError("I did not understand that math operation.", line_no=ln)

        raise VerbaRuntimeError("I did not understand that value.", line_no=ln)

    def _eval_bool(self, b: ast.BoolExpr, *, env: Environment) -> bool:
        ln = b.span.line_no
        col = b.span.col
        raw = b.span.line_content
        if isinstance(b, ast.Compare):
            left = self._eval_expr(b.left, env=env, context="general")
            right = self._eval_expr(b.right, env=env, context="general")
            if b.op == "null":
                return left is None
            if b.op == "!null":
                return left is not None
            if b.op == "in":
                if not isinstance(right, list):
                    raise VerbaRuntimeError("I expected a list after 'in'.", line_no=ln, col=col, line=raw)
                return left in right
            if b.op == "!in":
                if not isinstance(right, list):
                    raise VerbaRuntimeError("I expected a list after 'not in'.", line_no=ln, col=col, line=raw)
                return left not in right
            if b.op in [">", "<", ">=", "<="]:
                a = self._to_number(left, ln)
                c = self._to_number(right, ln)
                if b.op == ">":
                    return a > c
                if b.op == "<":
                    return a < c
                if b.op == ">=":
                    return a >= c
                if b.op == "<=":
                    return a <= c
            if b.op in ["==", "!="]:
                res = left == right
                return res if b.op == "==" else (not res)
            raise VerbaRuntimeError("I did not understand that comparison.", line_no=ln, col=col, line=raw)

        if isinstance(b, ast.BoolNot):
            return not self._eval_bool(b.inner, env=env)
        if isinstance(b, ast.BoolAnd):
            return self._eval_bool(b.left, env=env) and self._eval_bool(b.right, env=env)
        if isinstance(b, ast.BoolOr):
            return self._eval_bool(b.left, env=env) or self._eval_bool(b.right, env=env)
        raise VerbaRuntimeError("I did not understand that condition.", line_no=ln, col=col, line=raw)

    def _call(self, name: str, args: list[ast.Expr], *, caller_env: Environment, line_no: int) -> Any:
        if name not in self.functions:
            raise VerbaRuntimeError(f"I cannot run the function called {name} because it has not been defined.", line_no=line_no)
        fn = self.functions[name]
        # Fill in defaults for missing trailing args
        evaled_args = [self._eval_expr(a, env=caller_env, context="general") for a in args]
        if len(evaled_args) < len(fn.params):
            for p in fn.params[len(evaled_args):]:
                if p in fn.defaults:
                    evaled_args.append(fn.defaults[p])
                else:
                    raise VerbaRuntimeError(
                        f"The function called {name} needs {len(fn.params)} value(s), but you gave {len(args)}.",
                        line_no=line_no,
                    )
        if len(evaled_args) != len(fn.params):
            raise VerbaRuntimeError(
                f"The function called {name} needs {len(fn.params)} value(s), but you gave {len(args)}.",
                line_no=line_no,
            )
        call_env = Environment(parent=self.globals)
        for p, v in zip(fn.params, evaled_args):
            call_env.set(p, v)
        try:
            self._exec_block(fn.body, env=call_env)
        except _ReturnSignal as r:
            return r.value
        return None

    def _call_native_method(self, obj: NativeInstance, method_name: str, args: list[ast.Expr], *, caller_env: Environment, line_no: int) -> Any:
        if method_name not in obj.methods:
            raise VerbaRuntimeError(f"Module '{obj.name}' has no function called '{method_name}'.", line_no=line_no)
        nf = obj.methods[method_name]
        # Evaluate provided args; pad missing optional args with empty string
        evaled = [self._to_word(self._eval_expr(a, env=caller_env, context="general")) for a in args]
        # Build positional call, injecting interpreter where needed
        call_args: list[Any] = []
        arg_i = 0
        for p in nf.params:
            if p == "__interp__":
                call_args.append(self)
            elif arg_i < len(evaled):
                call_args.append(evaled[arg_i])
                arg_i += 1
            else:
                call_args.append("")
        try:
            result = nf.fn(*call_args)
        except Exception as e:
            raise VerbaRuntimeError(str(e), line_no=line_no)
        # Wrap dict results as a NativeInstance so .prop access works
        if isinstance(result, dict):
            ni = NativeInstance(method_name, {})
            ni.props = {k: (str(v) if not isinstance(v, str) else v) for k, v in result.items()}
            return ni
        return result if result is not None else ""

    def _call_method(self, obj: Instance, method_name: str, args: list[ast.Expr], *, caller_env: Environment, line_no: int) -> Any:
        if method_name not in obj.cls.methods:
             raise VerbaRuntimeError(f"Object has no method called {method_name}.", line_no=line_no)
        fn = obj.cls.methods[method_name]
        if len(args) != len(fn.params):
            raise VerbaRuntimeError(
                f"The method called {method_name} needs {len(fn.params)} value(s), but you gave {len(args)}.",
                line_no=line_no,
            )
        call_env = Environment(parent=self.globals)
        call_env.set("self", obj)
        for p, a in zip(fn.params, args):
            call_env.set(p, self._eval_expr(a, env=caller_env, context="general"))
            
        try:
            self._exec_block(fn.body, env=call_env)
        except _ReturnSignal as r:
            return r.value
        return None

    def _to_number(self, v: Any, line_no: int) -> float:
        if isinstance(v, bool):
            return 1.0 if v else 0.0
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v) if "." in v else float(int(v))
            except ValueError:
                pass
        raise VerbaRuntimeError("I expected a number here.", line_no=line_no)

    def _to_word(self, v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, str):
            return v
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            if isinstance(v, float) and v.is_integer():
                return str(int(v))
            return str(v)
        return str(v)

    def _format_value(self, v: Any) -> str:
        if isinstance(v, Pointer):
            return repr(v)
        if isinstance(v, bool):
            return "true" if v else "false"
        if v is None:
            return "nothing"
        if isinstance(v, list):
            return ", ".join(self._format_value(x) for x in v)
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v)
