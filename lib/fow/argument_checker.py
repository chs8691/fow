###############################################################################
# Parameter checker and all its stuff
# Use check_params(). Methods, startging with an underscore (_) are private.
###############################################################################


def check_params(actual, rules):
    """
    """
    #print('actual=' + str(actual))
    #print('rules=' + str(rules))

    #First, check that every actual options is known (names and shorts)
    #Regardless of particualar pathes. Just for printing a good message
    ret = _find_unknown_options(actual, rules)
    if not ret is None:
        if ret['type'] == 'name':
            print('Unknown option --' + ret['option'] + ' for this command.')
        else:
            print('Unknown option -' + ret['option'] + ' for this command.')
        return
    #else:
        #print('checkParams() findUnknownOption=' + str(ret))

    #All options are known; now find the path that match the options
    rule = _find_rule_by_options(actual, rules)
    if rule is None:
        print('Missing obligatorie parameter(s), please check the options.')
        return
    #else:
        #print('checkParams() Found rule=' + str(rule))

    #Check actual arguments againts this path
    cnt = _check_args(actual, rule)
    if cnt < 0:
        print('Missing arguments. Check the options and its arguments.')
    elif cnt > 0:
        print('Too many arguments. Check the options and its arguments.')
    #else:
        #print('checkParams() Arguments are ok.')


def _find_unknown_options(actual, rules):
    """
    Simple check, if alle actual options are defined in at least one rule.
    But it doesn't check for a valid rule.
    If an unknown option is found, information about it will be retured. Return
    format = dict(option='force', type='name'), where type can be 'name' or
    'short'.
    If all options are well known, False will be returned.
    False.
    """
    #First check all named options
    for actual_name in actual['names']:
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

    #Names or ok, now check short options
    for actual_short in actual['shorts']:
        found_short = False
        for rule in rules:
            for node in rule:
                if node['atom']['short'] == actual_short:
                    found_short = True
                    break
            if found_short:
                break
        if not found_short:
            return dict(option=actual_short, type='short')

    return None


def _node_match_actual(actual, node):
    """
    Returns True, if there is an actual option, that matches the node
    Example:
        atomShort = dict(name='short', short='s', args=0)
        node = dict(atom=atomShort, obligat=True)
    """
    #print('node=' + str(node))

    #The None-Option always match
    if len(node['atom']['name']) == 0 and \
        len(node['atom']['short']) == 0:
        return True

    for name in actual['names']:
        if name == node['atom']['name']:
            return True

    for short in actual['shorts']:
        if short == node['atom']['short']:
            return True

    return False


def _options_match_rule(items, rule, type):
    """
    Checks for items, if every item is valid for the give rule.
    Type must be either 'names' or 'shorts' and determines, what to check.
    Returns True, if all items are defined in the rule, otherwise False.
    """
    for item in items:
        found_node = False
        for node in rule:
            if node['atom'][type] == item:
                found_node = True
                break
        if not found_node:
            return False

    return True


def _has_valid_options(actual, rule):
    """
    Returns True, if actal's options match this rule. Otherswise returns False.
    Doesn't check if actual has additional invalid options.
    earlier step.
    """
    #check obligatories
    for node in rule:
        if node['obligat'] is True:
            #print('node=' + str(node))
            if not _node_match_actual(actual, node):
                return False

    #check optionals
    if not _options_match_rule(actual['names'], rule, 'names') and \
       not _options_match_rule(actual['shorts'], rule, 'shorts'):
        return False

    return True


#rules = [rule1, rule2, ...]
#rule = [node1, node2, ...]
#node = dict(atom_dict, obligat)
#atom_dict = dict(name='force', short = 's', args=2)
def _find_rule_by_options(actual, rules):
    """
    Search the rule, that match its options. The search will stop
    at the first hit, so the rules have to been disjunked.
    Returs found rule or, if nothing found None.
    """
    for rule in rules:
        if _has_valid_options(actual, rule):
            return rule

    return None


def _check_args(actual, rule):
    """
    Counts number of actual arguments and number of defines arguments in
    the rule.
    Returns 0, if actual argument's number match the rules one.
    Returns an integer < 0, if the actuals or to few.
    Returns an integer > 0, if the actuals or to many.
    """
    actualsNr = len(actual['args'])
    ruleMin = 0
    ruleMax = 0

    for node in rule:
        if node['atom']['args'] == 1:
            ruleMax += 1
        elif node['atom']['args'] == 2:
            ruleMax += 1
            ruleMin += 1

    if actualsNr < ruleMin:
        return actualsNr - ruleMin
    elif actualsNr > ruleMax:
        return actualsNr - ruleMax
    else:
        return 0

