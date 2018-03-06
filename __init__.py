from inout import parse_grammar, print_grammar
from algorithms import reduce_grammar, remove_nullable_vars, eliminate_left_recursion, left_factor, parse
from exceptions import BadInputException

while True:
    try:
        grammar = parse_grammar()
        print("The following grammar has been initially formed:")
        print_grammar(grammar)

        grammar = remove_nullable_vars(grammar)
        print("After removal of nullable variables:")
        print_grammar(grammar)

        grammar = reduce_grammar(grammar)
        print("After removal of non-generating and unreachable variables:")
        print_grammar(grammar)

        grammar = eliminate_left_recursion(grammar)
        print("After elimination of left recursion:")
        print_grammar(grammar)

        grammar = left_factor(grammar)
        print("After left factoring:")
        print_grammar(grammar)

        while True:
            string = input("Enter a string to check if it belongs to the language ('s' to stop): ")

            if string == 's':
                break
            else:
                print(parse(string, grammar))
        print('')

    except BadInputException as e:
        print(e)
        print('')

    yes = ('y', 'Y', 'н', 'Н')
    no = ('n', 'N', 'т', 'Т')
    again = ''
    print("You can now change the input file and run the program again")

    while len(again) < 1 or again[0] not in yes + no:
        again = input("Do you want to run the program again (y/n)? ")

    if again[0] not in yes:
        break

    print('')
