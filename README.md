## Verba — A Natural English Programming Language

Verba is a tiny interpreter where programs read like natural English sentences.

### Key constraints

In Verba source files, the only allowed symbols are:

- comma `,` (separator)
- period `.` (statement terminator)

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

### Language overview (current)

#### Notes / comments

```vb
note this is ignored by the interpreter.
```

#### Names (variables and functions)

- Names are **case-insensitive** and can be **multi-word** (e.g. `user age`).
- Use commas to separate list items and function parameters/arguments.

#### Values and text

- **Numbers**: `1`, `2`, `3.5`
- **Booleans**: `true`, `false`
- **Text**:
  - single-token words like `hello` can be used as “word values” (often via `the word`)
  - multi-word text uses `quote ...` (e.g. `quote out.txt`)
  - in `say`/`display`, multi-word phrases without `quote` are treated as literal text

### Small features (with syntax + examples)

#### Variables

```vb
let counter be the number 1.
set counter to 5.
increase counter by 1.
decrease counter by 2.
```

See `examples/full_example.vb` and `examples/table.vb`.

#### Output

- `say` prints with a newline
- `display` prints without a newline (useful in loops)

```vb
say hello and username.
display item.
say.
```

See `examples/pattern-star.vb`.

#### Input

```vb
ask for name.
ask the user for age.
ask the user quote what is your name and save to username.
```

See `examples/full_example.vb` and `examples/table.vb`.

#### Conditions

```vb
if age is less than 18, do the following.
    say you are a minor.
otherwise do the following.
    say you are an adult.
end if.
```

Comparisons supported:
- `is`, `equals`
- `is not`, `does not equal`
- `is greater than`, `is more than`
- `is less than`, `is fewer than`
- `is at least`, `is at most`

Boolean operators supported: `and`, `or`, `not`.

See `examples/full_example.vb`.

#### Loops

Repeat a fixed number of times:

```vb
repeat 2 times, do the following.
    say again.
end repeat.
```

While loop:

```vb
keep doing the following while counter is at most 3.
    say counting and counter.
    increase counter by 1.
end keep.
```

For-each loop over a list:

```vb
for each item in colors, do the following.
    say color and item.
end for.
```

See `examples/lists_and_loops.vb`, `examples/full_example.vb`, and `examples/table.vb`.

#### Lists

```vb
let colors be a list of red, green, blue.
add yellow to colors.
remove green from colors.
```

1-based indexing (item 1 is the first item):

```vb
let first color be item 1 of colors.
```

See `examples/lists_and_loops.vb`.

#### Functions

Define and run:

```vb
define greet person needing name, age as follows.
    say hello and name.
end define.

run greet person with username, user age.
```

Return a value:

```vb
define add two numbers needing a, b as follows.
    give back a plus b.
end define.
```

Capture the result of a function call:

```vb
let total be the result of running add two numbers with 2, 3.
```

See `examples/full_example.vb`.

#### Math expressions

```vb
let result be num times counter.
let x be 10 plus 2 times 3.
let r be 10 remainder after dividing by 3.
```

Operators supported: `plus`, `minus`, `times`, `divided by`, `remainder after dividing by`.

See `examples/table.vb`.

#### File I/O

```vb
save message to file called quote out.txt.
load file called quote out.txt into loaded message.
say loaded message.
```

See `examples/file_io.vb`.

### Notes

- Every statement must end with a period.
- When Verba cannot understand a line, it throws a plain-English error pointing at the line number.
