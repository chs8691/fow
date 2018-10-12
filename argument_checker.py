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
import re
from plump import NONE_PARAM, MANDATORY_PARAM


def check_rules(cmd_list, rules):
    """
    Checks arguments against the rules and print a message if a violation is found.
    :param cmd_list: Command line args
    :param rules: Rule set
    :return: dictionary with 'message' [error message text|None], 'rule' with [rule|None] and list with
    options dicts (empty, if options not valid).
    """

    atom_list = []
    # extract atoms in a unique list
    for rule in rules:
        for item in rule:
            if item['atom'] not in atom_list:
                atom_list.append(item['atom'])

    args = _normalize_commands(cmd_list, atom_list)
    # print('check_rules() args={}'.format(args))

    ret = _analyze_rules(args, rules)
    if ret['message'] is not None:
        print(ret['message'])

    return ret


def _analyze_rules(args, rules):
    """
    Parse rule set to find the rule which options match the mandatory expected ones.
    :param args: Command line list, e.g. ['config', '--create', 'x;, '--test']
    :param rules: [rules1, rules2, ...]
    :return: dictionary with 'message' [error message text|None], 'rule' with [rule|None] and list with
    options dicts (empty, if options not valid).
    """
    ret = dict(message=None, rule=None, options=dict())

    # print("_analyze_rules() rules={}".format(str(rules)))
    # print("_analyze_rules() args={}".format(str(args)))

    # 1. Check that all args are known
    for arg in (a for a in args if re.match('^--\w+$', a)):
        found = False
        for rule in rules:
            if len([i for i in rule if i['atom']['name'] == arg[2:]]) > 0:
                found = True
                break
        if not found:
            ret['message'] = "Unknown option '{}'".format(arg[2:])
            return ret

    # Now we can check all args and options
    # print("_analyze_rules() Check rule by rule against the actuals")
    for rule in rules:
        # print("\nanalyze_rules()   rule={}".format(str(rule)))
        valid_rule = True

        # --- 1. Check obligatory rule item against actuals --- #
        for rule_item in (i for i in rule if i['obligat']):
            # print("_analyze_rules()     item={}".format(str(rule_item)))
            if rule_item['atom']['name'] == '':
                continue
            try:
                args.index("--{}".format(rule_item['atom']['name']))
            except ValueError:
                # print("_analyze_rules()     ValueError={}".format(str(rule_item['atom']['name'])))
                ret['message'] = "Missing obligatory parameter '{}'".format(rule_item['atom']['name'])
                valid_rule = False
                break

        if not valid_rule:
            # print("_analyze_rules()   rule->arg: not valid")
            continue
        # else:
        #     print("_analyze_rules()   rule->arg: valid")

        # --- 2. Check all args against rule items --- #
        # print("_analyze_rules()   2. Check all args against rule items")
        for arg in (a for a in args if re.match('^--\S+$', a)):
            # print("_analyze_rules()     arg={}".format(str(arg)))
            if len([i for i in rule if i['atom']['name'] == arg[2:]]) == 0:
                # print("_analyze_rules()     not found={}".format(str(arg)))
                ret['message'] = "Unexpected option '{}'".format(arg[2:])
                valid_rule = False
                break

        if not valid_rule:
            continue

        # print("\n_find_rule_by_mandatory()   valid rule={}".format(str(rule)))

        # ----------------------------------- #
        # --- Now we have chosen the rule --- #
        # ----------------------------------- #
        params_ret = _analyze_params(args, rule)

        if valid_rule:
            ret['rule'] = rule
            if params_ret['valid_options']:
                ret['options'] = params_ret['options']
                ret['message'] = None
            else:
                ret['message'] = params_ret['message']

            break

    return ret


def _analyze_params(args, rule):
    """
    Checks for one valid rule the parameters
    """
    ret = dict(message=None, options=dict(), valid_options=True)

    # print("\n_find_rule_by_mandatory()   rule={}".format(str(rule)))
    # print("_analyze_rules()   checking args {}".format(str(args)))
    # --- 3. Check parameters --- #
    for arg in (a for a in args if re.match('^--\S+$', a)):
        rule_item = [i for i in rule if i['atom']['name'] == arg[2:]][0]
        # print("_analyze_rules()     arg={} rule_item={}".format(str(arg), str(rule_item)))
        # Not the last item
        if (args.index(arg) + 1) < (len(args)) and re.match('[^-].*', args[args.index(arg) + 1]):
            param_actual = True
            # print("_analyze_rules()     arg2 {}".format(str(arg2)))
        else:
            param_actual = False

        if rule_item['atom']['args'] == NONE_PARAM and param_actual:
            ret['message'] = "Option '{}' may not have an argument".format(arg[2:])
            ret['valid_options'] = False
            break

        if rule_item['atom']['args'] == MANDATORY_PARAM and not param_actual:
            ret['message'] = "Missing mandatory argument for option '{}'".format(arg[2:])
            # print("_analyze_rules()     message={}".format(str(ret['message'])))
            ret['valid_options'] = False
            break

        # mark checked values as empty string and save options/param for return
        if ret['valid_options'] and param_actual:
            ret['options'][args[args.index(arg)][2:]] = args[args.index(arg) + 1]
            args[args.index(arg) + 1] = ''
        else:
            ret['options'][args[args.index(arg)][2:]] = None

        args[args.index(arg)] = ''

    # print("_analyze_rules()  args is now={}".format(str(args)))

    if ret['valid_options']:
        # print("_analyze_rules()  valid options")
        # Always return the '' option
        ret['options'][''] = None
        # Check now '' rule
        try:
            rule_item = [i for i in rule if i['atom']['name'] == ''][0]
            expected_none_arg = rule_item['atom']['args']
        except IndexError:
            expected_none_arg = NONE_PARAM

        # print("_analyze_rules() expected_none_arg={}".format(str(expected_none_arg)))

        if len([a for a in args[1:] if len(a) > 0]) > 0:
            # find all not handled items
            for arg in (a for a in args[1:] if len(a) > 0):
                if expected_none_arg == NONE_PARAM:
                    ret['message'] = "Unexpected argument '{}'".format(arg)
                    ret['valid_options'] = False
                    break
                else:
                    ret['options'][''] = arg
                    args[args.index(arg)] = ''
                    # parameter found, no more parameter expected
                    expected_none_arg = NONE_PARAM
        else:
            if expected_none_arg == MANDATORY_PARAM:
                ret['message'] = "Missing argument."
                ret['valid_options'] = False

        # print("_analyze_rules() expected_none_arg={}".format(str(expected_none_arg)))

    return ret


def _normalize_commands(_actual, atoms):
    """
    Replace shorts by names, so it's easier to analyze
    and read the arguments. Unknown options wil be ignored
    Example:
        _actual = ['config', '--create', 'x;, '-t']
        atoms = [atom1, atom2, ...]
        return = ['config', '--create', 'x, '--test']
    :param _actual: command line arguments
    :param atoms: Simple list of rules
    :returns updated _actual
    """

    # print("_normalize_commands() atoms={}".format(atoms))
    # print("_normalize_commands() actuals={}".format(str(_actual)))

    ret = _actual.copy()
    for arg in _actual[1:]:
        if re.match('^-\w$', arg):
            for rule in (r for r in atoms if r['short'] == arg[1:]):
                ret[_actual.index(arg)] = "--{}".format(rule['name'])
                # print("_normalize_commands() arg {0} to {1}".format(arg, ret[_actual.index(arg)]))
        # else:
        #     print("_normalize_commands() arg {} not matching".format(arg))

    # Unknown shorts have to be converted too: -x to --x
    for arg in (a for a in ret[1:] if re.match('^-\w$', a)):
        ret[ret.index(arg)] = "-{}".format(arg)

    # print("_normalize_commands() ret={}".format(str(ret)))
    return ret
