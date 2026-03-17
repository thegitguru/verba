asterisk = "*".

define print triangle needing rows as follows.
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

ask the user "how many rows do you want?" and save to row count.

run print triangle with row count.