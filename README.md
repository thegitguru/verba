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
```

---

### Output

```vb
say "hello ", username.
say.
display item.
```

> Spacing is controlled entirely by your string literals.

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

---

### Conditions

```vb
if age < 18:
    say "you are a minor.".
else:
    say "you are an adult.".
end.
```

Comparisons: `==`, `!=`, `>`, `<`, `>=`, `<=`, `is null`, `is not null`

Boolean operators: `and`, `or`, `not`

---

### Loops

**Repeat a fixed number of times:**
```vb
repeat 2 times:
    say "again".
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

---

### Try / Catch

```vb
try:
    run dangerous_function.
on error saving to error_message:
    say "An error occurred: ", error_message.
end.
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

/- re-seat at a different variable
y = 5.
ptr = &y.
deref ptr = 0.
say y.                /- prints 0

/- null safety
ptr = null.
if ptr is null:
    say "no target.".
end.
```

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

z = 10.
q = &z.
say "q via &z, value: ", deref q.
deref q = 20.
say "after deref q = 20, z = ", z.
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

### 2. File I/O & System Streams

```vb
append "Server Starting..." to file called "output.log".

message = "hello".
save message to file called "out.txt".

load file called "out.txt" into loaded_message.
say loaded_message.

delete file called "out.txt".
```

### 3. HTTP Networking

```vb
fetch "http://example.com" into site_html.
say "Fetched! HTML: ", site_html.
```

### 4. Memory Management

```vb
fetch "http://some-giant-API.com/huge-payload" into massive_variable.
free massive_variable.
```

### 5. Asynchronous Concurrency

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

### 6. Pointers

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

## Notes

- Every root-level statement must end with `.` or `:`.
- When Verba cannot understand a line, it throws a plain-English error pointing at the exact line and column.
