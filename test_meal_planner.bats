#!/usr/bin/env bats

cmd="./meal_planner.py"

@test "No arguments -> Error" {
    run "${cmd}"
    [ $status -eq 1 ]
}

@test "Ask for help with -h/--help" {
    run ${cmd} -h
    [ $status -eq 0 ]

    run ${cmd} --help
    [ $status -eq 0 ]

    [ "$(${cmd} -h)" = "$(${cmd} --help)" ]

    run ${cmd} -h
    [[ "${lines[0]}" = *"usage: meal_planner.py RECIPE_FILE [OPTIONS]"* ]]
}

@test "Bad filename" {
    run ${cmd} bad_file
    [ $status -eq 1 ]

    echo ${output}
    [[ "${output}" == *"Error parsing arguments: ['bad_file']"* ]]
    [[ "${output}" == *"Unknown file: bad_file."* ]]
}
