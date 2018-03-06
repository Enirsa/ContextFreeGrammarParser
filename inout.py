from collections import OrderedDict
from exceptions import BadInputException


input_file = 'input.txt'


def parse_grammar():
    grammar = OrderedDict()
    rules = __read_input_file()
    bad_format = BadInputException("The input file isn't formatted according to the requirements — "
                                   "double-check it for typos or take a look at the README file")
    for rule_str in rules:
        if rule_str[0] != '"' or rule_str[len(rule_str) - 1] != '"':
            raise bad_format

        rule = rule_str[1:len(rule_str) - 1].split('" -> "')

        if len(rule) != 2:
            raise bad_format

        variable = rule[0]
        __validate_variable(variable)
        replacements = __parse_replacements(rule[1])

        if variable not in grammar:
            grammar[variable] = replacements
        else:
            grammar[variable] = grammar[variable] | replacements

    return grammar


def print_grammar(grammar):
    if len(grammar) > 0:
        max_length = __get_max_variable_length(grammar)

        for variable in grammar:
            prolonged_variable = variable

            while len(prolonged_variable) < max_length:
                prolonged_variable += ' '

            print(prolonged_variable + " -> ", end='')
            replacement_str = ''
            sorted_replacements = sorted(grammar[variable])

            for replacement in sorted_replacements:
                for symbol in replacement:
                    if symbol[0] == 't':
                        replacement_str += 'ε' if symbol[1] == '' else symbol[1]
                    else:
                        replacement_str += symbol[1]  # TODO: emphasize that it's a variable somehow
                replacement_str += '|'
            replacement_str = replacement_str[:len(replacement_str) - 1]
            print(replacement_str)
    else:
        print('empty grammar')
    print('')


def __read_input_file():
    try:
        with open(input_file, 'r') as f:
            rules = f.readlines()
        # strips whitespace symbols from both ends of each line and filters empty ones afterwards
        return list(filter(None, [x.strip() for x in rules]))
    except IOError as e:
        raise BadInputException("Things went wrong while reading from the input file: " + str(e))


def __validate_variable(variable):
    for ch in variable:
        if ch == '(' or ch == ')':
            raise BadInputException("Brackets can't be used in variables")
        elif ch == '|':
            raise BadInputException("Vertical bars can't be used in variables")
        elif ch == '\\':
            raise BadInputException("Backslashes can't be used in variables")
        elif ch == '"':
            raise BadInputException("Double quotes can't be used in variables")


def __parse_replacements(replacements_str):
    replacements = set()

    for string in __split_by_vertical_bar(replacements_str):
        replacement = []

        if string == '':
            # this will be epsilon
            replacement.append(('t', ''))
        else:
            i = 0
            while i < len(string):
                if string[i] == '\\':
                    if i == len(string) - 1:
                        raise BadInputException("A backslash has to either escape a terminal symbol "
                                                "or be escaped itself")
                    replacement.append(('t', string[i + 1]))
                    i += 1
                elif string[i] == '(':
                    opened_at = i
                    closed_at = __skip_to_closing_bracket(string, opened_at)
                    replacement.append(('v', string[opened_at + 1: closed_at]))
                    i = closed_at
                elif string[i] == ')':
                    raise BadInputException("Invalid bracket structure")
                else:
                    replacement.append(('t', string[i]))
                i += 1

        replacements.add(tuple(replacement))

    return replacements


# to keep it fair, I don't use the built-in regex engine
def __split_by_vertical_bar(string):
    result = []

    i = 0
    while i < len(string):
        prev_symbol = string[i - 1] if i > 0 else None

        if string[i] == '|' and prev_symbol != '\\':
            result.append(string[:i])
            string = string[i + 1:]
            i = 0
        else:
            i += 1
    result.append(string)

    return result


def __skip_to_closing_bracket(string, opened_at):
    i = opened_at + 1
    while i < len(string):
        if string[i] == ')':
            break
        else:
            # don't want to write same exception throwing twice, so will just use existing method on each symbol
            __validate_variable(string[i])
            i += 1

    if i == len(string) or i - opened_at < 2:
        raise BadInputException("Invalid bracket structure")

    return i


def __get_max_variable_length(grammar):
    max_length = 0
    for variable in grammar:
        max_length = len(variable) if len(variable) > max_length else max_length
    return max_length
