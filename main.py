# -*- coding: utf-8 -*-
import os
import shutil
import re
import plump


#TODO ninja zeigt symbols nur bei fehlerfreiem Coding --> print korrigieren
#OPTIMIZE Config keys in Hilfe listen
#FIXME config: wird beim Schreiben eines Eintrags die pickle datei \
#     erzeugt, wird trotzdem settings.pickle not found ausgegeben


def task(_arg_struct):
    """
    Task manipulation.
    """

    ##0: No param allowed, 1: param optional, 2: param obligatory
    #if not checkArgs(_arg_dict,
    #    {'-t': 0, '--test': 0, '-p': 2, '--path': 2}):
    #    return
    atom_create = dict(name='create', short='c', args=2)
    atom_activate = dict(name='activate', short='a', args=2)
    atom_show = dict(name='show', short='s', args=0)
    atom_none = dict(name='none', short='n', args=0)

    #print('_arg_struct=' + str(_arg_struct))
    rules = [
        [dict(atom=atom_none, obligat=True)],
        [dict(atom=atom_create, obligat=True)],
        [dict(atom=atom_activate, obligat=True)],
        [dict(atom=atom_show, obligat=True)]
        ]

    if not plump.checkParams(_arg_struct, rules):
        return

    #Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)
    #print('args=' + str(args))

    #print('Params=' + str(arg_dict))

    #task --show
    if 'show' in args['names'] or 'none' in args['names']:
        print('Actual task is ' + plump.getActualTask()['task'] + '.')
        return

    #task --create <task>
    if 'create' in args['names']:
        #<task> is just a name
        if args['args'][0].count('/') == 0:
            if plump.getActualTask() is None:
                print('No actual task set. ' +
                    'Use first "task --activate <task>" to activate an ' +
                    'existing task or use "task --create <folder/name>" ' +
                    ' to specify the task name and its direcory.')
                return

            else:
                name = plump.getActualTask()['folder'] + '/' + args['args'][0]

        #<task> contains a path
        else:
            name = args['args'][0]

        if plump._exist_dir(name):
            print('task ' + name + 'alread exists.' +
            ' Choose a different name to create a new task.')
            return

        os.makedirs(plump.DIR_02 + '/' + name)
        os.mkdir(plump.DIR_02 + '/' + name + '/' + plump.DIR_FINAL)
        os.mkdir(plump.DIR_02 + '/' + name + '/' + plump.DIR_JPG)
        os.mkdir(plump.DIR_02 + '/' + name + '/' + plump.DIR_RAW)
        os.mkdir(plump.DIR_02 + '/' + name + '/' + plump.DIR_WORK)
        plump.setConfig(plump.TASK, name)


def backup(_arg_struct):
    """
    Backup data to external file system. Imput is the argument structure.
    """
    ##0: No param allowed, 1: param optional, 2: param obligatory
    #if not checkArgs(_arg_dict,
    #    {'-t': 0, '--test': 0, '-p': 2, '--path': 2}):
    #    return

    atomTest = dict(name='test', short='t', args=0)
    atomPath = dict(name='path', short='p', args=2)
    atomNone = dict(name='none', short='n', args=0)

    #atomNone must be mandatory for rules with more than one path
    rules = [[dict(atom=atomNone, obligat=True),
                dict(atom=atomTest, obligat=False)],
             [dict(atom=atomPath, obligat=True),
                dict(atom=atomTest, obligat=False)]]

    if not plump.checkParams(_arg_struct, rules):
        return

    #Normalize for easy access: -t -> --test etc.
    args = plump.plump.normalizeArgs(_arg_struct, rules)
    #print('args=' + str(args))

    #backup --path <path>
    if 'path' in args['names']:
        path = args['args'][0]
    #backup
    else:
        if not plump.BACKUP_DIR in plump.readConfig() or \
            plump.readConfig()[plump.BACKUP_DIR] == 'None' or \
            plump.readConfig()[plump.BACKUP_DIR] is None:
            print('Backup directory not set. Use "backup <path>" for this ' +
                'call or set backup path with "config backupDir <path>".')
            return
        else:
            path = plump.readConfig()[plump.BACKUP_DIR]

    #backup --test
    if 'test' in args['names']:
        option_test = ' --dry-run '
    else:
        option_test = ' '

    if not os.path.exists(path):
        print('Path does not exists. Check directory "' + path + '".')
        return

    print('Starting backup to "' + os.path.abspath(path) + '".')
    os.system('rsync -rltv --delete --info=stats2' + option_test
        + '. ' + path)


def config(_arg_struct):
    """
    Set or delete a config item
    """

    atom_delete = dict(name='delete', short='d', args=2)
    atom_list = dict(name='list', short='l', args=1)
    atom_none = dict(name='none', short='n', args=0)
    atom_set = dict(name='set', short='s', args=2)

    #atomNone must be mandatory for rules with more than one path
    rules = [[dict(atom=atom_none, obligat=True)],
             [dict(atom=atom_list, obligat=True)],
             [dict(atom=atom_delete, obligat=True)],
             [dict(atom=atom_set, obligat=True)]]

    if not plump.checkParams(_arg_struct, rules):
        return

    #Normalize for easy access: -t -> --test etc.
    #args = {names=[<option1>,...], args=[<arg1>,...]}
    args = plump.plump.normalizeArgs(_arg_struct, rules)

    settings = plump.readConfig()

    if 'delete' in args['names']:
        settings[args['args'][0]] = 'None'
        plump.writeConfig(settings)
        return

    if 'list' in args['names'] or 'none' in args['names']:
        if len(args['args']) == 0:
            for key, value in list(settings.items()):
                print((key + ' = ' + str(value)))
        else:
            print((settings[args['args'][0]]))

    if 'set' in args['names']:
        (key, value) = args['args'][0].split('=')
        settings[key] = value
        plump.writeConfig(settings)


def init(_arg_struct):
    """
    Initializes the fow. Call this once.
    """

    atomForce = dict(name='force', short='f', args=0)
    atomNone = dict(name='none', short='n', args=0)

    #Set atomNone as non-obligat, otherwise check will fail
    rules = [[dict(atom=atomNone, obligat=False),
                dict(atom=atomForce, obligat=False)]]

    if not plump.checkParams(_arg_struct, rules):
        return

    #Normalize for easy access: -t -> --test etc.
    args = plump.plump.normalizeArgs(_arg_struct, rules)
    #print('args=' + str(args))

    if not 'force' in args['names']:
        for dir in plump.getAllFowDirs().values():
            if plump._exist_dir(dir):
                print('"' + dir + '" already exists. ' + 'Use -f option to ' +
                'force deleting all existings fow-directories.')
                return

    for dir in plump.getAllFowDirs().values():
        if plump._exist_dir(dir):
            shutil.rmtree(dir)

    os.mkdir(plump.DIR_FOW)
    settings = dict()
    plump.writeConfig(settings)

    os.mkdir(plump.DIR_00)
    os.mkdir(plump.DIR_00 + '/' + plump.DIR_JPG)
    os.mkdir(plump.DIR_00 + '/' + plump.DIR_RAW)

    os.mkdir(plump.DIR_01)
    os.mkdir(plump.DIR_01 + '/' + plump.DIR_JPG)
    os.mkdir(plump.DIR_01 + '/' + plump.DIR_RAW)

    os.mkdir(plump.DIR_02)

    #Define all settings and initialze them
    plump.writeConfig({plump.GPX_DIR: None,
                plump.BACKUP_DIR: None,
                plump.TASK: None})


def fow(args=None):
    """
    Generic command executor for consuming fow commands.
    cmd    list with arguments
    """
    if args is None or len(args) == 1:
        print('fow version ' + plump.VERSION + '. "help" shows all commands.')
        return

    #print((str(len(cmds)) + ' args=' + str(cmds)))
    cmds = args[1:]

    if cmds[0] == 'help':
        showHelp(plump.toArgStruct(cmds[1:]))

    elif cmds[0] == 'config':
        config(plump.toArgStruct(cmds[1:]))

    elif cmds[0] == 'init':
        init(plump.toArgStruct(cmds[1:]))

    elif cmds[0] == 'backup':
        backup(plump.toArgStruct(cmds[1:]))

    elif cmds[0] == 'task':
        task(plump.toArgStruct(cmds[1:]))

    else:
        print('Unknown command. Use help to list all commands.')


def showHelp(_arg_struct):
    """
    generate help and show it. For specific command help, there has to be one
    file for each command with name help_<command>.txt. The first line of this
    file must be the abstract of the command.
    """
    atomNone = dict(name='none', short='n', args=1)

    #For commands with only one path atomNone must be non-obligatory!
    rules = [[dict(atom=atomNone, obligat=False)]]

    if not plump.checkParams(_arg_struct, rules):
        return

    #Normalize for easy access: -t -> --test etc.
    args = plump.plump.normalizeArgs(_arg_struct, rules)
    #help
    if len(args['args']) == 0:
        #Get all help files in the help dir

        try:
            pattern = re.compile('help_\w+.txt')
            names = [f for f in os.listdir(plump.getHelpFileDir())
                        if os.path.isfile(os.path.join(
                        plump.getHelpFileDir(), f))
                        and pattern.match(f)]
            print(('fow commands:'))
            out = ''
            for f in names:
                    with open(os.path.join(
                        plump.getHelpFileDir(), f)) as help_file:
                        out += help_file.readline()
                        #print(help_file.readline(), end='')
            print(out[0:-1])
        except:
            print('Uuups, could not find the help files in directory "' +
                plump.getHelpFileDir()
                + '". Please, check your fow installation.')
            return

    #help <command>
    elif len(args['args']) == 1:
            try:
                with open(os.path.join(plump.getHelpFileDir(),
                        'help_' + args['args'][0] + '.txt'), 'r') as data:
                    out = ''
                    for each_line in data:
                        out += each_line
                        #print(each_line, end='')
                    print(out[0:-1])
            except:
                print(args['args'][0] + ' is unknown. ' +
                'Use help to see all commands.')


