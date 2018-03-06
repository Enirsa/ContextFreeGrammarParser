from collections import OrderedDict


# this is how epsilon is represented inside the program
# the comma is needed to specify that this is a tuple inside a tuple
epsilon = (('t', ''),)


def remove_nullable_vars(old_grammar):
    if len(old_grammar) == 0:
        return OrderedDict()

    new_grammar = OrderedDict()
    start_variable = list(old_grammar.keys())[0]

    directly_nullable_vars = __get_directly_nullable_vars(old_grammar)
    nullable_vars = set(directly_nullable_vars)
    __add_indirectly_nullable_vars(old_grammar, nullable_vars)

    # workaround for the case when an empty string belongs to the language
    if start_variable in nullable_vars:
        new_start_var = start_variable + "'"

        while new_start_var in old_grammar:
            new_start_var += "'"

        new_grammar[new_start_var] = {
            epsilon,
            (('v', start_variable),)
        }

    for variable in old_grammar:
        if variable in directly_nullable_vars:
            replacements = set(old_grammar[variable])
            replacements.remove(epsilon)
            if len(replacements) > 0:
                new_grammar[variable] = replacements
        else:
            new_grammar[variable] = set(old_grammar[variable])

    __bisect_replacements(new_grammar, nullable_vars)

    return new_grammar


def reduce_grammar(grammar):
    if len(grammar) == 0:
        return OrderedDict()

    reduced_grammar = __remove_nongenerating_vars(grammar)

    if len(reduced_grammar) > 1:
        reduced_grammar = __remove_unreachable_vars(reduced_grammar)

    return reduced_grammar


def eliminate_left_recursion(grammar):
    if len(grammar) == 0:
        return OrderedDict()

    new_grammar = OrderedDict()
    variables = list(grammar.keys())

    for i in range(len(variables)):
        new_replacements = set() if i > 0 else set(grammar[variables[i]])

        for j in range(i):
            for replacement in grammar[variables[i]]:
                if replacement[0][0] == 'v' and variables.index(replacement[0][1]) == j:
                    new_replacements = new_replacements | __append_postfix(grammar[variables[j]], replacement[1:])
                else:
                    new_replacements.add(replacement)

        immediate_rec = set()

        for replacement in new_replacements:
            if replacement[0][0] == 'v' and replacement[0][1] == variables[i]:
                immediate_rec.add(replacement)

        if len(immediate_rec) > 0:
            new_replacements = new_replacements - immediate_rec

            without_first_variables = set()
            for replacement in immediate_rec:
                without_first_variables.add(tuple(list(replacement)[1:]))

            additional_var = variables[i] + "'"

            while additional_var in grammar:
                additional_var += "'"

            new_replacements = __append_postfix(new_replacements, (('v', additional_var),))
            additional_replacements = __append_postfix(without_first_variables, (('v', additional_var),))
            additional_replacements.add(epsilon)

            new_grammar[variables[i]] = new_replacements
            new_grammar[additional_var] = additional_replacements
        else:
            new_grammar[variables[i]] = new_replacements

    return new_grammar


def left_factor(grammar):
    if len(grammar) == 0:
        return OrderedDict()

    new_grammar = OrderedDict()

    for variable in grammar:
        new_replacements = set(grammar[variable])
        additional_rules = OrderedDict()

        while True:
            prefix = __get_longest_common_prefix(new_replacements)

            if prefix is not None:
                same_prefix = set()

                for replacement in new_replacements:
                    if len(replacement) >= len(prefix) and list(replacement)[:len(prefix)] == prefix:
                        same_prefix.add(replacement)

                if len(same_prefix) > 1:
                    new_replacements = new_replacements - same_prefix

                    additional_var = variable + "'"
                    while additional_var in grammar or additional_var in additional_rules:
                        additional_var += "'"

                    new_replacements.add(tuple(prefix + [('v', additional_var)]))
                    additional_rules[additional_var] = __crop_prefix(prefix, same_prefix)
            else:
                break

        new_grammar[variable] = new_replacements

        for var in additional_rules:
            new_grammar[var] = additional_rules[var]

    return new_grammar


def parse(string, grammar):
    if len(grammar) == 0:
        return False

    start_variable = list(grammar.keys())[0]

    if len(string) == 0:
        return epsilon in grammar[start_variable]

    return __recursive_descent(string, 0, grammar, start_variable) != -1


def __get_directly_nullable_vars(grammar):
    directly_nullable_vars = set()

    for variable in grammar:
        if epsilon in grammar[variable]:
            directly_nullable_vars.add(variable)

    return directly_nullable_vars


def __add_indirectly_nullable_vars(grammar, nullable_vars):
    found_nullable = True

    while found_nullable:
        found_nullable = False

        for variable in grammar:
            if variable in nullable_vars:
                continue

            nullable = False

            for replacement in grammar[variable]:
                nullable_replacement = True

                for symbol in replacement:
                    if symbol[0] == 't' or symbol[1] not in nullable_vars:
                        nullable_replacement = False
                        break

                if nullable_replacement:
                    nullable = True
                    break

            if nullable:
                nullable_vars.add(variable)
                found_nullable = True
                break


def __bisect_replacements(grammar, nullable_vars):
    for n_variable in nullable_vars:
        for variable in grammar:
            new_replacements = set()

            for replacement in grammar[variable]:
                bisection_result = set()
                __bisect_replacement(replacement, n_variable, 0, bisection_result)

                # means current nullable variable isn't present in this replacement, just keep it as it is
                if len(bisection_result) == 0:
                    bisection_result.add(replacement)

                new_replacements = new_replacements | bisection_result

            grammar[variable] = new_replacements


def __bisect_replacement(replacement, by_variable, from_index, bisection_result):
    for i in range(from_index, len(replacement)):
        if replacement[i][0] == 'v' and replacement[i][1] == by_variable:
            # variant with the nullable variable present
            bisection_result.add(replacement)
            __bisect_replacement(replacement, by_variable, i + 1, bisection_result)

            # variant with the nullable variable removed (in case of a non-empty result)
            if len(replacement) > 1:
                temp_list = list(replacement)
                temp_list.pop(i)
                new_replacement = tuple(temp_list)
                bisection_result.add(new_replacement)
                __bisect_replacement(new_replacement, by_variable, i, bisection_result)


def __remove_nongenerating_vars(old_grammar):
    new_grammar = OrderedDict()
    generating_vars = __get_generating_vars(old_grammar)

    for variable in old_grammar:
        if variable in generating_vars:
            new_replacements = __get_new_replacements(old_grammar[variable], generating_vars)

            if len(new_replacements) > 0:
                new_grammar[variable] = new_replacements

    if list(old_grammar.keys())[0] not in new_grammar:
        return OrderedDict()
    else:
        return new_grammar


def __get_generating_vars(grammar):
    generating_vars = set()
    changes_made = True

    while changes_made:
        changes_made = False

        for variable in grammar:
            if variable not in generating_vars and __is_generating(grammar[variable], generating_vars):
                generating_vars.add(variable)
                changes_made = True

    return generating_vars


def __is_generating(replacements, generating_vars):
    for replacement in replacements:
        generating = True

        for symbol in replacement:
            if symbol[0] == 'v' and symbol[1] not in generating_vars:
                generating = False
                break

        if generating:
            return True

    return False


def __get_new_replacements(old_replacements, generating_vars):
    new_replacements = set()

    for replacement in old_replacements:
        include = True

        for symbol in replacement:
            if symbol[0] == 'v' and symbol[1] not in generating_vars:
                include = False
                break

        if include:
            new_replacements.add(replacement)

    return new_replacements


def __remove_unreachable_vars(old_grammar):
    new_grammar = OrderedDict()
    reachable_vars = set()
    start_variable = list(old_grammar.keys())[0]
    reachable_vars.add(start_variable)
    __fill_reachable_vars(start_variable, old_grammar, reachable_vars)

    for variable in old_grammar:
        if variable in reachable_vars:
            new_grammar[variable] = set(old_grammar[variable])

    return new_grammar


def __fill_reachable_vars(variable, grammar, reachable_vars):
    for replacement in grammar[variable]:
        for symbol in replacement:
            if symbol[0] == 'v' and symbol[1] not in reachable_vars:
                reachable_vars.add(symbol[1])
                __fill_reachable_vars(symbol[1], grammar, reachable_vars)


def __append_postfix(replacements, postfix):
    result = set()

    for replacement in replacements:
        with_postfix = tuple(list(replacement) + list(postfix)) if replacement != epsilon else postfix
        result.add(with_postfix)

    return result


def __get_longest_common_prefix(replacements):
    replacements_l = list(replacements)
    replacements_l.sort(key=len, reverse=True)

    for replacement in replacements_l:
        if len(replacement) > 1:
            i = -1
            while i > -len(replacement):
                prefix = list(replacement)[:i]

                for r in replacements_l:
                    if r is replacement:
                        continue

                    if len(r) >= len(prefix) and list(r)[:len(prefix)] == prefix:
                        return prefix

                i -= 1

    return None


def __crop_prefix(prefix, replacements):
    result = set()

    for replacement in replacements:
        cropped = tuple(list(replacement)[len(prefix):])

        if len(cropped) == 0:
            cropped = epsilon

        result.add(cropped)

    return result


def __recursive_descent(string, position, grammar, var):
    first_iteration = var is list(grammar.keys())[0]

    for replacement in grammar[var]:
        current_pos = position

        for i in range(len(replacement)):
            if replacement[i][0] == 'v':
                current_pos = __recursive_descent(string, current_pos, grammar, replacement[i][1])
            elif replacement[i][1] == string[current_pos]:
                current_pos += 1
                current_pos = -1 if (current_pos == len(string) and i != len(replacement) - 1) else current_pos
            else:
                current_pos = -1

            if current_pos == -1:
                break

        if current_pos != -1 and (current_pos == len(string) or not first_iteration):
            return current_pos

    if not first_iteration and epsilon in grammar[var]:
        return position

    return -1
