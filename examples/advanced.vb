class Person:
    define init needing first_name as follows:
        self.name = first_name.
    end.
    define walk as follows:
        say self.name, "is walking.".
    end.
end.

p = new Person with "Alice".
run p.walk.
p.name = "Bob".
run p.walk.

note Async
async define background work as follows:
    say "background job running".
    append "hello file!" to file called "bg.log".
    give "job done".
end.

task = async run background work.
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
