# -*- coding: utf-8 -*-
import pickle
import os
import shutil
import re


DIR_00 = '00_Inbox'
DIR_01 = '01_Import'
DIR_02 = '02_Progress'
DIR_FOW = '.fow'
DIR_JPG = 'jpg'
DIR_RAW = 'raw'
DIR_FINAL = 'final'
DIR_WORK = 'work'
VERSION = '0.0.1'
BACKUP_DIR = 'backupDir'
GPX_DIR = 'gpxDir'
TASK = 'task'


def getHelpFileDir():
    """
    Returns the string path to the help files. In this directory, there has
    to be a file for every command.
    """
    return 'helpFiles'


def checkParams(_actual, _rules):
    """
    Validation checker for the given arguments. Return True, if arg_struct
    is valid, otherwise False. allowed_list is a list of dictionies. For
    every valid path, there is one item.
    Example:
        _actual = {
            names=['test', 'create'], shorts=['p'], args=['~/backup']
            }
        _rules = [Path1List, Path2List, ...]
        pathList = [Node1Dict, Node2Dict, ...]
        nodeDict = {atom=atom1Dict, obligat=trueOrFalse}
        atom = {name='name1', short='n', args=0_1_OR_2}

    Statement without a option must have this rule:
        atom = {name='name1', short='n', args=0_1_OR_2}

    Command without options
        A path without options must have an atom like this:
            atomNone = {name='none', short='n', args=0}
        For commands with only one path atomNone must be non-obligatory!
        For commands withmore than one path, atomNone must be obligatory!


    Values of args are a integer 0.2:
        0: Argument without parameter
        1: Argument has optional parameter
        2: Argument has an obligatory parameter
    Prints message for first failed validation and returns with False.
    """
    #print('actual=' + str(_actual))
    message = 'Unexpected arguments.'

    ################################################
    #--- Check, if there is an undefined option ---#
    ################################################
    validOptions = False
    actualOptionsSum = len(_actual['names']) + len(_actual['shorts'])
    for path in _rules:

        #print('path=' + str(path))

        # Search for unexpected options (names)
        foundNames = 0
        for actualName in _actual['names']:
            foundThisName = False
            #print('actualName ' + actualName)
            for ruleNode in path:
                if actualName == ruleNode['atom']['name']:
                    foundThisName = True
                    #print('found ' + actualName)
                    break
            if foundThisName:
                foundNames += 1
            else:
                #print('not found ' + actualName)
                message = '--' + actualName
                break

        # Now, search for unexpected options (shorts)
        foundShorts = 0
        for actualShort in _actual['shorts']:
            foundThisShort = False
            #print('actualShort=' + str(actualShort))
            for ruleNode in path:
                #print('ruleNode=' + str(ruleNode))
                if actualShort == ruleNode['atom']['short']:
                    foundThisShort = True
                    break
            if foundThisShort:
                foundShorts += 1
            else:
                message = '-' + actualShort
                break

        #print('foundShort=' + str(foundShorts))
        #print('foundName=' + str(foundNames))

        if foundShorts + foundNames == actualOptionsSum:
            validOptions = True
            break

    if not validOptions:
        #Path not valid
        print("Unknown option " + message)
        return False

    #print('All options are known.')

    # All options are known.
   ###############################################
   #--- Search the valid path for the options ---#
   ###############################################
    found_path = None
    for path in _rules:
        message = ''
        valid = True

        #print('path=' + str(path))

        # Check if expected nodes are called
        argsRange = dict(min=0, max=0)
        for node in path:
            #print('node=' + str(node))
            #print('_actual=' + str(_actual))
            #print('sum=' + str(len(_actual['names']) + len(_actual['shorts'])))
            #print('res=' + str(len(_actual['names']) +
                #len(_actual['shorts']) > 0))

            if node['atom']['name'] in _actual['names'] \
            or node['atom']['short'] in _actual['shorts']:
                if node['atom']['args'] == 1:
                    argsRange['max'] += 1
                elif node['atom']['args'] == 2:
                    argsRange['min'] += 1
                    argsRange['max'] += 1
            elif node['obligat']:
                #Mandatory parameter not used
                message = 'Missing masettings[cmds[0]] = ' + \
                            'cmds[1]ndatory option --' + \
                            str(node['atom']['name'])
                valid = False
                break

        # Found a valid path, exit.
        if valid:
            found_path = path
            break
        else:
            continue

    if found_path is None:
        print('Invalid options: ' + message)
        return False

    #print('Found path=' + str(found_path))

   ############################################
   #--- Check arguments for the found path ---#
   ############################################
    message = ''
    valid = True

    #print('path=' + str(found_path))
    #print('argsRange=' + str(argsRange))

    # Last check: number of arguments
    if len(_actual['args']) < argsRange['min']:
        valid = False
        message = 'Too less arguments for this option(s).'
    elif len(_actual['args']) > argsRange['max']:
        valid = False
        message = 'Too many arguments for this option(s).'

    if not valid:
        print('Invalid parameters: ' + message)
        return False
    #else:
        #print('Statement is ok.')

    return True


def getAllFowDirs():
    """
    Returns a dictionary with all fow sub directories. Use this to create dirs
    or for backup fow.
    """
    dirs = {'DIR_FOW': DIR_FOW,
            'DIR_00': DIR_00,
            'DIR_01': DIR_01,
            'DIR_02': DIR_02}
    return dirs


def normalizeArgs(_actual, rules):
    """
    Only changes shorts to name, so it's easier to analyze
    the arguments.
    Example:
        _actual = {
            names=[], shorts=['c', 't'], args=[]
            }
        _rules = [Path1List, ...]
        pathList = [testDict, createDict, ...]
        testDict = {atom=atomTestDict, obligat=trueOrFalse}
        atomTestDict = {name='test', short='t', args=0_1_OR_2}  etc.
        returns { names=['create','test'], args=[] }
    """
    #print('_actual=' + str(_actual))
    ret = _actual.copy()
    founds = set()
    #print('copy=' + str(ret))
    for short in _actual['shorts']:
        #print('short=' + short)
        for path in rules:
            #print('path=' + str(path))
            for node in path:
                #print('node=' + str(node))
                if short == node['atom']['short']:
                    #print('found short ' + short)
                    if not node['atom']['name'] in ret['names']:
                        ret['names'].append(node['atom']['name'])
                    #Delete only one time
                    if short in ret['shorts']:
                        founds.add(short)
                        #ret['shorts'].remove(short)

    #print('founds=' + str(founds))

    #print('ret=' + str(ret))
    return ret


def readConfig():
    """
    Returns a dictionary with setting.pickle.
    """
    settings = dict()
    try:
        with open('.fow/setting.pickle', 'rb') as data:
            settings = pickle.load(data)
    except:
        print('setting.pickle not found but will be created with next writing.')
    return settings


def _exist_dir(dir_name):
    """
    Returns True, if the directory exists
    """
    dirs = os.listdir('.')
    for dir in dirs:
        if dir == dir_name:
            return True
    return False


def getActualTask():
    """
    Returns dictionary wiht keys 'task', 'name' and 'folder'
    of the actual task or None, if not set.
    """
    item = readConfig()[TASK]
    if item is None or item == 'None':
        return None
    else:
        (folder, name) = item.rsplit('/', 1)
        task = {'task': item, 'name': name, 'folder': folder}
        return task


def toArgStruct(cmds):
    """
    Returns well formed structure of the given command list as a
    dictionary of two list options and args.
    Non option calls will be convereted to option '--none'
    Example:
    From ['--test', '--create', '-p', '~/backup']
    To   dict=(names=['test', 'create'], shorts=['p'], args=['~/backup'])
    Example:
    From ['~/backup']
    To   dict=(names=['none'], shorts=[], args=['~/backup'])
    """

    names = []
    shorts = []
    args = []

    for i in range(len(cmds)):
        #print('cmds i = ' + cmds[i])
        #print('cmds i = ' + cmds[i][0:2])
        if len(cmds[i]) >= 2 and cmds[i][0:2] == '--':
            names.append(cmds[i][2:])
        elif len(cmds[i]) >= 1 and cmds[i][0] == '-':
            shorts.append(cmds[i][1:])
        else:
            args.append(cmds[i])

    if len(names) + len(shorts) == 0:
        names.append('none')

    return dict(names=names, shorts=shorts, args=args)


def setConfig(key, value):
    """
    Updates or creates the specific value in the config pickle.
    Returns True, if item could be updated, otherwise False.
    """
    settings = readConfig()
    settings[key] = value

    return writeConfig(settings)


def writeConfig(settingDict):
    """
    Rewrites complete config pickle. Do set a specific config value,
    use setConfig()
    Returns True if setting.pickle could be written, otherwise Talse
    """
    try:
        with open('.fow/setting.pickle', 'wb') as data:
            pickle.dump(settingDict, data)
    except IOError as err:
        print('Could not save settings to setting.pickle: ' + str(err))
        return False
    return True

