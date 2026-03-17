note test imports
import from file called quote examples\my_module.vb.

say quote module loaded!.

let res be the result of running multiply things with 4, 5.
say quote The result is and res.

note test error handling
try to do the following.
    say quote Going to divide by zero now...
    let oops be 10 / 0.
on error saving to error message, do the following.
    say quote Caught an error!.
    say quote Reason: and error message.
end try.

note simple catch without error capture
try to do the following.
    let x be 1 / 0.
on error, do the following.
    say quote Caught another error silently!.
end try.
