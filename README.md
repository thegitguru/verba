## Verba — A Natural English Programming Language

Verba is a modern interpreter designed to bridge the gap between plain English and structural programming. Verba has two identical paradigms: you can write programs that read like conversational English sentences, or drop instantly into highly concise, familiar structural syntax whenever you feel like it.

### Key constraints

In Verba source files, statements can only be ended with:
- period `.` (standard statement terminator)
- colon `:` (block starter / statement terminator)

Blocks are detected by indentation (4 spaces or a tab). 

### Install (optional)

From the repo root:

```bash
python -m pip install -e .
```

### Run a Verba program

```bash
python -m verba examples/full_example.vb
```

Or, if installed:

```bash
verba examples/full_example.vb
```

### Start the REPL

```bash
python -m verba --repl
```

Type `end.` on its own line to exit.

---

### Language overview

#### Notes / comments

```vb
note this is ignored by the interpreter.
```

#### Syntax Dualities
Verba was designed from the ground up to allow for perfectly interchangeable natural language grammar or structural, concise syntaxes on the fly. You can mix and match conversational English keywords with symbolic shorthand entirely seamlessly.

#### Variables & Assignments
*Verbose Style:*
```vb
let counter be the number 1.
let name be the word quote Alice.
increase counter by 1.
decrease counter by 2.
```

*Concise Style:*
```vb
counter = 1.
name = "Alice".
counter += 1.
counter -= 2.
```

#### Output
*Verbose Style:*
```vb
say hello and username.
display item.
```

*Concise Style:*
```vb
say "hello ", username.
say.
```

#### Input
*Verbose Style:*
```vb
ask the user quote what is your name and save to username.
```

*Concise Style:*
```vb
ask the user "what is your name?" and save to username.
```

#### Conditions
*Verbose Style:*
```vb
if age is less than 18, do the following.
    say you are a minor.
otherwise do the following.
    say you are an adult.
end if.
```

*Concise Style:*
```vb
if age < 18:
    say "you are a minor.".
else:
    say "you are an adult.".
end.
```

Comparisons supported:
- *Verbose:* `is`, `equals`, `is not`, `does not equal`, `is greater than`, `is less than`, `is at least`, `is at most`
- *Concise:* `==`, `!=`, `>`, `<`, `>=`, `<=`

Boolean operators supported: `and`, `or`, `not`.

#### Loops

Repeat a fixed number of times:
```vb
repeat 2 times, do the following.
    say again.
end repeat.
```

While loop:
*Verbose Style:*
```vb
keep doing the following while counter is at most 3.
    say counting and counter.
    increase counter by 1.
end keep.
```

*Concise Style:*
```vb
while counter <= 3:
    say "counting ", counter.
    counter += 1.
end.
```

For-each loop over a list:
*Verbose Style:*
```vb
for each item in colors, do the following.
    say color and item.
end for.
```

*Concise Style:*
```vb
for item in colors:
    say "color ", item.
end.
```

#### Lists

```vb
colors = a list of red, green, blue.
add yellow to colors.
remove green from colors.
```

1-based indexing (item 1 is the first item):
```vb
let first color be item 1 of colors.
```

#### Functions

Define and run:
*Verbose Style:*
```vb
define greet person needing name, age as follows.
    say "hello ", name.
end define.

run greet person with username, user age.
```

*Concise Style:*
```vb
define greet person needing name, age:
    say "hello ", name.
end.

run greet person with username, user age.
```

Return a value:
*Verbose Style:*
```vb
define add two numbers needing a, b as follows.
    give back a plus b.
end define.
```

*Concise Style:*
```vb
define add two numbers needing a, b:
    give a + b.
end.
```

Capture function result:
*Verbose & Concise:*
```vb
let total be the result of running add two numbers with 2, 3.
total = the result of running add two numbers with 2, 3.
```

#### Math expressions

```vb
result = num * counter.
x = 10 + 2 * 3.
r = 10 % 3.
```

Operators supported:
- *Verbose:* `plus`, `minus`, `times`, `divided by`, `remainder after dividing by`
- *Concise:* `+`, `-`, `*`, `/`

#### Try / Catch Error Handling

*Verbose Style:*
```vb
try to do the following.
    run dangerous_function.
on error saving to error_message, do the following.
    say "An error occurred: ", error_message.
end.
```

*Concise Style:*
```vb
try:
    run dangerous_function.
on error saving to error_message:
    say "An error occurred: ", error_message.
end.
```

#### Imports

```vb
import from file called "my_module.vb".
```

---

## Advanced Capabilities

Verba is not simply an educational syntax mapped around basic primitives. It natively connects to the Operating System to support fully featured, modern software practices natively written directly into the grammar.

### 1. Object-Oriented Programming (OOP)
Define structural Classes holding discrete properties, instantiate isolated memory Objects out of those classes, and call internal properties or native methods seamlessly via standard dot-notation!
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
Load direct textual streams from hard drives directly into variables, push textual append updates to live log paths over time, instantly save new files completely overwriting the target, and perform deletion/garbage collection of real files from disk dynamically.
```vb
append "Server Starting..." to file called "output.log".

message = "hello".
save message to file called "out.txt".

load file called "out.txt" into loaded message.
say loaded message.

delete file called "out.txt".
```

### 3. HyperText Networking
Perform native OS-level URL HTTP requests entirely embedded in plain-grammar variables.
```vb
fetch "http://example.com" into site_html.
say "Source Code fetched! HTML: ", site_html.
```

### 4. Memory Management
Drop extreme memory burdens or excessive OS stream variables entirely out of variable-state scope with direct variable memory wiping.
```vb
fetch "http://some-giant-API.com/huge-payload" into massive_variable.
free massive_variable.
```

### 5. Asynchronous Parallel Concurrency
Natively dispatch complex or long-running computations into parallel Operating System background threads, gracefully `await` the generated signals out of band, and never hold up your main-thread processes natively cleanly with conversational grammar!
```vb
async define background work needing server_url:
    fetch server_url into html.
    say "background job running".
    give html.
end.

task = async run background work with "https://example.com".
say "Doing something else on the main thread entirely!".
await result = task.
say "Async Web Request Finished! Result: ", result.
```

### Notes
- Every single root-level statement must end with a period `.` or colon `:`.
- When Verba cannot understand a line, it throws a plain-English error pointing directly at the line number context.
