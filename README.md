# Verba — A Natural English Programming Language

Verba is a modern interpreter designed to bridge the gap between plain English and structural programming. Verba has two identical paradigms: you can write programs that read like conversational English sentences, or drop instantly into highly concise, familiar structural syntax whenever you feel like it.

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

### Syntax Dualities

Verba allows perfectly interchangeable natural language or concise structural syntax. You can mix and match freely.

---

### Variables & Assignment

*Verbose:*
```vb
let counter be the number 1.
let name be the word quote Alice.
increase counter by 1.
decrease counter by 2.
```

*Concise:*
```vb
counter = 1.
name = "Alice".
counter += 1.
counter -= 2.
```

---

### Output

*Verbose:*
```vb
say hello and username.
display item.
```

*Concise:*
```vb
say "hello ", username.
say.
```

> Spacing is controlled entirely by your string literals. `say "hello ", name.` prints `hello aryan`.

---

### Input

*Verbose:*
```vb
ask the user quote what is your name and save to username.
```

*Concise:*
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

Operators:
- *Verbose:* `plus`, `minus`, `times`, `divided by`, `remainder after dividing by`
- *Concise:* `+`, `-`, `*`, `/`, `%`

---

### Conditions

*Verbose:*
```vb
if age is less than 18, do the following.
    say you are a minor.
otherwise do the following.
    say you are an adult.
end if.
```

*Concise:*
```vb
if age < 18:
    say "you are a minor.".
else:
    say "you are an adult.".
end.
```

Comparisons:
- *Verbose:* `is`, `equals`, `is not`, `does not equal`, `is greater than`, `is less than`, `is at least`, `is at most`
- *Concise:* `==`, `!=`, `>`, `<`, `>=`, `<=`

Boolean operators: `and`, `or`, `not`

---

### Loops

**Repeat a fixed number of times:**
```vb
repeat 2 times, do the following.
    say again.
end repeat.
```

**While loop:**

*Verbose:*
```vb
keep doing the following while counter is at most 3.
    say "counting ", counter.
    increase counter by 1.
end keep.
```

*Concise:*
```vb
while counter <= 3:
    say "counting ", counter.
    counter += 1.
end.
```

**For-each loop:**

*Verbose:*
```vb
for each item in colors, do the following.
    say "color ", item.
end for.
```

*Concise:*
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

*Verbose:*
```vb
define greet_person needing name, age as follows.
    say "hello ", name.
end define.

run greet_person with username, user_age.
```

*Concise:*
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

*Verbose:*
```vb
try to do the following.
    run dangerous_function.
on error saving to error_message, do the following.
    say "An error occurred: ", error_message.
end.
```

*Concise:*
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

Verba has first-class pointer semantics. A pointer holds a reference to a variable's memory cell — reading or writing through it directly affects the original variable.

**Take a reference:**

*Verbose:*
```vb
ptr = ref x.
```

*Concise:*
```vb
ptr = &x.
```

**Read through a pointer (dereference):**

*Verbose:*
```vb
val = value at ptr.
```

*Concise:*
```vb
val = deref ptr.
```

**Write through a pointer:**

*Verbose:*
```vb
set value at ptr to 42.
```

*Concise:*
```vb
deref ptr = 42.
```

**Re-seat a pointer at a different variable:**
```vb
point ptr to y.
```

**Null pointer:**
```vb
ptr = null.
```

**Null checks:**
```vb
if ptr is null:
    say "nothing here.".
end.

if ptr is not null:
    say "value: ", deref ptr.
end.
```

**Pass a pointer to a function to mutate the original:**
```vb
define double_it needing n as follows.
    deref n = deref n * 2.
end.

val = 5.
run double_it with &val.
say val.
```

---

## Examples

### 1. test.vrb — Basic Variables & Math

A minimal program demonstrating typed variable declarations and arithmetic expressions.

```vb
let x be the number 2.
let y be the number 5.
say "x + y = ", x + y, ", x - y = ", x - y.
```

**Output:**
```
x + y = 7, x - y = -3
```

---

### 2. math_and_else.vrb — Math, Input & Conditionals

Demonstrates user input, verbose-style math operations, `set`, and an `if/else` block.

```vb
ask the user quote what is your name and save to username.
say "hello " and username.

let score be the number 10.
set score to score + 5 * 2.
let quotient be score / 4.
let difference be quotient - 1.

say "your score is ", score.
say "your quotient is ", quotient.
say "your difference is ", difference.

if difference is greater than 3, do the following.
    say "difference is big".
else do the following.
    say "difference is small".
end if.
```

**Output:**
```
what is your name aryan
hello aryan
your score is 20
your quotient is 5
your difference is 4
difference is big
```

---

### 3. lists_and_loops.vrb — Lists, For & Repeat

Demonstrates list creation, mutation, for-each iteration, and a fixed repeat loop.

```vb
colors = a list of red, green, blue.
add yellow to colors.
remove green from colors.

for item in colors:
    say "color ", item.
end.

repeat 2 times, do the following.
    say again.
end repeat.
```

**Output:**
```
color red
color blue
color yellow
again
again
```

---

### 4. full_example.vrb — Functions, Input & While Loop

A complete program combining function definitions, user input, conditionals, and a while loop.

```vb
note this program asks for a name and age, then greets the user.

define greet_person needing name, age as follows.
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

say goodbye.
```

**Output:**
```
what is your name? aryan
how old are you? 21
hello aryan
you are an adult.
counting 1
counting 2
counting 3
goodbye
```

---

### 5. table.vrb — Multiplication Table

Takes two inputs and prints a multiplication table using a while loop.

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

**Output:**
```
which number's table do you want? 5
how many times? 12
5 x 1 = 5
5 x 2 = 10
...
5 x 12 = 60
```

---

### 6. pattern-star.vrb — Star Triangle Pattern

Builds a right-angled star triangle using nested while loops, lists, and a for-each loop.

```vb
asterisk = "*".

define print_triangle needing rows as follows.
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

**Output (5 rows):**
```
*
**
***
****
*****
```

---

### 7. my_module.vrb — Reusable Module

A standalone module file that defines a reusable function and can be imported by other programs.

```vb
define multiply_things needing a, b:
    give a * b.
end.

say "module loaded !".
```

---

### 8. test_new_features.vrb — Imports & Error Handling

Demonstrates importing an external module, capturing its return value, and try/catch error handling.

```vb
note test imports

import from file called "examples/my_module.vrb".

say "module loaded !".

res = the result of running multiply_things with 4, 5.
say "The result is ", res.

note test error handling
try to do the following:
    say "Going to divide by zero now...".
    oops = 10 / 0.
on error saving to error_message, do the following:
    say "Caught an error !".
    say "Reason : ", error_message.
end.

note simple catch without error capture
try to do the following:
    x = 1 / 0.
on error, do the following:
    say "Caught another error silently !".
end.
```

**Output:**
```
module loaded !
module loaded !
The result is 20
Going to divide by zero now...
Caught an error !
Reason : Error on line 13:
  I cannot divide by zero.
Caught another error silently !
```

---

### 9. file_io.vrb — File I/O & Error Handling

Saves a variable to disk, loads it back, and wraps the whole operation in a try/catch block.

```vb
note demonstrate saving and loading text with error handling.

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

**Output:**
```
File saved successfully.
Loaded content: hello
```

---

### 10. advanced.vrb — OOP, Async, Fetch & Memory

The most complete example. Covers classes, object instantiation, async functions, file append, HTTP fetch, and memory freeing.

```vb
class Person:
    define init needing first_name as follows:
        self.name = first_name.
    end.
    define walk as follows:
        say self.name, " is walking.".
    end.
end.

p = new Person with "Alice".
run p.walk.
p.name = "Bob".
run p.walk.

note Async
async define background_work as follows:
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

note Fetch url
fetch "http://google.com" into data.
say "Fetched google.com successfully.".

note Free memory
free data.
```

**Output:**
```
Alice is walking.
Bob is walking.
background job running
Task finished with: job done
Read from file: hello file!
Fetched google.com successfully.
```

---

### 11. pointers.vrb — Native Pointer Semantics

Demonstrates first-class pointer operations: taking references, reading and writing through pointers, null checks, re-seating, and passing pointers to functions.

```vb
/- 1. take a reference with ref / &
x = 42.
ptr = ref x.
say "ptr points to x, value: ", deref ptr.

/- 2. write through a pointer — mutates x directly
deref ptr = 100.
say "after deref write, x = ", x.

/- 3. verbose syntax: point / value at / set value at
y = 7.
point ptr to y.
say "ptr re-seated to y, value at ptr: ", value at ptr.

set value at ptr to 99.
say "after set value at ptr, y = ", y.

/- 4. null pointer and null checks
p = null.
if p is null:
    say "p is null.".
end.

p = ref x.
if p is not null:
    say "p is not null, value: ", deref p.
end.

/- 5. passing a pointer to a function — mutates the original variable
define double_it needing n as follows.
    deref n = deref n * 2.
end.

val = 5.
vptr = ref val.
run double_it with vptr.
say "after double_it, val = ", val.

/- 6. concise & syntax
z = 10.
q = &z.
say "q via &z, value: ", deref q.
deref q = 20.
say "after deref q = 20, z = ", z.
```

**Output:**
```
ptr points to x, value: 42
after deref write, x = 100
ptr re-seated to y, value at ptr: 7
after set value at ptr, y = 99
p is null.
p is not null, value: 100
after double_it, val = 10
q via &z, value: 10
after deref q = 20, z = 20
```

---

## Advanced Capabilities

### 1. Object-Oriented Programming

Define classes with `init` and methods, instantiate with `new`, access properties via dot-notation.

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
ptr = ref x.          /- or: ptr = &x.
say deref ptr.        /- prints 10
deref ptr = 99.       /- x is now 99
say x.                /- prints 99

/- re-seat at a different variable
y = 5.
point ptr to y.
set value at ptr to 0.
say y.                /- prints 0

/- null safety
ptr = null.
if ptr is null:
    say "no target.".
end.
```

---

## Notes

- Every root-level statement must end with `.` or `:`.
- When Verba cannot understand a line, it throws a plain-English error pointing at the exact line and column.
