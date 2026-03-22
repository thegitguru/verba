from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from . import ast
from .errors import VerbaRuntimeError


from .runtime_types import (
    Pointer, Function, ClassObj, Instance, NativeFunction, NativeInstance, Environment, Module, OptionValue,
    _ReturnSignal, _BreakSignal, _ContinueSignal, _RespondSignal, _RedirectSignal, _VerbaRequest
)


class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self._http_routes: dict[tuple[str, str], tuple] = {}
        self._http_response = None
        self._inject_stdlib()

    # ── stdlib injection ──────────────────────────────────────────────────────

    def _inject_stdlib(self) -> None:
        from .stdlib import http as _http_mod
        from .stdlib import browser as _browser_mod
        from .stdlib import express as _express_mod
        from .stdlib import strings as _strings_mod
        from .stdlib import math as _math_mod
        from .stdlib import json as _json_mod
        from .stdlib import os as _os_mod
        from .stdlib import time as _time_mod
        from .stdlib import env as _env_mod
        from .stdlib import random as _random_mod
        from .stdlib import base64 as _base64_mod
        from .stdlib import regex as _regex_mod
        from .stdlib import datetime as _datetime_mod
        from .stdlib import db as _db_mod
        from .stdlib import crypto as _crypto_mod
        from .stdlib import csv as _csv_mod
        from .stdlib import vibe as _vibe_mod
        from .stdlib import xml as _xml_mod
        from .stdlib import gui as _gui_mod
        from .stdlib import canvas as _canvas_mod
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
            ("random",  _random_mod),
            ("base64",  _base64_mod),
            ("regex",   _regex_mod),
            ("datetime",_datetime_mod),
            ("db",      _db_mod),
            ("crypto",  _crypto_mod),
            ("csv",     _csv_mod),
            ("xml",     _xml_mod),
            ("gui",     _gui_mod),
            ("canvas",  _canvas_mod),
            ("vibe",    _vibe_mod),
        ]:
            needs_interp: set = getattr(mod, "NEEDS_INTERP", set())
            methods = {}
            for fn_name, (fn, params) in mod.FUNCTIONS.items():
                p_list = list(params)
                if fn_name in needs_interp:
                    p_list.append("__interp__")
                methods[fn_name] = NativeFunction(
                    name=fn_name, params=p_list, fn=fn,
                    needs_interp=(fn_name in needs_interp),
                )
            self.globals.set(mod_name, NativeInstance(mod_name, methods))

    def run(self, program: list[ast.Stmt]) -> Any:
        return self._exec_block(program, env=self.globals)

    def _exec_block(self, stmts: list[ast.Stmt], *, env: Environment) -> Any:
        for s in stmts:
            self._exec_stmt(s, env=env)
        return None

    def _has_yield(self, stmts: list[ast.Stmt]) -> bool:
        for s in stmts:
            if isinstance(s, ast.Yield): return True
            if isinstance(s, ast.If):
                if self._has_yield(s.then_body): return True
                if s.else_body and self._has_yield(s.else_body): return True
            if isinstance(s, (ast.Repeat, ast.While, ast.Unless, ast.ForEach, ast.ForEachIndexed, ast.WithStmt, ast.Test)):
                if hasattr(s, 'body') and self._has_yield(s.body): return True
            if isinstance(s, ast.TryBlock):
                if self._has_yield(s.try_body): return True
                if s.catch_body and self._has_yield(s.catch_body): return True
                if s.finally_body and self._has_yield(s.finally_body): return True
            if isinstance(s, ast.Match):
                for b in s.branches:
                    if self._has_yield(b.body): return True
                if s.else_body and self._has_yield(s.else_body): return True
        return False

    def _exec_generator(self, stmts: list[ast.Stmt], *, env: Environment) -> Any:
        for s in stmts:
            if isinstance(s, ast.Yield):
                yield self._eval_expr(s.value, env=env, context="general")
            elif isinstance(s, ast.If):
                if self._eval_bool(s.condition, env=env): yield from self._exec_generator(s.then_body, env=env)
                elif s.else_body: yield from self._exec_generator(s.else_body, env=env)
            elif isinstance(s, ast.Unless):
                if not self._eval_bool(s.condition, env=env): yield from self._exec_generator(s.body, env=env)
            elif isinstance(s, ast.Repeat):
                n = int(self._to_number(self._eval_expr(s.times, env=env, context="general"), s.span.line_no))
                for i in range(n):
                    loop_env = Environment(parent=env)
                    if s.index_name: loop_env.set(s.index_name, i + 1)
                    try: yield from self._exec_generator(s.body, env=loop_env)
                    except _ContinueSignal: pass
                    except _BreakSignal: break
            elif isinstance(s, ast.While):
                while self._eval_bool(s.condition, env=env):
                    try: yield from self._exec_generator(s.body, env=env)
                    except _ContinueSignal: pass
                    except _BreakSignal: break
            elif isinstance(s, ast.ForEach):
                lst = env.get(s.list_name)
                for item in lst:
                    inner = Environment(parent=env)
                    inner.set(s.item_name, item)
                    try: yield from self._exec_generator(s.body, env=inner)
                    except _ContinueSignal: pass
                    except _BreakSignal: break
            else:
                self._exec_stmt(s, env=env)

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

        if isinstance(s, ast.Help):
            topic = s.topic.lower() if s.topic else ""
            if not topic:
                modules = [k for k, v in self.globals.values.items() if isinstance(v, NativeInstance)]
                print("Available modules: " + ", ".join(modules))
                print("Type 'help <name>.' to see documentation for a variable, module, function, or class.")
                return
            
            # 1. Check functions
            f = env.get_function(topic)
            if f:
                print(f"--- HELP: {f.name} ---")
                print(f"Usage: run {f.name} with {', '.join(f.params)}.")
                if f.doc: print(f"Documentation: {f.doc}")
                return
            
            # 2. Check classes
            c = env.get_class(topic)
            if c:
                print(f"--- HELP: class {c.name} ---")
                if c.parent: print(f"Extends: {c.parent.name}")
                print(f"Methods: {', '.join(c.methods.keys())}")
                if c.doc: print(f"Documentation: {c.doc}")
                return

            # 3. Check modules/dotted
            parts = topic.split(".")
            mod_name = parts[0]
            if mod_name in self.globals.values:
                mod = self.globals.get(mod_name)
                if isinstance(mod, NativeInstance):
                    if len(parts) == 1:
                        print(f"--- HELP: module {mod_name} ---")
                        print("Functions: " + ", ".join(mod.methods.keys()))
                    else:
                        fn_name = parts[1]
                        if fn_name in mod.methods:
                            fn = mod.methods[fn_name]
                            print(f"Function: {mod_name}.{fn_name}")
                            print(f"Parameters: {', '.join(fn.params)}")
                        else:
                            print(f"Function '{fn_name}' not found in module '{mod_name}'.")
                    return

            # 4. Fallback check env
            try:
                v = env.get(topic)
                print(f"Variable '{topic}' is of type {type(v).__name__}.")
            except KeyError:
                print(f"I don't know anything about '{topic}'.")
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

        if isinstance(s, ast.Test):
            print(f"Running test \"{s.name}\"...")
            # Run in a fresh env but with globals access
            test_env = Environment(parent=self.globals)
            try:
                 self._exec_block(s.body, env=test_env)
                 print(f"  Result: PASSED.")
            except VerbaRuntimeError as e:
                 print(f"  Result: FAILED: {e}")
            return

        if isinstance(s, ast.WithStmt):
            val = self._eval_expr(s.expr, env=env, context="general")
            with_env = Environment(parent=env)
            with_env.set(s.var_name, val)
            try:
                self._exec_block(s.body, env=with_env)
            finally:
                # If the value has a close method, call it
                if isinstance(val, Instance) and "close" in val.cls.methods:
                    self._call_method(val, "close", [], {}, caller_env=env, line_no=ln)
                elif isinstance(val, NativeInstance) and "close" in val.methods:
                    self._call_native_method(val, "close", [], {}, caller_env=env, line_no=ln)
            return


        if isinstance(s, ast.Match):
            subject_val = self._eval_expr(s.subject, env=env, context="general")
            for br in s.branches:
                if self._match_pattern(br.pattern, subject_val, env):
                    self._exec_block(br.body, env=env)
                    return
            if s.else_body:
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

        if isinstance(s, ast.Unless):
            ok = self._eval_bool(s.condition, env=env)
            if not ok:
                self._exec_block(s.body, env=env)
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
                raise VerbaRuntimeError(f"The iterator called {s.list_name} has not been defined yet.", line_no=ln, col=col, line=raw)
            lst = env.get(s.list_name)
            if not getattr(lst, '__iter__', False):
                raise VerbaRuntimeError(f"The variable called {s.list_name} is not iterable.", line_no=ln, col=col, line=raw)
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
                raise VerbaRuntimeError(f"The iterator called {s.list_name} has not been defined yet.", line_no=ln, col=col, line=raw)
            lst = env.get(s.list_name)
            if not getattr(lst, '__iter__', False):
                raise VerbaRuntimeError(f"The variable called {s.list_name} is not iterable.", line_no=ln, col=col, line=raw)
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
            # The first 'note' statement in the body is the docstring.
            doc = s.doc
            body_stmts = []
            for stmt in s.body:
                if isinstance(stmt, ast.Note) and doc is None:
                    doc = stmt.value
                else:
                    body_stmts.append(stmt)

            # Reconstruct the AST node with the stripped body and found docstring
            # We don't overwrite the AST node in place generally, but here we can
            # just store a modified Function object.
            fn = Function(
                name=s.name,
                params=s.params,
                body=body_stmts,
                decorators=s.decorators,
                doc=doc
            )
            fn.defaults = {k: self._eval_expr(v, env=env, context="general") for k, v in (s.defaults or {}).items()}
            fn.defining_env = env
            # Store scoped to current environment
            env.functions[s.name] = fn
            return

        if isinstance(s, ast.GiveBack):
            if len(s.values) == 1:
                value = self._eval_expr(s.values[0], env=env, context="general")
            else:
                value = [self._eval_expr(v, env=env, context="general") for v in s.values]
            raise _ReturnSignal(value)

        if isinstance(s, ast.Run):
            self._eval_expr(s, env=env, context="general")
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
                    result = self._call(inner.func_name, inner.args, inner.kwargs, caller_env=env, line_no=ln)
                else:
                    obj = env.get(inner.obj_name) if env.contains(inner.obj_name) else None
                    if isinstance(obj, NativeInstance):
                        result = self._call_native_method(obj, inner.method, inner.args, inner.kwargs, caller_env=env, line_no=ln)
                    else:
                        result = self._call_method(obj, inner.method, inner.args, inner.kwargs, caller_env=env, line_no=ln)
            else:
                result = self._eval_expr(rhs, env=env, context="general")
            # Unpack
            if not isinstance(result, list):
                result = [result]
            for i, name in enumerate(s.names):
                env.set(name, result[i] if i < len(result) else None)
            return

        if isinstance(s, ast.LetResultOfRun):
            value = self._call(s.func_name, s.args, s.kwargs, caller_env=env, line_no=ln)
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
            filename = str(self._eval_expr(s.filename, env=env, context="general"))
            if not filename.endswith(".vrb"):
                filename += ".vrb"

            from pathlib import Path
            search_paths = [Path(filename), Path("modules") / filename]
            content = None
            for p in search_paths:
                if p.exists():
                    content = p.read_text(encoding="utf-8")
                    break

            if content is None:
                raise VerbaRuntimeError(f"I could not find the file called {filename}.", line_no=ln, col=col, line=raw)
            
            from .parser import parse
            from .errors import VerbaParseError
            from .runtime_types import Module
            try:
                prog = parse(content)
                if s.alias:
                    # Execute in a fresh global scope (but with access to core globals?)
                    # For simplicity, just fresh
                    mod_env = Environment(parent=self.globals)
                    self._exec_block(prog, env=mod_env)
                    # Bind as a Module object
                    env.set(s.alias, Module(s.alias, mod_env))
                else:
                    # Legacy: execute in current env
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

        if isinstance(s, ast.EnumDef):
            # Enums are objects where members are their own unique identifiers (lowercased for consistency)
            obj = NativeInstance(s.name, {})
            for m in s.members:
                low_m = m.lower()
                obj.props[low_m] = f"{s.name.lower()}.{low_m}"
            env.set(s.name.lower(), obj)
            return

        if isinstance(s, ast.ClassDef):
            parent = env.get_class(s.parent_name) if s.parent_name else None
            if s.parent_name and parent is None:
                raise VerbaRuntimeError(f"Parent class {s.parent_name} has not been defined.", line_no=ln)
            # Inherit parent methods, child overrides take precedence
            merged = dict(parent.methods) if parent else {}
            merged.update(s.methods)
            # Merge fields: parent fields first, then child fields override
            merged_fields = dict(parent.field_defaults or {}) if parent else {}
            merged_fields.update(s.fields or {})
            cls_obj = ClassObj(s.name, merged, parent, doc=s.doc)
            # Evaluate field default expressions and store values
            cls_obj.field_defaults = {
                k: self._eval_expr(v, env=env, context="general")
                for k, v in merged_fields.items()
            }
            env.classes[s.name] = cls_obj
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
            self._eval_expr(s, env=env, context="general")
            return

        if isinstance(s, ast.LetResultOfMethod):
            obj = env.get(s.obj_name) if env.contains(s.obj_name) else None
            val = self._call_method(obj, s.method, s.args, s.kwargs, caller_env=env, line_no=ln)
            env.set(s.target_name, val)
            return

        if isinstance(s, ast.LetResultOfRun):
            val = self._call(s.func_name, s.args, s.kwargs, caller_env=env, line_no=ln)
            env.set(s.target_name, val)
            return

        if isinstance(s, ast.AsyncDefine):
            env.functions[s.name] = s
            return

        if isinstance(s, ast.AsyncRun):
            import threading
            # Background tasks should see everything the current scope sees
            task_env = Environment(parent=env)
            fn_def = env.get_function(s.func_name)
            if not fn_def:
                raise VerbaRuntimeError(f"I don't know a function called {s.func_name}.", line_no=ln)
                
            for p, a in zip(fn_def.params, s.args):
                task_env.set(p, self._eval_expr(a, env=env, context="general"))
                
            task = {"result": None, "done": False, "error": None}
            def _async_worker():
                try:
                    res = None
                    try:
                        self._exec_block(fn_def.body, env=task_env)
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
            # Execute the body if it's a block (registers routes)
            if s.body:
                self._exec_block(s.body, env=env)
                
            import http.server, threading
            port = int(self._to_number(self._eval_expr(s.port, env=env, context="general"), ln))
            interp = self

            class _VerbaHandler(http.server.BaseHTTPRequestHandler):
                def log_message(self, format: str, *args: Any) -> None: pass

                def _dispatch(self, method: str):
                    import urllib.parse
                    parsed   = urllib.parse.urlparse(self.path)
                    path     = parsed.path
                    qs       = urllib.parse.parse_qs(parsed.query)
                    print(f"DEBUG HTTP: method={method} path={path} qs={qs}")
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
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        self._raw_respond(500, "text/plain", f"Server Error: {str(e)}")
                        return
                    # If no respond statement was hit, send empty 200
                    self._raw_respond(200, "text/html", "")

                def _raw_respond(self, status: int, mime: str, body: str):
                    data = body.encode("utf-8")
                    self.send_response(status)
                    self.send_header("Content-Type", mime)
                    self.send_header("Content-Length", str(len(data)))
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

        if isinstance(e, ast.Run):
            return self._call(e.name, e.args, e.kwargs, caller_env=env, line_no=ln)

        if isinstance(e, ast.MethodCall):
            obj = env.get(e.obj_name) if env.contains(e.obj_name) else None
            return self._call_method(obj, e.method, e.args, e.kwargs, caller_env=env, line_no=ln)

        if isinstance(e, ast.SomeLiteral):
            return OptionValue.some(self._eval_expr(e.value, env=env, context="general"))

        if isinstance(e, ast.NoneLiteral):
            return OptionValue.none()

        if isinstance(e, ast.StringConcat):
            return "".join(self._to_word(self._eval_expr(p, env=env, context="say")) for p in e.parts)

        if isinstance(e, ast.ListLength):
            if not env.contains(e.list_name):
                raise VerbaRuntimeError(f"The variable called {e.list_name} has not been defined yet.", line_no=ln)
            lst = env.get(e.list_name)
            if not isinstance(lst, (list, str)):
                raise VerbaRuntimeError(f"The variable called {e.list_name} is not a list or word.", line_no=ln)
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
            cls = env.get_class(e.class_name)
            if cls is None:
                raise VerbaRuntimeError(f"Class {e.class_name} has not been defined.", line_no=ln)
            inst = Instance(cls)
            import copy
            for fname, fval in cls.field_defaults.items():
                inst.props[fname] = copy.deepcopy(fval)
            if "init" in cls.methods:
                self._call_method(inst, "init", e.args, e.kwargs, caller_env=env, line_no=ln)
            elif e.args or e.kwargs:
                raise VerbaRuntimeError(f"Class {e.class_name} does not have an init method but arguments were passed.", line_no=ln)
            return inst

        if isinstance(e, ast.MapLiteral):
            res = {}
            for k_expr, v_expr in e.pairs:
                k = self._eval_expr(k_expr, env=env, context="general")
                v = self._eval_expr(v_expr, env=env, context="general")
                res[k] = v
            return res

        if isinstance(e, ast.ListLiteral):
            return [self._eval_expr(v, env=env, context="general") for v in e.values]

        if isinstance(e, ast.ListComprehension):
            source = self._eval_expr(e.list_expr, env=env, context="general")
            if not isinstance(source, list):
                raise VerbaRuntimeError("Comprenhension 'in' must be followed by a list.", line_no=ln)
            out = []
            for item in source:
                loop_env = Environment(parent=env)
                loop_env.set(e.var_name, item)
                if e.cond_expr is None or self._eval_bool(e.cond_expr, env=loop_env):
                    out.append(self._eval_expr(e.result_expr, env=loop_env, context="general"))
            return out

        if isinstance(e, ast.MapComprehension):
            source = self._eval_expr(e.list_expr, env=env, context="general")
            # maps can be built from lists or other maps
            items = source.items() if isinstance(source, dict) else source
            out = {}
            for item in items:
                loop_env = Environment(parent=env)
                if isinstance(source, dict):
                    loop_env.set(e.key_var, item[0])
                    loop_env.set(e.val_var, item[1])
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    loop_env.set(e.key_var, item[0])
                    loop_env.set(e.val_var, item[1])
                else:
                    loop_env.set(e.key_var, item)
                    loop_env.set(e.val_var, item)
                
                if e.cond_expr is None or self._eval_bool(e.cond_expr, env=loop_env):
                    k = self._eval_expr(e.key_expr, env=loop_env, context="general")
                    v = self._eval_expr(e.val_expr, env=loop_env, context="general")
                    out[k] = v
            return out

        if isinstance(e, ast.ObjectPropGet):
            if e.obj_name == "self":
                obj = env.get("self")
            else:
                obj = env.get(e.obj_name) if env.contains(e.obj_name) else None
            # Walk chained props: e.prop may be "address.city"
            for prop_part in e.prop.split("."):
                if isinstance(obj, NativeInstance):
                    obj = obj.props.get(prop_part)
                elif isinstance(obj, OptionValue):
                    if prop_part == "value":
                        obj = obj.value if obj.has_value else None
                    elif prop_part == "is_some":
                        obj = obj.has_value
                    elif prop_part == "is_none":
                        obj = not obj.has_value
                    else:
                        raise VerbaRuntimeError(f"Option has no property called '{prop_part}'.", line_no=ln)
                elif isinstance(obj, dict):
                    obj = obj.get(prop_part)
                elif isinstance(obj, (Instance, _VerbaRequest, Module)):
                    obj = obj.props.get(prop_part)
                else:
                    raise VerbaRuntimeError(f"Cannot access property '{prop_part}' on a non-object.", line_no=ln)
            return obj

        if isinstance(e, ast.Literal):
            return e.value

        if isinstance(e, ast.VarRef):
            if env.contains(e.name):
                return env.get(e.name)
            
            # Check for class reference
            cls = env.get_class(e.name)
            if cls: return cls
            
            # Check for function reference
            fn = env.get_function(e.name)
            if fn: return fn

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
            
            # String operations
            if e.op == "+" and (isinstance(left, str) or isinstance(right, str)):
                return self._to_word(left) + self._to_word(right)
            if e.op == "*" and isinstance(left, str) and isinstance(right, (int, float)):
                return left * int(right)
            if e.op == "*" and isinstance(right, str) and isinstance(left, (int, float)):
                return right * int(left)

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

    def _match_pattern(self, pattern: ast.MatchPattern, subject: Any, env: Environment) -> bool:
        if isinstance(pattern, ast.ValuePattern):
            expected = self._eval_expr(pattern.value, env=env, context="general")
            return subject == expected
        if isinstance(pattern, ast.VariablePattern):
            # Bind the variable in the match environment
            env.set(pattern.name, subject)
            return True
        if isinstance(pattern, ast.ListPattern):
            if not isinstance(subject, list) or len(subject) != len(pattern.patterns):
                return False
            for p, s in zip(pattern.patterns, subject):
                if not self._match_pattern(p, s, env):
                    return False
            return True
        if isinstance(pattern, ast.MapPattern):
            if not isinstance(subject, dict):
                return False
            for k, p in pattern.pairs:
                if k not in subject:
                    return False
                if not self._match_pattern(p, subject[k], env):
                    return False
            return True
        return False

    def _eval_bool(self, b: ast.BoolExpr, *, env: Environment) -> bool:
        ln = b.span.line_no
        col = b.span.col
        raw = b.span.line_content

        if isinstance(b, ast.BoolExprFromExpr):
            return bool(self._eval_expr(b.expr, env=env, context="general"))
        if isinstance(b, ast.Compare):
            left = self._eval_expr(b.left, env=env, context="general")
            right = self._eval_expr(b.right, env=env, context="general")
            if b.op == "some":
                return isinstance(left, OptionValue) and left.has_value
            if b.op == "!some":
                return not (isinstance(left, OptionValue) and left.has_value)
            if b.op == "none":
                return isinstance(left, OptionValue) and not left.has_value
            if b.op == "!none":
                return not (isinstance(left, OptionValue) and not left.has_value)
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

    def _call(self, name: str, args: list[ast.Expr], kwargs: Optional[dict[str, ast.Expr]] = None, *, caller_env: Environment, line_no: int) -> Any:
        fn = caller_env.get_function(name)
        if fn is None:
            raise VerbaRuntimeError(f"I cannot run the function called {name} because it has not been defined.", line_no=line_no)
        
        evaled_args = [self._eval_expr(a, env=caller_env, context="general") for a in args]
        evaled_kwargs = {k: self._eval_expr(v, env=caller_env, context="general") for k, v in (kwargs or {}).items()}
        
        call_env = Environment(parent=fn.defining_env or self.globals)
        for i, p in enumerate(fn.params):
            if p in evaled_kwargs:
                call_env.set(p, evaled_kwargs[p], local=True)
            elif i < len(evaled_args):
                call_env.set(p, evaled_args[i], local=True)
            elif p in fn.defaults:
                call_env.set(p, fn.defaults[p], local=True)
            else:
                raise VerbaRuntimeError(f"Function {name} missing value for parameter {p}.", line_no=line_no)
                
        # Native Decorators logic
        decs = fn.decorators or []
        if "log" in decs:
            print(f"[LOG] Calling {name} with args={evaled_args} kwargs={evaled_kwargs}")
        
        import time
        start_time = None
        if "time" in decs:
            start_time = time.time()
                
        if self._has_yield(fn.body):
            return self._exec_generator(fn.body, env=call_env)
                
        try:
            res = None
            self._exec_block(fn.body, env=call_env)
        except _ReturnSignal as r:
            res = r.value
            
        if "time" in decs and start_time is not None:
            elapsed = time.time() - start_time
            print(f"[TIME] {name} took {elapsed:.4f} seconds")
            
        return res

    def _call_module_fn(self, mod: Module, name: str, args: list[ast.Expr], kwargs: Optional[dict[str, ast.Expr]], *, caller_env: Environment, line_no: int) -> Any:
        fn = mod.env.functions.get(name) # only get from THAT module
        if fn is None: raise VerbaRuntimeError(f"Module {mod.name} has no function {name}.", line_no=line_no)
        evaled_args = [self._eval_expr(a, env=caller_env, context="general") for a in args]
        evaled_kwargs = {k: self._eval_expr(v, env=caller_env, context="general") for k, v in (kwargs or {}).items()}
        call_env = Environment(parent=fn.defining_env or self.globals) # Modules can see core globals
        for i, p in enumerate(fn.params):
            if p in evaled_kwargs: call_env.set(p, evaled_kwargs[p], local=True)
            elif i < len(evaled_args): call_env.set(p, evaled_args[i], local=True)
            elif p in fn.defaults: call_env.set(p, fn.defaults[p], local=True)
            else:
                raise VerbaRuntimeError(f"Module function {name} missing value for parameter {p}.", line_no=line_no)
        try:
            self._exec_block(fn.body, env=call_env)
        except _ReturnSignal as r:
            return r.value
        return None

    def _call_method(self, obj: Any, name: str, args: list[ast.Expr], kwargs: Optional[dict[str, ast.Expr]] = None, *, caller_env: Environment, line_no: int) -> Any:
        if isinstance(obj, OptionValue):
            return self._call_option_method(obj, name, args, kwargs, caller_env=caller_env, line_no=line_no)
        if isinstance(obj, NativeInstance):
            return self._call_native_method(obj, name, args, kwargs, caller_env=caller_env, line_no=line_no)
        if isinstance(obj, Module):
            return self._call_module_fn(obj, name, args, kwargs, caller_env=caller_env, line_no=line_no)
        if not isinstance(obj, Instance):
            raise VerbaRuntimeError(f"Cannot call method {name} on non-object.", line_no=line_no)
        
        cls = obj.cls
        while cls and name not in cls.methods:
            cls = cls.parent
        if not cls:
            raise VerbaRuntimeError(f"Object has no method called {name}.", line_no=line_no)
            
        fn = cls.methods[name]
        evaled_args = [self._eval_expr(a, env=caller_env, context="general") for a in args]
        evaled_kwargs = {k: self._eval_expr(v, env=caller_env, context="general") for k, v in (kwargs or {}).items()}
        
        call_env = Environment(parent=fn.defining_env or self.globals)
        call_env.set("self", obj)
        for i, p in enumerate(fn.params):
            if p in evaled_kwargs:
                call_env.set(p, evaled_kwargs[p], local=True)
            elif i < len(evaled_args):
                call_env.set(p, evaled_args[i], local=True)
            elif p in fn.defaults:
                call_env.set(p, fn.defaults[p], local=True)
            # note: 'init' often has defaults handled by ClassDef, but we stick to this for consistency
            
        try:
            self._exec_block(fn.body, env=call_env)
        except _ReturnSignal as r:
            return r.value
        return None

    def _call_native_method(self, obj: NativeInstance, method_name: str, args: list[ast.Expr], kwargs: Optional[dict[str, ast.Expr]] = None, *, caller_env: Environment, line_no: int) -> Any:
        if method_name not in obj.methods:
            raise VerbaRuntimeError(f"Module '{obj.name}' has no function called '{method_name}'.", line_no=line_no)
        nf = obj.methods[method_name]
        
        evaled_args = [self._eval_expr(a, env=caller_env, context="general") for a in args]
        evaled_kwargs = {k: self._eval_expr(v, env=caller_env, context="general") for k, v in (kwargs or {}).items()}
        
        call_args: list[Any] = []
        arg_i = 0
        for p in nf.params:
            if p == "__interp__":
                call_args.append(self)
            elif p in evaled_kwargs:
                call_args.append(evaled_kwargs[p])
            elif arg_i < len(evaled_args):
                call_args.append(evaled_args[arg_i])
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

    def _call_option_method(self, obj: OptionValue, method_name: str, args: list[ast.Expr], kwargs: Optional[dict[str, ast.Expr]] = None, *, caller_env: Environment, line_no: int) -> Any:
        evaled_args = [self._eval_expr(a, env=caller_env, context="general") for a in args]
        if method_name == "is_some":
            return obj.has_value
        if method_name == "is_none":
            return not obj.has_value
        if method_name == "unwrap":
            if not obj.has_value:
                raise VerbaRuntimeError("Cannot unwrap an empty option.", line_no=line_no)
            return obj.value
        if method_name == "unwrap_or":
            if obj.has_value:
                return obj.value
            return evaled_args[0] if evaled_args else None
        if method_name == "or_else":
            if obj.has_value:
                return obj
            if not evaled_args:
                raise VerbaRuntimeError("option.or_else needs a fallback value.", line_no=line_no)
            return OptionValue.some(evaled_args[0])
        raise VerbaRuntimeError(f"Option has no method called {method_name}.", line_no=line_no)


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
        if isinstance(v, OptionValue):
            if v.has_value:
                return f"some({self._to_word(v.value)})"
            return "none"
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
        if isinstance(v, OptionValue):
            if v.has_value:
                return f"some({self._format_value(v.value)})"
            return "none"
        if isinstance(v, bool):
            return "true" if v else "false"
        if v is None:
            return "nothing"
        if isinstance(v, list):
            return ", ".join(self._format_value(x) for x in v)
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v)
