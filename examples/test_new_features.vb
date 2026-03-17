note test imports

import from file called "examples/my_module.vb".

say "module loaded !".

res = the result of running multiply things with 4, 5.
say "The result is ", res.

note test error handling
try to do the following:
    say "Going to divide by zero now...".
    oops = 10 / 0.
on error saving to error message, do the following:
    say "Caught an error !".
    say "Reason : ", error message.
end.

note simple catch without error capture
try to do the following:
    x = 1 / 0.
on error, do the following:
    say "Caught another error silently !".
end.
