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


@dataclass
class ClassObj:
    name: str
    methods: dict[str, ast.Define]


class Instance:
    def __init__(self, cls: ClassObj):
        self.cls = cls
        self.props = {}

class _ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value


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
            for _ in range(n):
                self._exec_block(s.body, env=env)
            return

        if isinstance(s, ast.While):
            guard = 0
            while self._eval_bool(s.condition, env=env):
                self._exec_block(s.body, env=env)
                guard += 1
                if guard > 10_000_000:
                    raise VerbaRuntimeError("This loop ran for too long. Did you forget to update the condition?", line_no=ln, col=col, line=raw)
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
                self._exec_block(s.body, env=inner)
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
            self.functions[s.name] = Function(s.name, s.params, s.body)
            return

        if isinstance(s, ast.GiveBack):
            value = self._eval_expr(s.value, env=env, context="general")
            raise _ReturnSignal(value)

        if isinstance(s, ast.Run):
            self._call(s.name, s.args, caller_env=env, line_no=ln)
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
            try:
                self._exec_block(s.try_body, env=env)
            except VerbaRuntimeError as e:
                if s.catch_body is not None:
                    err_env = Environment(parent=env)
                    if s.error_name:
                        err_env.set(s.error_name, str(e))
                    self._exec_block(s.catch_body, env=err_env)
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
            self.classes[s.name] = ClassObj(s.name, s.methods)
            return

        if isinstance(s, ast.ObjectPropSet):
            obj = env.get(s.obj_name)
            if not isinstance(obj, Instance):
                raise VerbaRuntimeError(f"Variable {s.obj_name} is not an object.", line_no=ln, col=col, line=raw)
            val = self._eval_expr(s.value, env=env, context="general")
            obj.props[s.prop] = val
            return

        if isinstance(s, ast.MethodCall):
            obj = env.get(s.obj_name)
            if not isinstance(obj, Instance):
                raise VerbaRuntimeError(f"Variable {s.obj_name} is not an object.", line_no=ln, col=col, line=raw)
            self._call_method(obj, s.method, s.args, caller_env=env, line_no=ln)
            return

        if isinstance(s, ast.LetResultOfMethod):
            obj = env.get(s.obj_name)
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

        raise VerbaRuntimeError("I reached a statement I cannot execute yet.", line_no=ln)

    def _eval_expr(self, e: ast.Expr, *, env: Environment, context: str) -> Any:
        ln = e.span.line_no
        col = e.span.col
        raw = e.span.line_content

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
            if "init" in cls.methods:
                self._call_method(inst, "init", e.args, caller_env=env, line_no=ln)
            elif e.args:
                raise VerbaRuntimeError(f"Class {e.class_name} does not have an init method but arguments were passed.", line_no=ln)
            return inst

        if isinstance(e, ast.ObjectPropGet):
            if e.obj_name == "self":
                obj = env.get("self")
            else:
                obj = env.get(e.obj_name)
            if not isinstance(obj, Instance):
                raise VerbaRuntimeError(f"Variable {e.obj_name} is not an object.", line_no=ln)
            if e.prop in obj.props:
                return obj.props[e.prop]
            return None

        if isinstance(e, ast.Literal):
            return e.value

        if isinstance(e, ast.VarRef):
            if env.contains(e.name):
                return env.get(e.name)
            if context == "say":
                # In output, undefined names are treated as literal words (so "say hello." works).
                return e.name
            raise VerbaRuntimeError(f"The variable called {e.name} has not been defined yet.", line_no=ln, col=col, line=raw)

        if isinstance(e, ast.BinaryOp):
            left = self._eval_expr(e.left, env=env, context=context)
            right = self._eval_expr(e.right, env=env, context=context)
            if e.op in ["+", "-", "*", "/", "%"]:
                a = self._to_number(left, ln)
                b = self._to_number(right, ln)
                if e.op == "+":
                    return a + b
                if e.op == "-":
                    return a - b
                if e.op == "*":
                    return a * b
                if e.op == "/":
                    if b == 0:
                        raise VerbaRuntimeError("I cannot divide by zero.", line_no=ln, col=col, line=raw)
                    return a / b
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
        if len(args) != len(fn.params):
            raise VerbaRuntimeError(
                f"The function called {name} needs {len(fn.params)} value(s), but you gave {len(args)}.",
                line_no=line_no,
            )
        call_env = Environment(parent=self.globals)
        for p, a in zip(fn.params, args, strict=True):
            call_env.set(p, self._eval_expr(a, env=caller_env, context="general"))
        try:
            self._exec_block(fn.body, env=call_env)
        except _ReturnSignal as r:
            return r.value
        return None

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
