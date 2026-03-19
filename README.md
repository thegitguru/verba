# 🗣️ Verba — A Natural English Programming Language

**Verba** is an interpreted, English-like programming language designed to be readable by anyone, even without a programming background. Code reads like instructions you'd give a person. Every statement ends with a period `.` (or a colon `:` for blocks).

```verba
note A simple greeting program.

ask the user "What is your name?" and save to name.
say "Hello, ", name, "!".

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
| `verba check <file.vrb>` | Parse only — syntax check without running |
| `verba repl` | Start an interactive REPL |
| `verba format <file.vrb>` | Auto-format script with 4-space indentation |
| `verba install <url>` | Download & install a `.vrb` package into `modules/` |

---

## 📖 Language Reference

### Comments

```verba
/- This is a single-line comment.

/--
  This is a block comment.
  It can span multiple lines.
--/
```

### Variables & Assignment

```verba
name = "Alice".
age = 30.
is_admin = true.
score = 10 + 5 * 2.     /- supports +, -, *, /, %, **
quotient = 10 / 3.
modulo = 10 % 3.
power = 2 ** 8.
```

### String Interpolation

Double-quoted strings support `{variable}` interpolation. Single-quoted strings are raw literals.

```verba
user = "Alice".
greeting = "Hello, {user}!".     /- → "Hello, Alice!"
raw = 'No {interpolation} here'.
joined = join "Hello, ", user, "!".   /- explicit concatenation
```

### Output

```verba
say "Hello, world!".                   /- prints with newline
display "no newline ".                 /- prints without newline
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

### Conditions

```verba
if score > 90:
    say "A grade".
else if score > 70:
    say "B grade".
else:
    say "C grade".
end.
```

**Comparison operators:** `==`, `!=`, `<`, `>`, `<=`, `>=`, `is null`, `is not null`

**Logical operators:** `and`, `or`, `not`

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

/- for each with index
for item, idx in colors:
    say idx, ": ", item.
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

/- list literal
squares = [1, 4, 9, 16].

/- list comprehension
evens = x for x in nums if x > 2.
doubled = x * 2 for x in nums.
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

/- map pattern destructuring
match user:
    when {"role": "admin"}:
        say "Admin access".
    else:
        say "Regular user".
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
| `@memoize` | Caches results by arguments (avoids re-running) |

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
```

Modules are placed in the `modules/` folder and loaded by name.

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
run express.get with "/users/:id", "handle_user".
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

test "strings":
    s = "Hello, {name}!".
    assert s != "".
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
| `strings.index_of` with `s, sub` | First index of substring |
| `strings.slice` with `s, start, end` | Substring |
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
| `math.log` with `n, base` | Logarithm |
| `math.sin / cos / tan` with `n` | Trig functions |
| `math.random` | Random float 0..1 |
| `math.random_int` with `low, high` | Random integer |
| `math.min / max` with `a, b` | Min/Max |
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
| `crypto.generate_token` with `n` | Secure random hex token |
| `crypto.encrypt` with `text, key` | XOR + Base64 encryption |
| `crypto.decrypt` with `text, key` | Decrypt XOR + Base64 |

```verba
hash = the result of running crypto.hash with "my secret".
token = the result of running crypto.generate_token with 32.
```

### `json` — JSON Parsing & Building
| Function | Description |
|---|---|
| `json.parse` with `s` | Parse JSON string → dict/list |
| `json.get` with `obj, key` | Get key from object or JSON string |
| `json.set` with `json, key, value` | Return updated JSON string |
| `json.build` with `k1, v1, ...` | Build JSON from key-value pairs |
| `json.stringify` with `value` | Wrap value as JSON string |
| `json.has` with `json, key` | Check if key exists |
| `json.keys` with `json` | List all keys |
| `json.arr_len` with `json` | Length of JSON array |
| `json.arr_item` with `json, index` | Get item at index |

### `csv` — CSV Files
```verba
rows = the result of running csv.read with "data.csv".
for row in rows:
    say row.name.
end.

run csv.write with "out.csv", rows.
```

### `xml` — XML Parsing
```verba
parsed = the result of running xml.parse with "<root><item>hello</item></root>".
say parsed.tag.
found = the result of running xml.find with parsed, "item".
say found.text.
```

### `http` — HTTP Client
*(See HTTP Client section above)*

### `browser` — Web Scraping (stdlib only, no Playwright)
| Function | Description |
|---|---|
| `browser.open` with `url` | Fetch URL, store page |
| `browser.read` with `selector` | Read text from CSS tag (e.g. `"h1"`) |
| `browser.title` | Get page title |
| `browser.url` | Get current URL |
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
| `time.now` | Unix timestamp |
| `time.sleep` with `ms` | Sleep for milliseconds |
| `time.format` with `timestamp, fmt` | Format timestamp |
| `time.year / month / day` | Current date parts |
| `time.hour / minute / second` | Current time parts |
| `time.since` with `timestamp` | Elapsed seconds |

### `datetime` — Datetime Objects
| Function | Description |
|---|---|
| `datetime.now` with `format` | Current datetime, optional format string |
| `datetime.parse` with `text, layout` | Parse datetime string |
| `datetime.format` with `iso_str, layout` | Format ISO datetime |

### `random` — Randomness
| Function | Description |
|---|---|
| `random.number` with `min, max` | Random integer |
| `random.choice` with `list` | Random element from list |
| `random.shuffle` with `list` | Shuffled list |

### `regex` — Regular Expressions
| Function | Description |
|---|---|
| `regex.match` with `pattern, text` | True if pattern matches start |
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
| `env.get` with `key, default` | Read env var |
| `env.set` with `key, value` | Set env var |
| `env.has` with `key` | Check if set |
| `env.all` | List all as `key=value` strings |

### `gui` — Desktop UI (Tkinter)
```verba
win = the result of running gui.window with "My App".
run win.label with "Hello, Verba!".
run win.button with "Click me", "on_click".
run win.show.
```

---

## 🗂️ Project Structure

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

/- Run all examples automatically
python run_examples_test.py
```

---

# 🗣️ Verba — A Natural English Programming Language

**Verba** is an interpreted, English-like programming language designed to be readable by anyone, even without a programming background. Code reads like instructions you'd give a person. Every statement ends with a period `.` (or a colon `:` for blocks).

```verba
note A simple greeting program.

ask the user "What is your name?" and save to name.
say "Hello, ", name, "!".

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
| `verba check <file.vrb>` | Parse only — syntax check without running |
| `verba repl` | Start an interactive REPL |
| `verba format <file.vrb>` | Auto-format script with 4-space indentation |
| `verba install <url>` | Download & install a `.vrb` package into `modules/` |

---

## 📖 Language Reference

### Comments

```verba
/- This is a single-line comment.

/--
  This is a block comment.
  It can span multiple lines.
--/
```

### Variables & Assignment

```verba
name = "Alice".
age = 30.
is_admin = true.
score = 10 + 5 * 2.     /- supports +, -, *, /, %, **
quotient = 10 / 3.
modulo = 10 % 3.
power = 2 ** 8.
```

### String Interpolation

Double-quoted strings support `{variable}` interpolation. Single-quoted strings are raw literals.

```verba
user = "Alice".
greeting = "Hello, {user}!".     /- → "Hello, Alice!"
raw = 'No {interpolation} here'.
joined = join "Hello, ", user, "!".   /- explicit concatenation
```

### Output

```verba
say "Hello, world!".                   /- prints with newline
display "no newline ".                 /- prints without newline
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

### Conditions

```verba
if score > 90:
    say "A grade".
else if score > 70:
    say "B grade".
else:
    say "C grade".
end.
```

**Comparison operators:** `==`, `!=`, `<`, `>`, `<=`, `>=`, `is null`, `is not null`

**Logical operators:** `and`, `or`, `not`

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

/- for each with index
for item, idx in colors:
    say idx, ": ", item.
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

/- list literal
squares = [1, 4, 9, 16].

/- list comprehension
evens = x for x in nums if x > 2.
doubled = x * 2 for x in nums.
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

/- map pattern destructuring
match user:
    when {"role": "admin"}:
        say "Admin access".
    else:
        say "Regular user".
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
| `@memoize` | Caches results by arguments (avoids re-running) |

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
```

Modules are placed in the `modules/` folder and loaded by name.

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
run express.get with "/users/:id", "handle_user".
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

test "strings":
    s = "Hello, {name}!".
    assert s != "".
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
| `strings.index_of` with `s, sub` | First index of substring |
| `strings.slice` with `s, start, end` | Substring |
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
| `math.log` with `n, base` | Logarithm |
| `math.sin / cos / tan` with `n` | Trig functions |
| `math.random` | Random float 0..1 |
| `math.random_int` with `low, high` | Random integer |
| `math.min / max` with `a, b` | Min/Max |
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
| `crypto.generate_token` with `n` | Secure random hex token |
| `crypto.encrypt` with `text, key` | XOR + Base64 encryption |
| `crypto.decrypt` with `text, key` | Decrypt XOR + Base64 |

```verba
hash = the result of running crypto.hash with "my secret".
token = the result of running crypto.generate_token with 32.
```

### `json` — JSON Parsing & Building
| Function | Description |
|---|---|
| `json.parse` with `s` | Parse JSON string → dict/list |
| `json.get` with `obj, key` | Get key from object or JSON string |
| `json.set` with `json, key, value` | Return updated JSON string |
| `json.build` with `k1, v1, ...` | Build JSON from key-value pairs |
| `json.stringify` with `value` | Wrap value as JSON string |
| `json.has` with `json, key` | Check if key exists |
| `json.keys` with `json` | List all keys |
| `json.arr_len` with `json` | Length of JSON array |
| `json.arr_item` with `json, index` | Get item at index |

### `csv` — CSV Files
```verba
rows = the result of running csv.read with "data.csv".
for row in rows:
    say row.name.
end.

run csv.write with "out.csv", rows.
```

### `xml` — XML Parsing
```verba
parsed = the result of running xml.parse with "<root><item>hello</item></root>".
say parsed.tag.
found = the result of running xml.find with parsed, "item".
say found.text.
```

### `http` — HTTP Client
*(See HTTP Client section above)*

### `browser` — Web Scraping (stdlib only, no Playwright)
| Function | Description |
|---|---|
| `browser.open` with `url` | Fetch URL, store page |
| `browser.read` with `selector` | Read text from CSS tag (e.g. `"h1"`) |
| `browser.title` | Get page title |
| `browser.url` | Get current URL |
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
| `time.now` | Unix timestamp |
| `time.sleep` with `ms` | Sleep for milliseconds |
| `time.format` with `timestamp, fmt` | Format timestamp |
| `time.year / month / day` | Current date parts |
| `time.hour / minute / second` | Current time parts |
| `time.since` with `timestamp` | Elapsed seconds |

### `datetime` — Datetime Objects
| Function | Description |
|---|---|
| `datetime.now` with `format` | Current datetime, optional format string |
| `datetime.parse` with `text, layout` | Parse datetime string |
| `datetime.format` with `iso_str, layout` | Format ISO datetime |

### `random` — Randomness
| Function | Description |
|---|---|
| `random.number` with `min, max` | Random integer |
| `random.choice` with `list` | Random element from list |
| `random.shuffle` with `list` | Shuffled list |

### `regex` — Regular Expressions
| Function | Description |
|---|---|
| `regex.match` with `pattern, text` | True if pattern matches start |
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
| `env.get` with `key, default` | Read env var |
| `env.set` with `key, value` | Set env var |
| `env.has` with `key` | Check if set |
| `env.all` | List all as `key=value` strings |

### `gui` — Desktop UI (Tkinter)
```verba
win = the result of running gui.window with "My App".
run win.label with "Hello, Verba!".
run win.button with "Click me", "on_click".
run win.show.
```

---

## 🗂️ Project Structure

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

/- Run all examples automatically
python run_examples_test.py
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
- Indentation is **4 spaces** per level (tabs = 4 spaces)
- String interpolation uses `{variable}` inside double-quoted strings `"..."` only
- Single-quoted strings `'...'` are raw literals (no interpolation)
- Comments: `/-` for single-line, `/-- ... --/` for block

---

**Format a script:**
```bash
verba format examples/test.vrb
```
Enforces standard style and 4-space indentation across your code.

---

## Verbix — Package Manager

Verbix is the official package manager for Verba. It runs **standalone** (no `verba` prefix needed) and manages `.vrb` packages in the local `modules/` folder.

### Running Verbix

**Standalone command** (after adding to PATH):
```bash
verbix install https://raw.githubusercontent.com/.../my_module.vrb
```

**Via Python module:**
```bash
python -m verbix install https://raw.githubusercontent.com/.../my_module.vrb
```

**Via verba subcommand:**
```bash
verba verbix install https://raw.githubusercontent.com/.../my_module.vrb
```

### Commands

| Command | Description |
|---|---|
| `verbix install <url>` | Download and install a `.vrb` package from a URL |
| `verbix uninstall <name>` | Remove an installed package |
| `verbix packages` | List all installed packages |
| `verbix info <name>` | Show details about an installed package |
| `verbix --version` | Print Verbix version |

### Example

```bash
# 1. Install a package from a URL
verbix install http://localhost:8900/mathkit.vrb

# 2. List installed packages
verbix packages

# 3. Show package info
verbix info mathkit

# 4. Uninstall a package
verbix uninstall mathkit
```

Installed packages land in `modules/` and are tracked in `modules/.registry.json`. Use them in any script:

```vb
import from file called "modules/mathkit.vrb".

result = the result of running add with 10, 5.
say "10 + 5 = ", result.
```

### Using Verbix inside a Verba script

Verbix is also available as a built-in module (`verbix`) inside every Verba program:

```vb
/- Install a package at runtime
msg = the result of running verbix.install with "http://localhost:8900/mathkit.vrb".
say msg.

/- Check if a package is installed
ok = the result of running verbix.installed with "mathkit".
say "mathkit installed: ", ok.

/- List all packages
list = the result of running verbix.list.
say list.

/- Get info about a package
info = the result of running verbix.info with "mathkit".
say info.

/- Uninstall a package
result = the result of running verbix.uninstall with "mathkit".
say result.
```

### Building verbix.exe

To build a standalone `verbix.exe` binary:

```bash
pyinstaller verbix.spec
```

The binary will be at `dist/verbix.exe`. Add it to your PATH to use `verbix` from anywhere.


## ⚠️ Syntax Rules

- Every statement ends with `.` (period)
- Block openers end with `:` (colon)
- Blocks close with `end.`
- Indentation is **4 spaces** per level (tabs = 4 spaces)
- String interpolation uses `{variable}` inside double-quoted strings `"..."` only
- Single-quoted strings `'...'` are raw literals (no interpolation)
- Comments: `/-` for single-line, `/-- ... --/` for block

---

## 📄 License

MIT — free for personal and commercial use.