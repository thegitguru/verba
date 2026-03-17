x = 10.
y = 5.

say "The math equation:".
say "x + y = ", x + y.
say "x - y = ", x - y.
say "x * y = ", x * y.
say "x / y = ", x / y.

x += 2.
say "Now x is ", x.

if x == 12:
    say "x works with concise if conditions.".
else:
    say "condition failed.".
end.

let fruits be a list of "apple", "banana", "cherry".
for item in fruits:
    say "fruit: ", item.
end.

while y < 8:
    say "y is ", y.
    y += 1.
end.

define add two needing a, b as follows.
    give a + b.
end.

let res = the result of running add two with 1, 2.
say "function result: ", res.
