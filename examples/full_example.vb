note this program asks for a name and age, then greets the user.

define greet person needing name, age as follows.
    say "hello ", name.
    if age < 18:
        say "you are a minor.".
    else:
        say "you are an adult.".
    end.
end.

ask the user "what is your name?" and save to username.
ask the user "how old are you?" and save to user age.

run greet person with username, user age.

counter = 1.
while counter <= 3:
    say "counting ", counter.
    counter += 1.
end.

say goodbye.
