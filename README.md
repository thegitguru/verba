# Verba — A Concise Structural Programming Language

Verba is a modern interpreter with clean, readable structural syntax.

---

## Key Constraints

- Every statement must end with a period `.` or colon `:`
- Blocks are detected by indentation (4 spaces or a tab)

---

## Installation

**Requirement:** All you need is the `verba.exe` binary.

To use Verba, ensure that the folder containing `verba.exe` is in your system path. This allows you to run Verba scripts from any directory.

## Run a Program

```bash
verba examples/full_example.vrb
```

**Check syntax only (parse-only):**
```bash
verba --check examples/test.vrb
```

**Print version:**
```bash
verba --version
```

## Start the REPL

```bash
verba --repl
```

Type `end.` on its own line to exit.

## Formatter

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

---

## Language Overview

### Comments

```vb
note this is ignored by the interpreter.
/- this is also a single-line comment.
x = 10. /- inline comment, x is still 10.
```

Multi-line block comments use `/--` to open and `--/` to close:

```vb
/--
This entire block is ignored.
Spans as many lines as you need.
--/
```

---

### Variables & Assignment

```vb
counter = 1.
name = "Alice".
counter += 1.
counter -= 2.
counter *= 3.
counter /= 2.
```

---

### Output

```vb
say "hello ", username.
say.
display item.
```

> `say` adds a newline; `display` does not.

---

### Input

```vb
ask the user "what is your name?" and save to username.
```

---

### Math Expressions

```vb
result = num * counter.
x = 10 + 2 * 3.
r = 10 % 3.
```

Operators: `+`, `-`, `*`, `/`, `%`, `**` (power), `//` (floor divide)

Unary minus is supported: `neg = -5.`

---

Use `join` or **string interpolation** to combine values into a single string:

```vb
name = "Alice".
age = 30.

/- Option 1: join expression
greeting = join "Hello, ", name, "!".

/- Option 2: Interpolation (cleaner)
greeting = "Hello, {name}! You are {age} years old.".

say greeting.
```

`join` works anywhere an expression is expected — assignments, `respond with`, function arguments. Interpolation works inside any double-quoted string. Use `{{` and `}}` to escape literal braces.

---

### Conditions

```vb
if age < 18:
    say "you are a minor.".
else:
    say "you are an adult.".
end.
```

**else if** chaining:

```vb
if score >= 90:
    say "A".
else if score >= 80:
    say "B".
else:
    say "C".
end.
```

Comparisons: `==`, `!=`, `>`, `<`, `>=`, `<=`, `is null`, `is not null`

Boolean operators: `and`, `or`, `not`

---

### Match

```vb
match day:
    when "Mon":
        say "Monday".
    end.
    when "Fri":
        say "Friday".
    end.
    else:
        say "another day".
    end.
end.
```

---

### Loops

**Repeat a fixed number of times:**
```vb
repeat 5 times:
    say "again".
end.
```

**Repeat with an index variable:**
```vb
repeat 5 times with i:
    say "step ", i.
end.
```

**While loop:**
```vb
while counter <= 3:
    say "counting ", counter.
    counter += 1.
end.
```

**For-each loop:**
```vb
for item in colors:
    say "color ", item.
end.
```

**For-each with index:**
```vb
for item at i in colors:
    say i, ": ", item.
end.

**Numeric range loop:**
```vb
for i from 1 to 10:
    say i.
end.

/- Optional step
for i from 10 to 0 step -2:
    say i.
end.
```
**Loop control:**
```vb
stop.   /- break out of the loop
skip.   /- continue to the next iteration
```

---

### Lists

```vb
colors = a list of red, green, blue.
add yellow to colors.
remove green from colors.
```

**1-based indexing:**
```vb
first_color = item 1 of colors.
```

**Check membership:**
```vb
if "red" in colors:
    say "found it.".
end.

if "yellow" not in colors:
    say "missing yellow.".
end.
```

**Sorting:**
```vb
sort colors.
sort colors descending.
```

**Slicing:**
```vb
first 3 of colors into top_three.
last 2 of colors into bottom_two.
```

**Length:**
```vb
n = length of colors.
```

---

### Functions

```vb
define greet_person needing name, age:
    say "hello ", name.
end.

run greet_person with username, user_age.
```

**Return a value:**
```vb
define add_two_numbers needing a, b:
    give a + b.
end.
```

**Capture result:**
```vb
total = the result of running add_two_numbers with 2, 3.
```

**Multi-return & Tuple Unpacking:**
```vb
define min_max:
    give 1, 100.
end.

low, high = the result of running min_max.
say low, " to ", high.
```

**Default parameter values:**
```vb
define greet needing name, greeting = "Hello":
    say greeting, ", ", name.
end.

run greet with "Alice".
run greet with "Bob", "Hi".
```

---

**Try / Catch / Finally**

```vb
try:
    run dangerous_function.
on error saving to error_message:
    say "An error occurred: ", error_message.
finally:
    say "cleanup always runs.".
end.
```

**Raising errors:**
```vb
if age < 0:
    raise "Age cannot be negative.".
end.
```

Silent catch (no error variable):

```vb
try:
    x = 1 / 0.
on error:
    say "caught silently.".
end.
```

---

### Assert

```vb
assert x > 0 saying "x must be positive".
```

---

### Imports & Namespaces

```vb
import from file called "my_module.vrb".
```

**Namespaced Imports (`as` keyword):**
You can alias an import to prevent global namespace collisions.
```vb
import from file called "my_module.vrb" as mm.

the result of running mm.multiply_things with 4, 5.
say mm.some_variable.
```

---

### Pointers

```vb
x = 10.
ptr = &x.
say deref ptr.        /- prints 10
deref ptr = 99.       /- x is now 99
say x.                /- prints 99

y = 5.
ptr = &y.
deref ptr = 0.
say y.                /- prints 0

ptr = null.
if ptr is null:
    say "no target.".
end.
```

---

## Advanced Capabilities

### 1. Object-Oriented Programming

```vb
class Animal:
    define speak:
        say "...".
    end.
end.

class Person extends Animal:
    /- Class-level property with default value
    location = "Earth".
    
    define init needing first_name:
        self.name = first_name.
    end.
    define speak:
        say self.name, " from ", self.location, " says hello.".
    end.
end.

p = new Person with "Alice".
run p.speak.
p.name = "Bob".
run p.speak.
```

---

### 2. File I/O

```vb
append "Server Starting..." to file called "output.log".

message = "hello".
save message to file called "out.txt".

load file called "out.txt" into loaded_message.
say loaded_message.

delete file called "out.txt".
```

---

### 3. Simple HTTP Fetch

```vb
fetch "http://example.com" into site_html.
say "Fetched! HTML: ", site_html.

free site_html.
```

---

### 4. Asynchronous Concurrency

```vb
async define background_work needing server_url:
    fetch server_url into html.
    say "background job running".
    give html.
end.

task = async run background_work with "https://example.com".
say "Doing something else on the main thread!".
await result = task.
say "Async finished! Result: ", result.
```

---

### 5. Built-in HTTP Server

Define routes with `on route`, respond with `respond with`, redirect with `redirect to`, then start with `serve on port`.

```vb
on route "/" with method "GET":
    respond with "<h1>Hello!</h1>" status 200 type "text/html".
end.

on route "/greet" with method "GET":
    name = request.query_name.
    if name is null:
        name = "stranger".
    end.
    html = join "<h1>Hello, ", name, "!</h1>".
    respond with html status 200 type "text/html".
end.

on route "/echo" with method "POST":
    respond with request.body status 200 type "text/plain".
end.

on route "/old" with method "GET":
    redirect to "/new" status 301.
end.

serve on port 5000.
```

**Request object** available inside every route handler:

| Property | Value |
|---|---|
| `request.method` | `"GET"`, `"POST"`, etc. |
| `request.path` | `/greet` |
| `request.body` | raw request body string |
| `request.query_<key>` | query string value, e.g. `request.query_name` |
| `request.form_<key>` | form-encoded POST value |

**`respond with`** accepts comma-separated parts (like `say`):

```vb
respond with "<b>", name, "</b>" status 200 type "text/html".
```

Stop the server with `Ctrl+C`.

---

## Standard Library Modules

These modules are available in every Verba program without any import — `http`, `browser`, `express`, `strings`, `math`, `json`, `os`, `time`, `env`, `random`, `base64`, `regex`, `datetime`, `db`, `crypto`, `csv`, `xml`, `gui`, and `verbix`.

---

### `http` — Axios-like HTTP Client

```vb
res = the result of running http.get with "https://api.example.com/data".
say "status: ", res.status.
say "body:   ", res.body.
```

**Response object properties:** `res.status`, `res.ok`, `res.body`, `res.data`

| Function | Description |
|---|---|
| `http.get with url` | GET request |
| `http.get with url, headers` | GET with custom headers (JSON string) |
| `http.post with url, body` | POST form-encoded body |
| `http.post with url, body, headers` | POST with custom headers |
| `http.post_json with url, json` | POST with `Content-Type: application/json` |
| `http.put with url, body` | PUT request |
| `http.delete with url` | DELETE request |
| `http.encode_form with json` | Encode a JSON object as `key=value&...` |
| `http.encode_url with base, json` | Append query params to a URL |

**Example — POST JSON:**

```vb
res = the result of running http.post_json with "https://httpbin.org/post", '{"hello":"world"}'.
say "status: ", res.status.
```

**Example — error handling:**

```vb
try:
    res = the result of running http.get with "https://httpbin.org/status/404".
    say "status: ", res.status.
    say "ok: ", res.ok.
on error saving to err:
    say "request failed: ", err.
end.
```

> Use single-quoted strings `'...'` when your JSON contains double quotes.

---

### `strings` — String Utilities

| Function | Description |
|---|---|
| `strings.length with s` | Length of string |
| `strings.upper with s` | Uppercase |
| `strings.lower with s` | Lowercase |
| `strings.trim with s` | Strip whitespace |
| `strings.contains with s, sub` | Returns `"true"` or `"false"` |
| `strings.starts_with with s, prefix` | Returns `"true"` or `"false"` |
| `strings.ends_with with s, suffix` | Returns `"true"` or `"false"` |
| `strings.replace with s, old, new` | Replace all occurrences |
| `strings.split with s, sep` | Split into a list |
| `strings.index_of with s, sub` | First index of substring (`-1` if not found) |
| `strings.slice with s, start, end` | Substring by index |
| `strings.to_number with s` | Parse string to number |
| `strings.repeat with s, times` | Repeat string N times |

```vb
up = the result of running strings.upper with "hello".
say up.   /- HELLO
```

---

### `math` — Math Functions

| Function | Description |
|---|---|
| `math.floor with n` | Floor |
| `math.ceil with n` | Ceiling |
| `math.round with n, digits` | Round to N decimal places |
| `math.abs with n` | Absolute value |
| `math.sqrt with n` | Square root |
| `math.power with base, exp` | Exponentiation |
| `math.log with n, base` | Logarithm (natural if base omitted) |
| `math.sin with n` | Sine |
| `math.cos with n` | Cosine |
| `math.tan with n` | Tangent |
| `math.random` | Random float 0–1 |
| `math.random_int with low, high` | Random integer in range |
| `math.min with a, b` | Minimum |
| `math.max with a, b` | Maximum |
| `math.pi` | π |

```vb
r = the result of running math.random_int with 1, 100.
say "random: ", r.
```

---

### `browser` — HTTP Browser Module

No dependencies required — uses Python's built-in `urllib` and `html.parser`.

```vb
title = the result of running browser.open with "https://example.com", "true".
say "title: ", title.

heading = the result of running browser.read with "h1".
say "h1: ", heading.

current_url = the result of running browser.url.
say "url: ", current_url.

run browser.close.
```

| Function | Description |
|---|---|
| `browser.open with url, headless` | Fetch a URL and load the page |
| `browser.goto with url` | Navigate to a new URL |
| `browser.read with selector` | Get inner text of a tag (e.g. `"h1"`, `"p"`) |
| `browser.read_html with selector` | Get inner HTML of a tag |
| `browser.wait with ms` | Wait for a number of milliseconds |
| `browser.wait_for with selector` | Check element exists in loaded page |
| `browser.title` | Get the current page title |
| `browser.url` | Get the current page URL |
| `browser.close` | Clear the loaded page |

---

### `express` — Express-like Router

Handlers are plain Verba `define` functions. Register them by name, then call `express.listen`.

```vb
define handle_home:
    respond with "<h1>Hello from Express!</h1>" status 200 type "text/html".
end.

define handle_user:
    id = request.param_id.
    body = join '{"id":"', id, '"}'.
    respond with body status 200 type "application/json".
end.

define handle_echo:
    out = the result of running express.json_build with "echo", request.body.
    respond with out status 200 type "application/json".
end.

define handle_404:
    respond with "Not Found" status 404 type "text/plain".
end.

run express.use with "public", "/static".
run express.get with "/", "handle_home".
run express.get with "/users/:id", "handle_user".
run express.post with "/echo", "handle_echo".
run express.get with "*", "handle_404".

run express.listen with "5000".
```

**Route parameter** `:name` is available as `request.param_name`.

| Function | Description |
|---|---|
| `express.get with path, handler` | Register a GET route |
| `express.post with path, handler` | Register a POST route |
| `express.put with path, handler` | Register a PUT route |
| `express.delete with path, handler` | Register a DELETE route |
| `express.use with dir, prefix` | Serve static files from `dir` at URL `prefix` |
| `express.listen with port` | Start the server (blocks) |
| `express.json_build with k, v, ...` | Build a JSON object from key/value pairs |
| `express.json_key with json, key` | Extract a key from a JSON string |
| `express.json_arr_len with json` | Length of a JSON array |
| `express.json_arr_item with json, i` | Item at index `i` of a JSON array |

---


---

### `json` — JSON Parser & Generator

| Function | Description |
|---|---|
| `json.parse with s` | Parse JSON string into a dict/list |
| `json.get with obj, key` | Get key from object or JSON string |
| `json.set with json, key, val` | Return new JSON with key set |
| `json.build with k1, v1, ...` | Build object from key-value pairs |
| `json.stringify with val` | Convert value to JSON string |
| `json.arr_len with json` | Length of a JSON array |
| `json.arr_item with json, i` | Item at index `i` of array |

---

### `os` — Filesystem Operations

| Function | Description |
|---|---|
| `os.exists with path` | Check if file/dir exists |
| `os.is_file with path` | Check if path is a file |
| `os.is_dir with path` | Check if path is a directory |
| `os.list with path` | List directory contents |
| `os.mkdir with path` | Create directory (recursive) |
| `os.remove with path` | Delete file or directory |
| `os.rename with src, dst` | Rename/move file or directory |
| `os.cwd` | Get current working directory |
| `os.size with path` | Get file size in bytes |

---

### `time` — Date & Time

| Function | Description |
|---|---|
| `time.now` | Current Unix timestamp |
| `time.format with ts, fmt` | Format timestamp (default: `now`, `Y-M-D H:M:S`) |
| `time.sleep with ms` | Pause execution in milliseconds |
| `time.since with ts` | Seconds elapsed since timestamp |
| `time.year`, `time.month`, ... | Current time components |

---

### `env` — Environment Variables

| Function | Description |
|---|---|
| `env.get with key, default` | Get an environment variable |
| `env.set with key, val` | Set an environment variable |
| `env.has with key` | Check if variable exists |
| `env.all` | List all environment variables |

---

## Examples

### 1. test.vrb — Basic Variables & Math

```vb
x = 2.
y = 5.
say "x + y = ", x + y, ", x - y = ", x - y.
```

**Output:**
```
x + y = 7, x - y = -3
```

---

### 2. math_and_else.vrb — Math, Input & Conditionals

```vb
ask the user "what is your name?" and save to username.
say "hello ", username.

score = 10.
score = score + 5 * 2.
quotient = score / 4.
difference = quotient - 1.

say "your score is ", score.
say "your quotient is ", quotient.
say "your difference is ", difference.

if difference > 3:
    say "difference is big".
else:
    say "difference is small".
end.
```

---

### 3. lists_and_loops.vrb — Lists, For & Repeat

```vb
colors = a list of red, green, blue.
add yellow to colors.
remove green from colors.

for item in colors:
    say "color ", item.
end.

repeat 2 times:
    say "again".
end.
```

---

### 4. full_example.vrb — Functions, Input & While Loop

```vb
define greet_person needing name, age:
    say "hello ", name.
    if age < 18:
        say "you are a minor.".
    else:
        say "you are an adult.".
    end.
end.

ask the user "what is your name?" and save to username.
ask the user "how old are you?" and save to user_age.

run greet_person with username, user_age.

counter = 1.
while counter <= 3:
    say "counting ", counter.
    counter += 1.
end.

say "goodbye".
```

---

### 5. table.vrb — Multiplication Table

```vb
ask the user "which number's table do you want?" and save to num.
ask the user "how many times?" and save to limit.

counter = 1.
while counter <= limit:
    result = num * counter.
    say num, " x ", counter, " = ", result.
    counter += 1.
end.
```

---

### 6. pattern-star.vrb — Star Triangle Pattern

```vb
asterisk = "*".

define print_triangle needing rows:
    row = 1.
    while row <= rows:
        stars = a list of x.
        remove x from stars.
        col = 1.
        while col <= row:
            add asterisk to stars.
            col += 1.
        end.
        for item in stars:
            display item.
        end.
        say.
        row += 1.
    end.
end.

ask the user "how many rows do you want?" and save to row_count.
run print_triangle with row_count.
```

---

### 7. my_module.vrb — Reusable Module

```vb
define multiply_things needing a, b:
    give a * b.
end.

say "module loaded !".
```

---

### 8. test_new_features.vrb — Imports & Error Handling

```vb
import from file called "examples/my_module.vrb".

res = the result of running multiply_things with 4, 5.
say "The result is ", res.

try:
    say "Going to divide by zero now...".
    oops = 10 / 0.
on error saving to error_message:
    say "Caught an error !".
    say "Reason : ", error_message.
end.

try:
    x = 1 / 0.
on error:
    say "Caught another error silently !".
end.
```

---

### 9. file_io.vrb — File I/O & Error Handling

```vb
message = "hello".

try:
    save message to file called "out.txt".
    say "File saved successfully.".

    load file called "out.txt" into loaded_message.
    say "Loaded content: ", loaded_message.
on error saving to error_msg:
    say "An error occurred during file operations: ", error_msg.
end.
```

---

### 10. advanced.vrb — OOP, Async, Fetch & Memory

```vb
class Person:
    define init needing first_name:
        self.name = first_name.
    end.
    define walk:
        say self.name, " is walking.".
    end.
end.

p = new Person with "Alice".
run p.walk.
p.name = "Bob".
run p.walk.

async define background_work:
    say "background job running".
    append "hello file!" to file called "bg.log".
    give "job done".
end.

task = async run background_work.
await result = task.
say "Task finished with: ", result.

load file called "bg.log" into val.
say "Read from file: ", val.
delete file called "bg.log".

fetch "http://google.com" into data.
say "Fetched google.com successfully.".

free data.
```

---

### 11. pointers.vrb — Native Pointer Semantics

```vb
x = 42.
ptr = &x.
say "ptr points to x, value: ", deref ptr.

deref ptr = 100.
say "after deref write, x = ", x.

y = 7.
ptr = &y.
say "ptr re-seated to y, value: ", deref ptr.

deref ptr = 99.
say "after deref write, y = ", y.

p = null.
if p is null:
    say "p is null.".
end.

p = &x.
if p is not null:
    say "p is not null, value: ", deref p.
end.

define double_it needing n:
    deref n = deref n * 2.
end.

val = 5.
vptr = &val.
run double_it with vptr.
say "after double_it, val = ", val.
```

---

### 12. http_server.vrb — Built-in HTTP Server

```vb
on route "/" with method "GET":
    respond with "<h1>Hello from Verba!</h1>" status 200 type "text/html".
end.

on route "/greet" with method "GET":
    name = request.query_name.
    if name is null:
        name = "stranger".
    end.
    html = join "<h1>Hello, ", name, "!</h1>".
    respond with html status 200 type "text/html".
end.

on route "/echo" with method "POST":
    respond with request.body status 200 type "text/plain".
end.

on route "/old-ping" with method "GET":
    redirect to "/ping" status 301.
end.

on route "/count" with method "GET":
    n = request.query_n.
    if n is null:
        n = 3.
    end.
    counter = 1.
    output = "".
    while counter <= n:
        output = join output, counter, " ".
        counter += 1.
    end.
    respond with output status 200 type "text/plain".
end.

serve on port 5000.
```

Run with:
```bash
verba examples/http_server.vrb
```

---

### 13. use_http.vrb — HTTP Client

```vb
res = the result of running http.get with "https://httpbin.org/get".
say "status: ", res.status.
say "body: ", res.body.

form = the result of running http.encode_form with '{"name":"Verba","lang":"vrb"}'.
res2 = the result of running http.post with "https://httpbin.org/post", form.
say "POST status: ", res2.status.

res3 = the result of running http.post_json with "https://httpbin.org/post", '{"hello":"world"}'.
say "POST JSON status: ", res3.status.

url = the result of running http.encode_url with "https://httpbin.org/get", '{"q":"verba","page":"1"}'.
res4 = the result of running http.get with url.
say "GET with params status: ", res4.status.
```

---

### 14. use_browser.vrb — Browser / HTTP Fetch

```vb
title = the result of running browser.open with "https://example.com", "true".
say "page title: ", title.

heading = the result of running browser.read with "h1".
say "h1 text: ", heading.

current_url = the result of running browser.url.
say "url: ", current_url.

run browser.close.
say "browser closed.".
```

Run with:
```bash
verba examples/use_browser.vrb
```

---

### 15. use_express.vrb — Express-like Router

```vb
run express.use with "examples/webapp", "/static".

define handle_home:
    respond with "<h1>Welcome!</h1>" status 200 type "text/html".
end.

define handle_user:
    id = request.param_id.
    body = join '{"id":"', id, '"}'.
    respond with body status 200 type "application/json".
end.

define handle_echo:
    out = the result of running express.json_build with "echo", request.body.
    respond with out status 200 type "application/json".
end.

define handle_404:
    respond with "Not Found" status 404 type "text/plain".
end.

run express.get with "/", "handle_home".
run express.get with "/users/:id", "handle_user".
run express.post with "/echo", "handle_echo".
run express.get with "*", "handle_404".

run express.listen with "5000".
```

---

### 16. webapp/server.vrb — Full Web App (pure Verba backend)

A complete web application written entirely in Verba — no Python glue code needed.

```bash
verba examples/webapp/server.vrb
```

Then open `http://localhost:5000`. Features a calculator and a persistent counter, all served from Verba route handlers.

---

### 17. mathkit.vrb — Verbix Package Example

A reusable math utilities package hosted in `verba_packages/` and installable via Verbix.

```bash
# Serve the package folder locally
python -m http.server 8900   # run from verba_packages/

# Install it
verbix install http://localhost:8900/mathkit.vrb
```

```vb
note mathkit.vrb — math utilities package

define add needing a, b:
    give a + b.
end.

define divide needing a, b:
    if b == 0:
        raise "Cannot divide by zero.".
    end.
    give a / b.
end.

define average needing numbers:
    total = 0.
    count = 0.
    for n in numbers:
        total += n.
        count += 1.
    end.
    give total / count.
end.
```

---

### 18. use_mathkit.vrb — Using a Verbix-installed Package

```vb
import from file called "modules/mathkit.vrb".

sum = the result of running add with 12, 4.
say "12 + 4 = ", sum.

scores = a list of 80, 95, 70, 88, 92.
avg = the result of running average with scores.
say "average = ", avg.

try:
    bad = the result of running divide with 10, 0.
on error saving to err:
    say "caught: ", err.
end.
```

Run with:
```bash
verba examples/use_mathkit.vrb
```

---

- Every root-level statement must end with `.` or `:`.
- Use single-quoted strings `'...'` when your value contains double quotes (e.g. JSON literals).
- When Verba cannot understand a line, it throws a plain-English error with a **"Did you mean?" suggestion** for similarly named variables or misspelled keywords.
- Stop any running server with `Ctrl+C`.

---

## 💎 Advanced Syntax & Expressiveness

Verba includes modern language features that make data transformation and control flow extremely clear.

### List & Map Comprehensions
A concise way to transform lists or dictionaries.

```vb
# List Comprehension
squares = n * n for n in numbers.
odds = x for x in nums if x % 2 != 0.

# Map Comprehension
names = k: v for k, v in pairs.
```

### Match with Destructuring
Enhance your `match` statements to unpack lists or objects directly.

```vb
# List destructuring
match point:
    when [x, y]: say "X: {x}, Y: {y}".
    when [x, y, z]: say "3D point!".
end.

# Map destructuring
match res:
    when {"status": "200", "body": b}:
        say "Success: ", b.
    when {"status": "404"}:
        say "Not found".
end.
```

### Named Parameters
Better readability for functions with many arguments.

```vb
run save_user with name = "Alice", age = 30, active = "true".
```

### Context Managers (with)
Ensure resources like files are closed automatically.

```vb
with file "data.txt" as f:
    content = f.read().
    say content.
end.
```


## 📚 Standard Library expansion

Verba now features an expanded set of built-in modules for everyday tasks.

### Help
Interactive self-documentation directly in the language.

```vb
help.           # General help
help random.    # See available functions in 'random' module
help help.      # Help on the 'help' command itself
```

### New Modules
- **random**: `number(min, max)`, `choice(list)`, `shuffle(list)`.
- **regex**: `match(pattern, text)`, `search(pattern, text)`, `replace(pattern, repl, text)`.
- **base64**: `encode(text)`, `decode(text)`.
- **datetime**: `now(format)`, `parse(text, layout)`, `format(iso_str, layout)`.


### Advanced Data & GUI
Modern application modules for persistence and user interaction.

- **db**: SQLite interface. `db.open("path.db")` returns a connection with `.query(sql, args)` and `.execute(sql, args)`.
- **crypto**: `crypto.hash(text)`, `crypto.generate_token(n)`, `crypto.encrypt(text, key)`.
- **csv**: `csv.read(path)`, `csv.write(path, data_list)`.
- **xml**: `xml.parse(xml_str)`, `xml.find(data, tag)`.
- **gui**: `gui.window(title)` returns a window with `.button(text, callback)`, `.label(text)`, and `.show()`.

### Concise Literals
Verba now supports bracket and brace syntax for data structures in any expression:
```vb
# Lists
names = ["Alice", "Bob", "Charlie"].

# Maps
config = {"theme": "dark", "port": 5000}.

# Nested
users = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}].
```

## 🚀 Advanced Concepts

### 1. Iterators & Generators (`yield`)
Functions can pause execution and return multiple items natively using the `yield` statement without keeping the entire sequence in memory. These can be naturally traversed via the `for ... in` loop.

```vb
define number_stream:
    yield 1.
    say "Processing...".
    yield 2.
    yield 3.
end.

gen = the result of running number_stream.
for number in gen:
    say "Got: ", number.
end.
```

### 2. Native Decorators (`@` syntax)
Verba supports built-in metaprogramming with native decorators. Place them directly above `define` or `async define` statements.

* `@log`: Automatically logs to output when the function is initiated, printing its passed arguments.
* `@time`: Built-in performance execution tracing. Tracks exactly how many milliseconds the execution took and logs the duration once complete.

```vb
@log
@time
define heavy_calculation:
    # ... logic
end.
```

### 3. Built-In Testing & Assertions
Write test suites natively without needing an external testing framework running over Verba! The runtime executes tests in an isolated scoped environment but tracks global test assertions.

```vb
test "math addition works":
    assert 1 + 1 == 2 saying "Basic math failed!".
    assert 10 / 2 != 3.
end.
```
Run `verba examples/test_units.vrb` and Verba displays automated `PASSED`/`FAILED` reporting.

### 4. Docstrings & Metadata (`note`)
A `note` placed as the absolute first line of a `define` or `class` is treated as a runtime docstring. You can access it via the `help` command or directly at Runtime introspections!

```vb
define calc_area:
    note "Calculates the geometric area.".
    give 10 * 10.
end.
```
Then, `help calc_area.` in REPL will extract and display your detailed notes.
