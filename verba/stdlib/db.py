import sqlite3
import os

class _DBConn:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row

    def execute(self, sql, args=None):
        try:
            if args == "" or args is None:
                params = []
            else:
                params = args if isinstance(args, list) else [args]
            cursor = self.conn.execute(sql, params)
            self.conn.commit()
            return cursor.rowcount
        except Exception as e:
            print(f"DB Execute Error: {e} | SQL: {repr(sql)} | Args: {repr(args)}")
            return str(e)

    def query(self, sql, args=None):
        try:
            if args == "" or args is None:
                params = []
            else:
                params = args if isinstance(args, list) else [args]
            cursor = self.conn.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"DB Query Error: {e} | SQL: {sql} | Args: {args}")
            return str(e)
            
    def close(self):
        self.conn.close()

# These will be set by the Interpreter during injection or we can import them
# but circular imports are a risk. We'll use a late import or a helper.

def db_open(path, __interp__=None):
    from verba.runtime_types import NativeInstance, NativeFunction
    if not isinstance(path, str):
        path = str(path)
    
    conn = _DBConn(path)
    
    methods = {}
    methods["execute"] = NativeFunction("execute", ["sql", "args"], conn.execute)
    methods["query"]   = NativeFunction("query",   ["sql", "args"], conn.query)
    methods["close"]   = NativeFunction("close",   [],             conn.close)
    
    return NativeInstance("db_connection", methods)

NEEDS_INTERP = {"open"}

FUNCTIONS = {
    "open": (db_open, ["path"]),
}
