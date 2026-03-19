from __future__ import annotations
import math as _math
import random as _random


def math_floor(n: str) -> int:
    return _math.floor(float(n))

def math_ceil(n: str) -> int:
    return _math.ceil(float(n))

def math_round(n: str, digits: str = "0") -> float:
    result = round(float(n), int(digits))
    return int(result) if int(digits) == 0 else result

def math_abs(n: str) -> float:
    return abs(float(n))

def math_sqrt(n: str) -> float:
    v = float(n)
    if v < 0:
        raise RuntimeError("Cannot take square root of a negative number.")
    return _math.sqrt(v)

def math_power(base: str, exp: str) -> float:
    return float(base) ** float(exp)

def math_log(n: str, base: str = "") -> float:
    v = float(n)
    if base == "":
        return _math.log(v)
    return _math.log(v, float(base))

def math_sin(n: str) -> float:
    return _math.sin(float(n))

def math_cos(n: str) -> float:
    return _math.cos(float(n))

def math_tan(n: str) -> float:
    return _math.tan(float(n))

def math_random() -> float:
    return _random.random()

def math_random_int(low: str, high: str) -> int:
    return _random.randint(int(float(low)), int(float(high)))

def math_min(a: str, b: str) -> float:
    return min(float(a), float(b))

def math_max(a: str, b: str) -> float:
    return max(float(a), float(b))

def math_pi() -> float:
    return _math.pi


FUNCTIONS: dict[str, tuple] = {
    "floor":      (math_floor,      ["n"]),
    "ceil":       (math_ceil,       ["n"]),
    "round":      (math_round,      ["n", "digits"]),
    "abs":        (math_abs,        ["n"]),
    "sqrt":       (math_sqrt,       ["n"]),
    "power":      (math_power,      ["base", "exp"]),
    "log":        (math_log,        ["n", "base"]),
    "sin":        (math_sin,        ["n"]),
    "cos":        (math_cos,        ["n"]),
    "tan":        (math_tan,        ["n"]),
    "random":     (math_random,     []),
    "random_int": (math_random_int, ["low", "high"]),
    "min":        (math_min,        ["a", "b"]),
    "max":        (math_max,        ["a", "b"]),
    "pi":         (math_pi,         []),
}
