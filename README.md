# Verba — A Concise Structural Programming Language

Verba is a modern interpreter with clean, readable structural syntax.

---

## Key Constraints

- Every statement must end with a period `.` or colon `:`
- Blocks are detected by indentation (4 spaces or a tab)

---

## Install

```bash
python -m pip install -e .
```

## Run a Program

```bash
python -m verba examples/full_example.vrb
```

## Start the REPL

```bash
python -m verba --repl
```

Type `end.` on its own line to exit.

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

Operators: `+`, `-`, `*`, `/`, `%`

Unary minus is supported: `neg = -5.`

---

### String Concatenation

Use `join` to combine values into a single string:

```vb
greeting = join "Hello, ", name, "!".
say greeting.
```

`join` works anywhere an expression is expected — assignments, `respond with`, function arguments.

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

1-based indexing:
```vb
first_color = item 1 of colors.
```

Length:
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

**Default parameter values:**
```vb
define greet needing name, greeting = "Hello":
    say greeting, ", ", name.
end.

run greet with "Alice".
run greet with "Bob", "Hi".
```

---

### Try / Catch

```vb
try:
    run dangerous_function.
on error saving to error_message:
    say "An error occurred: ", error_message.
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

### Imports

```vb
import from file called "my_module.vrb".
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

Five modules are available in every Verba program without any import — `http`, `browser`, `express`, `strings`, and `math`.

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

> `browser.click`, `browser.type`, `browser.screenshot`, and `browser.eval` require Playwright (`pip install playwright && python -m playwright install chromium`) and will raise an error if called without it.

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
python -m verba examples/http_server.vrb
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
python -m verba examples/use_browser.vrb
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
python -m verba examples/webapp/server.vrb
```

Then open `http://localhost:5000`. Features a calculator and a persistent counter, all served from Verba route handlers.

---

## Notes

- Every root-level statement must end with `.` or `:`.
- Use single-quoted strings `'...'` when your value contains double quotes (e.g. JSON literals).
- When Verba cannot understand a line, it throws a plain-English error pointing at the exact line and column.
- Stop any running server with `Ctrl+C`.
