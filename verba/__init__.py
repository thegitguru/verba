"""Verba — a natural English programming language."""

def main():
    from .cli import main as _main
    return _main()

__all__ = ["main"]
