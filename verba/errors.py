from __future__ import annotations


class VerbaError(Exception):
    def __init__(self, message: str, *, line_no: int | None = None, col: int | None = None, line: str | None = None, hint: str | None = None):
        self.message = message
        self.line_no = line_no
        self.col = col
        self.line = line
        self.hint = hint
        super().__init__(self.format_error())

    def format_error(self) -> str:
        res = []
        if self.line_no is not None:
            res.append(f"Error on line {self.line_no}:")
        else:
            res.append("Error:")
        
        res.append(f"  {self.message}")
        
        if self.line is not None:
            res.append("")
            res.append(f"    {self.line}")
            if self.col is not None:
                # Account for indentation in the display
                pointer = " " * (self.col + 4) + "^"
                res.append(pointer)
        
        if self.hint:
            res.append(f"\n  Hint: {self.hint}")
            
        return "\n".join(res)


class VerbaParseError(VerbaError):
    pass


class VerbaRuntimeError(VerbaError):
    pass
