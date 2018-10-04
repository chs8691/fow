###############################################################################
# Parameter checker and all its stuff
# Use check_options(). Methods, starting with an underscore (_) are private.
# Example: fw export --path /my/backup/path -t
# actual
# ------
#    actual={
#        'shorts': ['t'],
#        'names': ['path'],
#        'args': ['/my/backup/path']}
#
# rules
# -----
#    atom_path = dict(name='path', short='p', args=2)
#    atom_force = dict(name='force', short='f', args=0)
#    atom_test = dict(name='test', short='t', args=0)
#    atom_none = dict(name='', short='', args=2)

#    rules = [
#        [dict(atom=atom_path, obligat=True),
#         dict(atom=atom_force, obligat=False),
#         dict(atom=atom_test, obligat=False)],

#        [dict(atom=atom_none, obligat=True),
#         dict(atom=atom_force, obligat=False),
#         dict(atom=atom_test, obligat=False)]]
###############################################################################


def check_options(options, rules, command):
    """
    Check for the user input against the command-specific
    rule. If a rule violation is found, a message will be printed, otherwise
    the check is silent.
    options: dict with options values, see header description
    rules: rules, see header description
    command: String with command under check, for message printing
    Returns true, if options is valid, otherwise false.
    """
    # print('check_options() options=' + str(options))
    # print('check_options() rules=' + str(rules))
    see_msg = 'See "fow help ' + command + '".'

    # First, check that every options option is known by name
    # Regardless of particular paths. Just for printing a good message
    ret = _find_unknown_options(options, rules)
    if ret is not None:
        if ret['type'] == 'name':
            print('Unknown option --' + ret['option'] + '. ' + see_msg)
        else:
            print('Unknown option -' + ret['option'] + '. ' + see_msg)
        return
    # else:
    #     print('check_options() findUnknownOption=' + str(ret))

    # All options are known; now find the path that match the options
    rule = _find_rule(options, rules)
    if rule is None:
        print('Invalid option constellation. ' + see_msg)
        return False

    # print('check_options() Found rule=' + str(rule))

    message = _check_rule(options, rule, command)
    if message is not None:
        print(message)
        return False

    # print('check_options() Arguments are ok.')

    return True


def _find_unknown_options(options, rules):
    """
    Simple check, if all options options are defined in at least one rule.
    But it doesn't check for a valid rule.
    If an unknown option is found, information about it will be retured. Return
    format = dict(option='force', type='name'), where type can be 'name' or
    'short'.
    If all options are well known, False will be returned.
    False.
    """
    # First check all named options
    for actual_name in (n for n in options['names'] if n is not None):
        found_name = False
        for rule in rules:
            for node in rule:
                if node['atom']['name'] == actual_name:
                    found_name = True
                    break
            if found_name:
                break
        if not found_name:
            return dict(option=actual_name, type='name')

    # # Names or ok, now check short options
    # for actual_short in (n for n in options['shorts'] if n is not None):
    #     found_short = False
    #     for rule in rules:
    #         for node in rule:
    #             if node['atom']['short'] == actual_short:
    #                 found_short = True
    #                 break
    #         if found_short:
    #             break
    #     if not found_short:
    #         return dict(option=actual_short, type='short')

    return None


def _node_match_options(options, node):
    """
    Returns True, if there is an options option, that matches the node
    Example:
        atomShort = dict(name='short', short='s', args=0)
        node = dict(atom=atomShort, obligat=True)
    """
    # print('_node_match_options node=' + str(node))

    # # a none-option always match
    # if len(node['atom']['name']) == 0 and \
    #         len(node['atom']['short']) == 0:
    #     return True

    for name in options['names']:
        if name == node['atom']['name']:
            return True

    for short in options['shorts']:
        if short == node['atom']['short']:
            return True

    # print("returning false")
    return False


def _options_match_rule(items, rule, type):
    """
    Checks for items, if every item is valid for the given rule.
    Type must be either 'names' or 'shorts' and determines, what to check.
    The None-Item will be ignored.
    Returns True, if all items are defined in the rule, otherwise False.
    """
    # print('_options_match_rule() rule=' + str(rule))
    # print('_options_match_rule() type=' + type)
    # print('_options_match_rule() items=' + str(items))
    for item in items:
        # print('_options_match_rule() item=' + str(item))

        found_node = False
        # for node in [n for n in rule if len(n['atom']['name']) > 0]:
        for node in rule:
            if node['atom'][type] == item:
                found_node = True
                break
        if not found_node:
            # print('_options_match_rule() found_node=' + str(found_node))
            return False

    # print('_options_match_rule() return True')
    return True


def _has_duplicates(options, rule):
    """
    Returns True, if quantity of every option with the same name exceeds the rule's definitions
    """
    # print('_has_duplicates() rule=' + str(rule))
    # print('_has_duplicates() options=' + str(options))

    # List of actual names as a set (uniques)
    for actual_name in frozenset(options['names']):
        # print('_has_duplicates()   checking actual=' + str(actual_name))
        actual_nr = options['names'].count(actual_name)
        expected_nr = len([n for n in rule if n['atom']['name'] == actual_name])
        # print('_has_duplicates()   actual={}, expected={}'.format(str(actual_nr), str(expected_nr)))
        if actual_nr > expected_nr:
            return True

    return False


def _has_valid_options(options, rule):
    """
    Returns True, if options's options match this rule. Otherwise returns False.
    Doesn't check if options has additional invalid options.
    earlier step.
    """
    # print("_has_valid_options() options={}".format(str(options)))
    # print("_has_valid_options() rule={}".format(str(rule)))
    # check obligatory parameters
    # Be careful: A rule with a non-option returns true
    for node in rule:
        # print('_has_valid_options() processing node=' + str(node))
        if node['obligat'] is True:
            # print('_has_valid_options()   checking obligatory')
            if not _node_match_options(options, node):
                # print('_has_valid_options()    _node_match_options=False')
                return False

            # print('_has_valid_options()   _node_match_options=true')

    # check optionals
    # print('_has_valid_options() checking optionals rule=' + str(rule))
    if not (_options_match_rule([n for n in options['names'] if n is not None], rule, 'name') and
            _options_match_rule([n for n in options['shorts'] if n is not None], rule, 'short')):
        # print('_has_valid_options() optionals check _options_match_rule=' + 'False')
        return False

    else:
        # print('_has_valid_options() optionals check _options_match_rule=' + 'True')
        return True


# rules = [rule1, rule2, ...]
# rule = [node1, node2, ...]
# node = dict(atom_dict, obligat)
# atom_dict = dict(name='force', short = 's', args=2)
def _find_rule(options, rules):
    """
    Search the rule, that match its options. The search will stop
    at the first hit, so the rules have to been disjunkt.
    :Returns: found rule or, if nothing found None.
    """
    for rule in rules:
        # print("_find_rule() processing rule={}".format(str(rule)))
        if _has_valid_options(options, rule) and not _has_duplicates(options, rule):
            # print("_find_rule()   valid={}".format(str('true')))
            return rule

        # print("_find_rule()   valid={}".format(str('false')))

    return None


# def _check_args(actual, rule):
#     """
#     Counts number of actual arguments and number of defined arguments in
#     the rule.
#     Returns 0, if actual argument's number match the rules one.
#     Returns an integer < 0, if the actuals or to few.
#     Returns an integer > 0, if the actuals or to many.
#     """
#     print('_check_args() actual=' + str(actual))
#     print('_check_args() rule=' + str(rule))
#
#     actualsNr = len([n for n in actual['args'] if n is not None])
#     ruleMin = 0
#     ruleMax = 0
#
#     for node in rule:
#         if node['atom']['args'] == 1:
#             ruleMax += 1
#         elif node['atom']['args'] == 2:
#             ruleMax += 1
#             ruleMin += 1
#     print('_check_args() actualNr=' + str(actualsNr))
#     print('_check_args() ruleMin=' + str(ruleMin))
#     print('_check_args() ruleMax=' + str(ruleMax))
#
#     if actualsNr < ruleMin:
#         return actualsNr - ruleMin
#     elif actualsNr > ruleMax:
#         return actualsNr - ruleMax
#     else:
#         return 0


def _check_rule(actual_matrix, rule, command):
    """
    Check actual parameter vs. its rule
    :param actual_matrix: Options matrix
    :param rule: Give rule
    :param command: Name of the command under test
    :return: message in error case or None, of valid
    """
    # print('_check_rule() actual_matrix=' + str(actual_matrix))
    # print('_check_rule() rule=' + str(rule))

    for name in actual_matrix['names']:
        # print("_check_rule() processing actual name={}".format(name))
        for node in (n for n in rule if n['atom']['name'] == name):
            # print("_check_rule()   processing node={}".format(str(node)))
            arg = get_arg_by_name(actual_matrix, name)
            # print("_check_rule()   actual arg={}".format(str(arg)))
            if node['atom']['args'] == 0 and arg is not None:
                if name == '':
                    return "Unexpected argument '{0}' for command '{1}'".format(arg, command)
                else:
                    return "Unexpected argument '{0}' for option '{1}' not allowed. Usage: 'fow {1} --{2}'"\
                        .format(arg, command, name)
            elif node['atom']['args'] == 2 and arg is None:
                if name == '':
                    return ("Mandatory argument for command '{0}' is missing: fow {0} <arg>. " +
                            "See 'fow help {0}'.").format(command)
                else:
                    return ("Mandatory argument for option '{1}' missing." +
                            " Usage: fow {0} {1}=<arg> or fow {0} {1}='<arg>'. " +
                            "See 'fow help {0}'.").format(command, name)
            # print("_check_rule()   --> ok")

    return None


def get_arg_by_name(paramatrix, name):
    """
    For a given name, the arg value will returned
    :param paramatrix: normalized arg_structure, s. plumb.normalizeArgs()
    :param name: key of list names
    :return: String with arg or, if not found, None
    """
    # print("get_arg_by_name() paramatrix=" + str(paramatrix))
    # print("get_arg_by_name() name=" + str(name))
    if name not in paramatrix['names']:
        return None

    return paramatrix['args'][paramatrix['names'].index(name)]


def normalize_option_matrix(_actual, rules):
    """
    Replace missing shorts and names, so it's easier to analyze
    and read the arguments. 'args' won't be touched. Unknown options wil be ignored
    Example:
        _actual = {
            names=[None, 'test', 'notDefinedName], shorts=['c', None, None], args=['argCreate', 'argTest', None]
            }
        _rules = [Path1List, ...]
        pathList = [testDict, createDict, ...]
        testDict = {atom=atomTestDict, obligat=trueOrFalse}
        atomTestDict = {name='test', short='t', args=0_1_OR_2}  etc.
    :param _actual: n x n matrix with names, shorts and args
    :returns updated _actual: Example: { names=['create','test', 'notDefinesName],
        shorts=['c', 't', None],
        args=['argCreate', 'argTest', None] }
    """
    # print('normalizeArgs() _actual=' + str(_actual))
    # print('normalizeArgs() rules=' + str(rules))
    ret = _actual.copy()
    # founds = set()
    # print('copy=' + str(ret))
    for short in _actual['shorts']:
        i = _actual['shorts'].index(short)
        # print('short=' + short)
        for path in rules:
            # print('path=' + str(path))
            for node in path:
                # print('node=' + str(node))
                if short == node['atom']['short']:
                    # print('found short ' + short)
                    ret['names'][i] = node['atom']['name']
                    # if short in ret['shorts']:
                    #     founds.add(short)

    for name in _actual['names']:
        i = _actual['names'].index(name)
        # print('name={}, i={}'.format(name, i))
        for path in rules:
            # print('path=' + str(path))
            for node in path:
                # print('node=' + str(node))
                if name == node['atom']['name']:
                    # print('found name {}.'.format(name))
                    ret['shorts'][i] = node['atom']['short']
                    # if name in ret['names']:
                    #     founds.add(short)

    # print('founds=' + str(founds))

    # print('normalize_option_matrix() ret=' + str(ret))
    return ret
