# 🗣️ Verba — A Natural English Programming Language

**Verba** is an interpreted, English-like programming language designed to be readable by anyone, even without a programming background. Code reads like instructions you'd give a person. Every statement ends with a period `.` (or a colon `:` for blocks).

```verba
/- A simple greeting program.

ask the user "What is your name?" and save to name.
say "Hello, {name}!".

score = 10.
score = score + 5 * 2.

if score > 15:
    say "Great score!".
else:
    say "Keep going!".
end.
```

---

## 📦 Installation

**Requirements:** Python 3.10+

```bash
# Run directly from source (no install needed)
python -m verba run yourfile.vrb

# Or install as a command-line tool
pip install -e .
verba run yourfile.vrb
```

---

## 🚀 CLI Commands

| Command | Description |
|---|---|
| `verba run <file.vrb>` | Run a Verba script |
| `verba watch <file.vrb>`| Watch a Verba script and re-run automatically on changes (Hot Reload) |
| `verba check <file.vrb>` | Parse only — syntax check without running |
| `verba repl` | Start an interactive REPL |
| `verba format <file.vrb>` | Auto-format script with 4-space indentation |
| `verba init <name>` | Initialize a new Verba project directory with scaffolding |
| `verba list` | List currently installed local packages in `modules/` |
| `verba search <query>`| Search for a package in the Verba registry by name. |
| `verba install <pkg/url>`| Download & install a `.vrb` package from the registry or a direct URL into `modules/`. If no package is passed, downloads all `dependencies` given in `verba.json` |
| `verba update <pkg>`| Update a package (or all packages) by verifying against the registry versions |
| `verba remove <pkg>` | Remove an installed package from `modules/` and `verba.json` |

---

## 📖 Language Reference

### Comments

```verba
/- This is a single-line comment.
# This is also a single-line comment.

/--
  This is a block comment.
  It can span multiple lines.
--/
```

### Notes (Inline Docs / Docstrings)

`note` is a special statement that works as a human-readable inline comment or docstring. It does not require a period terminator and is evaluated at parse-time only (not executed).

```verba
note This function computes the square of a number.

define square needing n:
    note Returns n multiplied by itself.
    give n * n.
end.
```

The first `note` inside a `define` or `class` block becomes the official **docstring** shown by `help`.

---

### Variables & Assignment

```verba
name = "Alice".
age = 30.
is_admin = true.
score = 10 + 5 * 2.     /- supports +, -, *, /, %, **
quotient = 10 / 3.
modulo = 10 % 3.
power = 2 ** 8.
floor_div = 10 // 3.    /- integer (floor) division
maybe_name = some "Verba".
missing_name = none.
```

### Null Safety & Option Types

Verba now supports first-class option values for places where a value may or may not exist.

```verba
name = some "Verba".
missing = none.

if name is some:
    safe_name = the result of running name.unwrap.
    say "Resolved name: ", safe_name.
end.

fallback = the result of running missing.unwrap_or with "Anonymous".
say fallback.
```

Use these checks:

- `is some`
- `is not some`
- `is none`
- `is not none`
- `is null`
- `is not null`

Use these Option methods:

- `option.is_some`
- `option.is_none`
- `option.unwrap`
- `option.unwrap_or with fallback`
- `option.or_else with fallback_option`
- `option.map with callback`
- `option.filter with predicate`
- `option.and_then with callback` (bind)

### String Interpolation

Double-quoted strings support `{variable}` interpolation. Single-quoted strings are raw literals.

```verba
user = "Alice".
greeting = "Hello, {user}!".     /- → "Hello, Alice!"
obj_prop = "City: {address.city}".  /- nested property access in string
raw = 'No {interpolation} here'.
joined = join "Hello, ", user, "!".   /- explicit concatenation
```

To write a literal brace inside an interpolated string, double it: `{{` or `}}`.

### Output

```verba
say "Hello, world!".                   /- prints with newline
display "no newline ".                 /- prints without newline (alias: print)
say "a", " ", "b", " ", "c".          /- prints multiple values on one line
say.                                   /- prints a blank line
```

### User Input

```verba
ask for name.
ask the user "What is your name?" and save to name.
```

### Arithmetic & Compound Assignment

```verba
x = 10.
x += 5.
x -= 2.
x *= 3.
x /= 2.
```

Compound assignment also works on object properties:
```verba
player.score += 10.
```

### Conditions

```verba
if score > 90:
    say "A grade".
else if score > 70:
    say "B grade".
otherwise:
    say "Try harder!".
end.

unless name == "Alice":
    say "Access denied.".
end.
```

**Comparison operators:** `==`, `!=`, `<`, `>`, `<=`, `>=`, `is null`, `is not null`, `is some`, `is not some`, `is none`, `is not none`, `in`, `not in`

**Aliases:** `is` → `==`, `is not` → `!=`, `is greater than` → `>`, `is less than` → `<`, `is at least` → `>=`, `is at most` → `<=`, `does not equal` → `!=`

### Logical Operators

Support: `and`, `or`, `not`, `<`, `>`, `<=`, `>=`, `==`. `!=`.

Additionally, Verba supports Python-style `!null` (is not null) and `null` (is null) shorthand:
```verba
if player !null:
    say "Ready!".
end.
```

### Loops

```verba
/- while loop
counter = 1.
while counter <= 5:
    say counter.
    counter += 1.
end.

/- repeat N times (with optional index variable)
repeat 3 times:
    say "hello".
end.

repeat 5 times with i:
    say "step ", i.
end.

/- for each in list
colors = a list of red, green, blue.
for color in colors:
    say color.
end.

/- for each with index (1-based)
for item at index in colors:
    say index, ": ", item.
end.

/- numeric range
for i from 1 to 10:
    say i.
end.

for i from 0 to 100 step 10:
    say i.
end.
```

**Loop control:**
```verba
stop.   /- break out of a loop
skip.   /- continue to next iteration
```

---

## 📋 Lists

```verba
nums = a list of 1, 2, 3, 4.
add 5 to nums.
remove 2 from nums.

/- access by index (1-based)
get item 1 from nums into first.

/- length
n = length of nums.

/- sort
sort nums.
sort nums descending.

/- slicing
first 3 of nums into top3.
last 2 of nums into bottom2.

/- list literal shorthand
squares = [1, 4, 9, 16].

/- `doubled = x * 2 for x in nums` (comprehension).

#### Modern Functional Methods
```verba
define square needing n: give n * n. end.
items = [1, 2, 3, 4, 5].

/- Transform and Filter
squares = the result of running items.map with square.
odds = the result of running items.filter with (define checking needing n: give n % 2 == 1. end.).

/- Aggregation
total = the result of running items.sum.
has_large = the result of running items.any with (define checking needing x: give x > 4. end.).
csv = the result of running items.join with ", ".
```

**Supported List Methods:** `map`, `filter`, `reduce`, `any`, `all`, `sum`, `join`, `count`.
```

---

## 🗺️ Maps (Dictionaries)

```verba
/- map literal
user = {"name": "Alice", "age": 30}.

/- access
say user.name.

/- set a key
user.email = "alice@example.com".

/- map literal with expression values
config = a map of
    host: "localhost",
    port: 8080.

/- map comprehension (key: value for k, v in source)
counts = k: (length of v) for k, v in data.

#### Modern Functional Methods
```verba
prices = {"Apple": 10, "Banana": 5}.
expensive = the result of running prices.filter with (define check needing k, v: give v > 5. end.).
keys = the result of running prices.keys.
price = the result of running prices.get with "Apple", 0.
```

**Supported Map Methods:** `map`, `filter`, `keys`, `values`, `get`, `has`, `count`.
```

---

## 🔧 Functions

```verba
define greet needing name:
    say "Hello, ", name.
end.

run greet with "Alice".

/- return a value
define square needing n:
    give n * n.
end.

result = the result of running square with 5.

/- multiple return values
define min_max needing a, b:
    give a, b.
end.

low, high = the result of running min_max with 1, 100.

/- default parameters
define greet_with_title needing name, title = "Dr.":
    say title, " ", name.
end.

/- keyword arguments (named params)
run greet_with_title with name = "Alice", title = "Prof.".

/- recursive
define factorial needing n:
    if n <= 1:
        give 1.
    end.
    give n * (the result of running factorial with n - 1).
end.
```

---

## 🎭 Generators (`yield`)

Functions that use `yield` become generators — they return a lazy stream of values.

```verba
define count_up needing limit:
    i = 1.
    while i <= limit:
        yield i.
        i += 1.
    end.
end.

gen = the result of running count_up with 5.
for n in gen:
    say n.
end.
```

---

## 🏗️ Classes & Objects

```verba
class Animal:
    name = "unnamed".

    define init needing given_name:
        self.name = given_name.
    end.

    define speak:
        say self.name, " makes a sound.".
    end.
end.

class Dog extends Animal:
    define speak:
        say self.name, " says: Woof!".
    end.
end.

dog = new Dog with "Rex".
run dog.speak.
say dog.name.
```

---

## 🧩 Pattern Matching (`match`)

```verba
match status:
    when 200:
        say "OK".
    when 404:
        say "Not found".
    else:
        say "Other status".
end.

/- list pattern destructuring
match point:
    when [0, 0]:
        say "Origin".
    when [x, 0]:
        say "On x-axis at ", x.
end.

/- map pattern destructuring
match user:
    when {"role": "admin"}:
        say "Admin access".
    else:
        say "Regular user".
end.
```

---

## 🏷️ Enums

```verba
enum Color:
    Red, Green, Blue.
end.

current = color.red.
say current.            /- → "color.red"

if current == color.red:
    say "It's red!".
end.
```

---

## 🔗 Pointers & References

```verba
x = 42.
ptr = &x.               /- take a reference

say deref ptr.          /- read through pointer → 42
deref ptr = 100.        /- write through pointer — also changes x
say x.                  /- → 100

/- null checks
p = null.
if p is null:
    say "no pointer".
end.

/- pass by reference to a function
define double_it needing n:
    deref n = deref n * 2.
end.

val = 5.
run double_it with &val.
say val.                /- → 10
```

---

## 🎨 Decorators

Decorators wrap functions with built-in behaviours. Apply them with `@decorator_name` above a `define` block.

Built-in decorators:
| Decorator | Effect |
|---|---|
| `@log` | Logs function name, args, and kwargs on every call |
| `@time` | Prints execution time after each call |

```verba
@log
@time
define compute needing n:
    give n * n.
end.

res = the result of running compute with 10.
```

---

## 📦 Modules & Namespaces

```verba
/- import a .vrb file (executed in a fresh scope)
import from file called "my_module.vrb" as mh.

/- call imported functions
result = the result of running mh.multiply_things with 3, 4.

/- access imported variables
say mh.version.
```

Modules are placed in the `modules/` folder and loaded by name.

---

## 🪟 With Statement (Scoped Binding)

The `with` statement binds an expression to a variable for the duration of its block. If the bound value has a `close` method it is called automatically on exit.

```verba
with the result of running db.open with "data.sqlite" as conn:
    run conn.execute with "SELECT 1".
end.
/- conn.close is called automatically here
```

---

## 🔍 Help System

```verba
help.                   /- lists all available modules
help strings.           /- shows all functions in the strings module
help strings.upper.     /- shows parameters for strings.upper
help myFunction.        /- shows docstring and usage for your function
help MyClass.           /- shows methods for a class
```

---

## 🗑️ Freeing Variables

```verba
temp = "I am temporary".
free temp.          /- removes temp from the current scope
delete temp.        /- alias for free
```

---

## 🛡️ Error Handling

```verba
try:
    result = 10 / 0.
on error saving to err:
    say "Caught: ", err.
finally:
    say "cleanup done".
end.

/- on error without capturing the error message
try:
    raise "Something went wrong.".
on error:
    say "An error occurred.".
end.

/- raise an error explicitly
raise "Something went wrong.".
```

---

## ⚡ Async Programming

```verba
async define fetch_data as follows:
    fetch "https://example.com" into html.
    give html.
end.

task = async run fetch_data.
await result = task.
say result.
```

---

## 📁 File I/O

```verba
save "Hello, world!" to file called "output.txt".
load file called "output.txt" into content.
append " More text." to file called "output.txt".
delete file called "output.txt".
```

---

## 🌐 HTTP Client (`http` module)

```verba
res = the result of running http.get with "https://httpbin.org/get".
say res.status.
say res.body.

/- POST form data
form = the result of running http.encode_form with '{"key":"val"}'.
res2 = the result of running http.post with "https://httpbin.org/post", form.

/- POST JSON
res3 = the result of running http.post_json with "https://httpbin.org/post", '{"hello":"Verba"}'.

/- build URL with query params
url = the result of running http.encode_url with "https://httpbin.org/get", '{"q":"verba"}'.
```

---

## 🖥️ HTTP Server (built-in)

```verba
on route "/" with method "GET":
    respond with "<h1>Hello from Verba!</h1>" status 200 type "text/html".
end.

on route "/echo" with method "POST":
    msg = request.body.
    respond with msg status 200 type "text/plain".
end.

on route "/old" with method "GET":
    redirect to "/" status 301.
end.

serve on port 5000.
```

**Request object properties:** `request.body`, `request.method`, `request.path`, `request.query_<name>`, `request.form_<name>`

---

## 🚂 Express-style Router (`express` module)

```verba
run express.use with "static_dir", "/static".     /- serve static files

define handle_home:
    respond with "<h1>Home</h1>" status 200 type "text/html".
end.

run express.get with "/", "handle_home".
run express.get with "/users/:id", "handle_user".   /- :id captured as request.param_id
run express.post with "/echo", "handle_echo".

run express.listen with "5000".
```

---

## 🧪 Built-in Testing Framework

```verba
test "math works":
    a = 10 + 5 * 2.
    assert a == 20.
end.

test "with message":
    assert 1 == 1 saying "one should equal one".
end.
```

Run the test suite:
```bash
verba run test_suite.vrb
```

---

## 📚 Standard Library

All modules are available by default — no imports needed.

### `strings` — String Manipulation
| Function | Description |
|---|---|
| `strings.length` with `s` | Character count |
| `strings.upper` with `s` | Uppercase |
| `strings.lower` with `s` | Lowercase |
| `strings.trim` with `s` | Strip whitespace |
| `strings.contains` with `s, sub` | Returns `"true"` or `"false"` |
| `strings.starts_with` with `s, prefix` | Prefix check |
| `strings.ends_with` with `s, suffix` | Suffix check |
| `strings.replace` with `s, old, new` | Replace all occurrences |
| `strings.split` with `s, sep` | Split into a list |
| `strings.index_of` with `s, sub` | First index of substring (-1 if not found) |
| `strings.slice` with `s, start, end` | Substring by index |
| `strings.to_number` with `s` | Parse to number |
| `strings.repeat` with `s, times` | Repeat string N times |

### `math` — Mathematics
| Function | Description |
|---|---|
| `math.floor` with `n` | Floor |
| `math.ceil` with `n` | Ceiling |
| `math.round` with `n, digits` | Round |
| `math.abs` with `n` | Absolute value |
| `math.sqrt` with `n` | Square root |
| `math.power` with `base, exp` | Exponentiation |
| `math.log` with `n, base` | Logarithm (natural if base omitted) |
| `math.sin / cos / tan` with `n` | Trig functions (radians) |
| `math.random` | Random float 0..1 |
| `math.random_int` with `low, high` | Random integer in range |
| `math.min / max` with `a, b` | Min/Max of two values |
| `math.pi` | π constant |

### `db` — SQLite Database
```verba
conn = the result of running db.open with "mydata.sqlite".
run conn.execute with "CREATE TABLE IF NOT EXISTS users (id INT, name TEXT)".
run conn.execute with "INSERT INTO users VALUES (1, 'Alice')".
rows = the result of running conn.query with "SELECT * FROM users".
say (length of rows).
run conn.close.
```

### `crypto` — Security & Hashing
| Function | Description |
|---|---|
| `crypto.hash` with `text, alg` | Hash text (SHA-256 by default) |
| `crypto.generate_token` with `n` | Secure random hex token of `n` bytes |
| `crypto.encrypt` with `text, key` | XOR + Base64 encryption |
| `crypto.decrypt` with `text, key` | Decrypt XOR + Base64 |

```verba
hash = the result of running crypto.hash with text = "my secret".
token = the result of running crypto.generate_token with n = 32.
```

### `json` — JSON Parsing & Building
| Function | Description |
|---|---|
| `json.parse` with `s` | Parse JSON string → dict/list |
| `json.get` with `obj, key` | Get key from object or JSON string |
| `json.set` with `json, key, value` | Return updated JSON string |
| `json.build` with `k1, v1, ...` | Build JSON from key-value pairs (up to 6 pairs) |
| `json.stringify` with `value` | Wrap value as JSON string |
| `json.has` with `json, key` | Returns `"true"` / `"false"` |
| `json.keys` with `json` | Returns a list of all keys |
| `json.arr_len` with `json` | Length of JSON array |
| `json.arr_item` with `json, index` | Get item at index from JSON array |

### `csv` — CSV Files
```verba
rows = the result of running csv.read with "data.csv".
for row in rows:
    say row.name.          /- each row is accessible as an object
end.

run csv.write with "out.csv", rows.
```

### `xml` — XML Parsing
```verba
parsed = the result of running xml.parse with "<root><item>hello</item></root>".
say parsed.tag.             /- → "root"
found = the result of running xml.find with parsed, "item".
say found.text.             /- → "hello"
```

### `http` — HTTP Client
*(See HTTP Client section above)*

### `browser` — Web Scraping (stdlib only, no Playwright)
| Function | Description |
|---|---|
| `browser.open` with `url` | Fetch URL, store page |
| `browser.goto` with `url` | Alias for open |
| `browser.read` with `selector` | Read text from CSS tag (e.g. `"h1"`) |
| `browser.read_html` with `selector` | Read raw inner HTML |
| `browser.title` | Get page title |
| `browser.url` | Get current URL |
| `browser.wait` with `ms` | Sleep for N milliseconds |
| `browser.wait_for` with `selector` | Assert element exists |
| `browser.close` | Reset browser state |

```verba
title = the result of running browser.open with "https://example.com".
heading = the result of running browser.read with "h1".
say heading.
```

### `os` — File System
| Function | Description |
|---|---|
| `os.exists` with `path` | Check if path exists |
| `os.is_file / is_dir` with `path` | Type check |
| `os.list` with `path` | List directory contents |
| `os.mkdir` with `path` | Create directory |
| `os.remove` with `path` | Delete file or directory |
| `os.rename` with `src, dst` | Rename/move |
| `os.cwd` | Current working directory |
| `os.join` with `a, b` | Join paths |
| `os.basename / dirname` with `path` | Path components |
| `os.size` with `path` | File size in bytes |

### `time` — Date & Time
| Function | Description |
|---|---|
| `time.now` | Unix timestamp (seconds) |
| `time.sleep` with `ms` | Sleep for milliseconds |
| `time.format` with `timestamp, fmt` | Format timestamp (strftime format) |
| `time.year / month / day` | Current date parts |
| `time.hour / minute / second` | Current time parts |
| `time.since` with `timestamp` | Elapsed seconds since timestamp |

### `datetime` — Datetime Objects
| Function | Description |
|---|---|
| `datetime.now` with `format` | Current datetime, optional format string |
| `datetime.parse` with `text, layout` | Parse datetime string |
| `datetime.format` with `iso_str, layout` | Format ISO datetime string |

### `random` — Randomness
| Function | Description |
|---|---|
| `random.number` with `min, max` | Random integer in range |
| `random.choice` with `list` | Random element from list |
| `random.shuffle` with `list` | Shuffled copy of list |

### `regex` — Regular Expressions
| Function | Description |
|---|---|
| `regex.match` with `pattern, text` | True if pattern matches start of text |
| `regex.search` with `pattern, text` | True if pattern found anywhere |
| `regex.replace` with `pattern, replacement, text` | Regex replace |

### `base64` — Encoding
| Function | Description |
|---|---|
| `base64.encode` with `text` | Base64 encode |
| `base64.decode` with `text` | Base64 decode |

### `env` — Environment Variables
| Function | Description |
|---|---|
| `env.get` with `key, default` | Read env var (returns default if not set) |
| `env.set` with `key, value` | Set env var |
| `env.has` with `key` | Returns `"true"` / `"false"` |
| `env.all` | Returns list of all `key=value` strings |

### `vibe` — WebSockets
```verba
conn = the result of running vibe.open with "ws://localhost:8080".
run conn.send with "Hello, server!".
msg = the result of running conn.receive.
say msg.
run conn.close.
```

### `gui` — Desktop UI (Tkinter)
```verba
win = the result of running gui.window with "My App".
run win.label with "Hello, Verba!".
run win.button with "Click me", "on_click".
inp = the result of running win.input with "Your name".
run win.show.

/- inside a callback:
define on_click:
    name = the result of running win.get with "Your name".
    say "Hello, ", name.
end.
```

### `canvas` — 2D Drawing & Animation

Provieds a Tkinter-backed drawing canvas with primitives, event handling, and animation loops.

```verba
/- Create a 800×600 canvas window
c = the result of running canvas.new with "My Drawing", 800, 600.
run c.background with "#1e1e2e".

/- Draw shapes
run c.rect with 50, 50, 200, 100, fill = "#a6e3a1".
run c.circle with 400, 300, 60, fill = "#cba6f7", outline = "#b4befe".
run c.line with 0, 0, 800, 600, color = "#f38ba8", width = 2.
run c.polygon with "100,50,200,200,0,200", fill = "#89dceb".
run c.text with 10, 10, "Hello Verba!", color = "#cdd6f4", size = 20.
run c.arc with 200, 200, 80, 0, 270, outline = "#fab387", width = 3.

/- Event handling
run c.on_click with "handle_click".    /- sets canvas_x, canvas_y globals
run c.on_key with "handle_key".        /- sets canvas_key global

define handle_click:
    run c.circle with canvas_x, canvas_y, 20, fill = "#f9e2af".
end.

/- Animation loop at 60 FPS
ball_x = 400.
ball_vx = 4.
define update:
    run c.clear.
    ball_x += ball_vx.
    if ball_x > 780: ball_vx = 0 - ball_vx. end.
    if ball_x < 20:  ball_vx = 0 - ball_vx. end.
    run c.circle with ball_x, 300, 20, fill = "#cba6f7".
end.
run c.loop with "update", 60.
```

| Method | Description |
|---|---|
| `canvas.new` with `title, width, height` | Create a new canvas window |
| `c.background` with `color` | Fill background with color (hex string) |
| `c.rect` with `x, y, w, h, fill, outline, width` | Draw a rectangle |
| `c.circle` with `cx, cy, r, fill, outline, width` | Draw a circle |
| `c.ellipse` with `cx, cy, rx, ry, fill, outline` | Draw an ellipse |
| `c.line` with `x1, y1, x2, y2, color, width` | Draw a line |
| `c.polygon` with `"x1,y1,x2,y2,...", fill, outline` | Draw a filled polygon |
| `c.arc` with `x, y, r, start, extent, fill, outline, width` | Draw an arc segment |
| `c.text` with `x, y, text, color, size, font, bold` | Draw text |
| `c.image` with `x, y, path` | Draw a PNG/GIF image |
| `c.move` with `id, dx, dy` | Move a drawn item by delta |
| `c.delete` with `id` | Remove a specific item |
| `c.clear` | Remove all items |
| `c.on_click` with `callback` | Bind left-click (sets `canvas_x`, `canvas_y`) |
| `c.on_key` with `callback` | Bind key press (sets `canvas_key`) |
| `c.on_motion` with `callback` | Bind mouse move (sets `canvas_x`, `canvas_y`) |
| `c.loop` with `callback, fps` | Run animation loop at given FPS |
| `c.update` | Push pending draws (non-blocking refresh) |
| `c.save` with `path` | Save as PostScript file |
| `c.show` | Open window (blocking until closed) |
| `c.close` | Destroy window |

---


```
verba/
├── ast.py           — Abstract Syntax Tree node definitions
├── tokenize.py      — Lexer / tokenizer
├── parser.py        — Parser (tokens → AST)
├── runtime.py       — Interpreter / evaluator
├── runtime_types.py — Runtime types (Environment, Function, Instance, etc.)
├── errors.py        — VerbaParseError, VerbaRuntimeError
├── cli.py           — CLI entry point (run, check, repl, format, install)
└── stdlib/
    ├── strings.py   — String functions
    ├── math.py      — Math functions
    ├── json.py      — JSON parsing & building
    ├── http.py      — HTTP client
    ├── browser.py   — Web scraping (stdlib, no Playwright)
    ├── os.py        — Filesystem
    ├── time.py      — Time & date helpers
    ├── datetime.py  — Datetime formatting
    ├── env.py       — Environment variables
    ├── random.py    — Randomness
    ├── base64.py    — Encoding
    ├── regex.py     — Regular expressions
    ├── db.py        — SQLite database
    ├── crypto.py    — Hashing, tokens, encryption
    ├── csv.py       — CSV read/write
    ├── xml.py       — XML parsing
    ├── gui.py       — Desktop GUI (Tkinter wrapper)
    ├── canvas.py    — 2D drawing & animation canvas (Tkinter)
    ├── vibe.py      — WebSocket client
    └── express.py   — Express-style HTTP router
```

---

## 🔬 Examples

| File | Description |
|---|---|
| `examples/math_and_else.vrb` | Arithmetic and if/else |
| `examples/full_example.vrb` | Functions, loops, user input |
| `examples/lists_and_loops.vrb` | Lists, add/remove, for-each |
| `examples/advanced.vrb` | Classes, async, fetch, file I/O |
| `examples/options.vrb` | Option values, unwrap, unwrap_or, and null-safety checks |
| `examples/pointers.vrb` | References, deref, pass-by-reference |
| `examples/file_io.vrb` | Save, load, append, delete files |
| `examples/use_http.vrb` | HTTP GET, POST, error handling |
| `examples/http_server.vrb` | Simple route-based HTTP server |
| `examples/use_express.vrb` | Express-style router with params |
| `examples/use_browser.vrb` | Web scraping with browser module |
| `examples/my_module.vrb` | Module/import example |
| `examples/table.vrb` | Multiplication table (user input) |
| `examples/pattern-star.vrb` | Star triangle with while loop |
| `examples/patterns/` | 10 ASCII pattern examples |
| `examples/webapp/server.vrb` | Full web app with REST API |
| `test_suite.vrb` | Comprehensive automated test suite |

---

## 🧑‍💻 Running the Examples

```bash
/- Basic scripts
python -m verba run examples/math_and_else.vrb
python -m verba run examples/advanced.vrb
python -m verba run examples/pointers.vrb

/- Server examples (blocks — use Ctrl+C to stop)
python -m verba run examples/http_server.vrb
python -m verba run examples/use_express.vrb
python -m verba run examples/webapp/server.vrb

/- Full test suite
python -m verba run test_suite.vrb
```

---

## 📦 Package Manager

```bash
/- Install a package from a URL
verba install https://raw.githubusercontent.com/user/repo/main/utils.vrb

/- Packages are saved to ./modules/
/- Use them with:
import from file called "utils.vrb" as utils.
```

---

## ✏️ Code Formatter

```bash
verba format yourfile.vrb
```

Enforces 4-space block indentation and consistent style.

---

## ⚠️ Syntax Rules

- Every statement ends with `.` (period)
- Block openers end with `:` (colon)
- Blocks close with `end.`
- Indentation is **4 spaces** per level (tabs count as 4 spaces)
- String interpolation uses `{variable}` inside double-quoted strings `"..."` only
- Single-quoted strings `'...'` are raw literals (no interpolation)
- Comments: `/-` or `#` for single-line, `/-- ... --/` for block
- Names are **single words** (no spaces); use underscores: `my_variable`
- All keywords are **case-insensitive** when parsed

---

## 📄 License

MIT — free for personal and commercial use.
