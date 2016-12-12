# -*- coding: utf-8 -*-
import os
import shutil
import re
import plump
import gzip
import task
from argument_checker import check_params

#DONE Export to local directories added
#DONE fow config --delete erases now the property instead of setting it to 'None'
#DONE show: new argument 'in' shows import and inbox
#DONE Backup now uses same config-notation like export: backup.path
#DONE show's output is now ordered by names
#DONE task output is now ordered by names
#DONE task: New option --long, task shows now only finals
#DONE task now accepts ending '/' in the path
#TODO fow exception when not within a fow. Error message instead
#TODO task should list location and title information
#TODO task soll verwaiste XMPs aufraeumen: task --xmp-cleanup|-x
#TODO renaming with exiv2 rename * -r %Y%m%d-%H%M%S-:basename:
#TODO cd dir and list dir functions: fow cd [--task|--inbox|..] [--final|jpg|...]
#TODO Jump into task dir with fow jump taks and junp to root dir
# http://www.fujix-forum.com/threads/in-camera-raw-processing.62573/ sagt:
# exiftool -Model="X-E2" *.RAF -> Umgeht Weiabgleichsfehler
# exiftool -Make="Fujifilm" DSCF3958.RAF -> dann zieht zwar die
# Objektivkorrektur korrekt, der Weissabgleichfehler kommt aber wieder!


def cmd_rename(_arg_struct):
    """
    Move an rename in files.
    """

    ##0: No param allowed, 1: param optional, 2: param obligatory
    #if not checkArgs(_arg_dict,
    #    {'-t': 0, '--test': 0, '-p': 2, '--path': 2}):
    #    return
    atom_none = dict(name='', short='', args=0)
    atom_force = dict(name='force', short='f', args=0)
    atom_test = dict(name='test', short='t', args=0)
    atom_verbose = dict(name='verbose', short='v', args=0)

    #print('export() _arg_struct=' + str(_arg_struct))
    rules = [
        [dict(atom=atom_none, obligat=True),
         dict(atom=atom_force, obligat=False),
         dict(atom=atom_test, obligat=False),
         dict(atom=atom_verbose, obligat=False)]
        ]

    if not check_params(_arg_struct, rules, 'rename'):
        return

    #Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)

    analysis = plump.rename_analyse(plump.get_path(plump.DIR_00),
        plump.get_path(plump.DIR_01))
    #print('rename() analysis=' + str(analysis))

    # --verbose option
    verbose = 'verbose' in args['names']
    force = 'force' in args['names']

    #rename --test
    if 'test' in args['names']:
        plump.rename_test(analysis, verbose, force)
        return

    #rename
    else:
        plump.rename_do(analysis, verbose, force)


def cmd_export(_arg_struct):
    """
    Copy finals to external destinations.
    """

    ##0: No param allowed, 1: param optional, 2: param obligatory
    #if not checkArgs(_arg_dict,
    #    {'-t': 0, '--test': 0, '-p': 2, '--path': 2}):
    #    return
    atom_path = dict(name='path', short='p', args=2)
    atom_force = dict(name='force', short='f', args=0)
    atom_test = dict(name='test', short='t', args=0)
    atom_none = dict(name='', short='', args=2)

    #print('export() _arg_struct=' + str(_arg_struct))
    rules = [
        [dict(atom=atom_path, obligat=True),
         dict(atom=atom_force, obligat=False),
         dict(atom=atom_test, obligat=False)],

        [dict(atom=atom_none, obligat=True),
         dict(atom=atom_force, obligat=False),
         dict(atom=atom_test, obligat=False)]
        ]

    if not check_params(_arg_struct, rules, 'export'):
        return

    #Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)

    # Get destination
    if 'path' in args['names']:
        dest = args['args'][0]
    else:
        try:
            dest = plump.readConfig()[plump.EXPORT_PREFIX
                + '.' + args['args'][0]]
        except:
            print('Destination value not defined. Create it with ' +
                '"config -s export.' + args['args'][0] + '" first.')
            return

    if dest is None:
        print('Destination not valid. See "help export".')
        return

    if not os.path.exists(dest):
        print('Destination directory not reachable: ' + dest)
        return

    if not task.check_actual():
        return

    src_dir = task.get_actual()['task'] + '/' + plump.DIR_FINAL
    src_path = task.get_path(src_dir)
    files = plump.list_jpg(src_path)

    #[dict(name='image001.jpg', exists='true')]
    analysis = plump.export_analyse(task.get_actual(), dest)
    if 'test' in args['names']:
        plump.export_test(analysis, src_dir, dest)
        return

    #export --force
    if 'force' in args['names']:
        print(str(len(files)) + ' images in ' + task.get_actual()['task']
            + '/' + plump.DIR_FINAL)
        print('Destination: ' + dest)
        plump.export_copy(analysis, src_path, dest)

    #export
    else:
        exists = False
        for item in analysis:
            if item['exists']:
                exists = True
        if exists:
            print('Files would be overwritten! ' +
            'Use --test to list the file(s) ' +
            'or use --force to overwrite the image(s). ')
        else:
            print(str(len(files)) + ' images in ' + task.get_actual()['task']
                + '/' + plump.DIR_FINAL)
            print('Destination: ' + dest)
            plump.export_copy(analysis, src_path, dest)


def cmd_task(_arg_struct):
    """
    Task manipulation.
    """

    #Command needs an existing fow.
    if not plump.is_fow():
        return

    ##0: No param allowed, 1: param optional, 2: param obligatory
    #if not checkArgs(_arg_dict,
    #    {'-t': 0, '--test': 0, '-p': 2, '--path': 2}):
    #    return
    atom_create = dict(name='create', short='c', args=2)
    atom_activate = dict(name='activate', short='a', args=2)
    atom_short = dict(name='short', short='s', args=0)
    atom_long = dict(name='long', short='l', args=0)
    atom_raw_import = dict(name='raw-import', short='r', args=0)
    atom_fill_final = dict(name='fill-final', short='f', args=0)
    atom_test = dict(name='test', short='t', args=0)
    atom_none = dict(name='', short='', args=0)

    #print('_arg_struct=' + str(_arg_struct))
    rules = [
        [dict(atom=atom_none, obligat=True)],

        [dict(atom=atom_create, obligat=True)],

        [dict(atom=atom_activate, obligat=True)],

        [dict(atom=atom_raw_import, obligat=True),
            dict(atom=atom_test, obligat=False)],

        [dict(atom=atom_fill_final, obligat=True),
            dict(atom=atom_test, obligat=False)],

        [dict(atom=atom_short, obligat=True)],

        [dict(atom=atom_long, obligat=True)]
        ]

    if not check_params(_arg_struct, rules, 'task'):
        return

    #Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)
    #print('args=' + str(args))

    #print('Params=' + str(arg_dict))

    #--- Options for the actual task ---#

    #task --short
    #task
    #task --long
    if 'short' in args['names'] or 'long' in args['names'] \
        or len(args['names']) == 0:
        if task.get_actual() is None:
            print('No actual task. ' +
            'Use "task --create <task>" to create one.')
        else:
            print('Actual task is ' + task.get_actual()['task'] + '.')
            if 'short' in args['names']:
                plump.show_task_summary(
                    plump.get_path(plump.DIR_02) + '/'
                    + task.get_actual()['task'])
            elif 'long' in args['names']:
                plump.show_task(
                    plump.get_path(plump.DIR_02) + '/'
                    + task.get_actual()['task'], False)
            else:
                plump.show_task(plump.get_path(plump.DIR_02) + '/'
                    + task.get_actual()['task'], True)
        return

    #task --raw-import
    #task --raw-import --test
    if 'raw-import' in args['names'] or \
        'missing-raws' in args['names']:
        if task.get_actual() is None:
            print('No actual task set, please specify the folder, too: ' +
                '[' + plump.get_path(plump.DIR_02) + '/]<folder>/<task>')
            return

        plump.move_corresponding_raws(
            plump.get_path(plump.DIR_02) + '/'
            + task.get_actual()['task']
            + '/' + plump.DIR_JPG,
            plump.get_path(plump.DIR_01) + '/' + plump.DIR_RAW,
            plump.get_path(plump.DIR_02) + '/' + task.get_actual()['task']
            + '/' + plump.DIR_RAW, 'test' in args['names'])
        return

    #task --fill-final
    #task --fill-final --test
    if 'fill-final' in args['names']:
        if task.get_actual() is None:
            print('No actual task set, please specify the folder, too: ' +
                '[' + plump.get_path(plump.DIR_02) + '/]<folder>/<task>')
            return

        plump.copy_missing_jpgs(
            plump.get_path(plump.DIR_02) + '/' +
            task.get_actual()['task']
                + '/' + plump.DIR_JPG,
            plump.get_path(plump.DIR_02) + '/' +
            task.get_actual()['task']
                + '/' + plump.DIR_FINAL,
            'test' in args['names'])
        return

    #--- Options to change the actual task ---#

    #arg 0 is the path, Path may not end with '/'
    if len(args['args'][0]) > 0 and args['args'][0][-1] == '/':
        args['args'][0] = args['args'][0][0:-1]

    #Extract folder and task name
    if args['args'][0].count('/') > 2:
        print('Path too long, use [[' + plump.DIR_02 + ']/<folder>/]]<task>')
        return

    #Dictionary with all task parts
    path = dict(folder=None, task=None, ft=None, path=None)
    if args['args'][0].count('/') == 2:
        #print(args['args'][0])
        if not args['args'][0].startswith(plump.DIR_02 + '/'):
            print('Invalid path. Try [[' + plump.DIR_02 +
                 '/]<folder>/]]<task>.')
            return
        else:
            parts = args['args'][0].split('/')
            path['folder'] = parts[-2]
            path['task'] = parts[-1]
    elif args['args'][0].count('/') == 1:
        parts = args['args'][0].split('/')
        path['folder'] = parts[-2]
        path['task'] = parts[-1]
    else:
        path['task'] = args['args'][0]

    #If only task is given, take the active folder
    if path['folder'] is None:
        if task.get_actual() is None:
            print('No actual task set, please specify the folder, too: ' +
                '[[' + plump.DIR_02 + '/]<folder>/]]<task>')
            return
        path['folder'] = task.get_actual()['folder']

    #For conveniencly usage
    path['ft'] = path['folder'] + '/' + path['task']
    path['path'] = plump.get_path(plump.DIR_02) + '/' + path['ft']

    #task --create <task>
    if 'create' in args['names']:
        if os.path.exists(path['path']):
            print('task ' + path['ft'] + ' already exists.' +
            ' Choose a different name to create a new task.')
            return

        os.makedirs(path['path'])
        os.mkdir(path['path'] + '/' + plump.DIR_FINAL)
        os.mkdir(path['path'] + '/' + plump.DIR_JPG)
        os.mkdir(path['path'] + '/' + plump.DIR_RAW)
        os.mkdir(path['path'] + '/' + plump.DIR_WORK)
        plump.setConfig(plump.TASK, path['ft'])
        return

    if 'activate' in args['names']:
        #print('path =' + str(path))
        if not os.path.exists(path['path']):
            print('task ' + path['ft'] + ' does not exist.' +
            ' To create a new task use "task --create [<folder>/]<task>"')
            return

        plump.setConfig(plump.TASK, path['ft'])


def cmd_backup(_arg_struct):
    """
    Backup data to external file system. Input is the argument structure.
    """
    ##0: No param allowed, 1: param optional, 2: param obligatory
    #if not checkArgs(_arg_dict,
    #    {'-t': 0, '--test': 0, '-p': 2, '--path': 2}):
    #    return

    atomTest = dict(name='test', short='t', args=0)
    atomPath = dict(name='path', short='p', args=2)
    atomNone = dict(name='', short='', args=0)

    #atomNone must be mandatory for rules with more than one path
    rules = [
                [dict(atom=atomPath, obligat=True),
                 dict(atom=atomTest, obligat=False)],

                [dict(atom=atomNone, obligat=True),
                 dict(atom=atomTest, obligat=False)]
             ]

    if not check_params(_arg_struct, rules, 'backup'):
        return

    #Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)
    #print('args=' + str(args))

    #backup --path <path>
    if 'path' in args['names']:
        path = args['args'][0]
    #backup
    else:
        if not plump.BACKUP_PATH in plump.readConfig() or \
            plump.readConfig()[plump.BACKUP_PATH] == 'None' or \
            plump.readConfig()[plump.BACKUP_PATH] is None:
            print('Backup directory not set. Use "backup <path>" for this ' +
                'call or set backup path with "config backupDir <path>".')
            return
        else:
            path = plump.readConfig()[plump.BACKUP_PATH]

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
        + plump.get_fow_root() + plump.DIR_FOW + ' '
        + plump.get_fow_root() + plump.DIR_00 + ' '
        + plump.get_fow_root() + plump.DIR_01 + ' '
        + plump.get_fow_root() + plump.DIR_02 + ' '
        + path)


def cmd_show(_arg_struct):
    """
    Processing step reporting
    """

    atom_short = dict(name='short', short='s', args=1)
    atom_none = dict(name='', short='', args=1)

    #atomNone must be mandatory for rules with more than one path
    rules = [[dict(atom=atom_none, obligat=True)],
             [dict(atom=atom_short, obligat=False)]]

    if not check_params(_arg_struct, rules, 'show'):
        return

    #Normalize for easy access: -t -> --test etc.
    #args = {names=[<option1>,...], args=[<arg1>,...]}
    args = plump.normalizeArgs(_arg_struct, rules)

    #print(str(args))

    if 'inbox' in args['args']:
        if 'short' in args['names']:
            plump.show_in_summary(plump.get_path(plump.DIR_00))
        else:
            plump.show_in(plump.get_path(plump.DIR_00))
        return

    if 'import' in args['args']:
        if 'short' in args['names']:
            plump.show_in_summary(plump.get_path(plump.DIR_01))
        else:
            plump.show_in(plump.get_path(plump.DIR_01))
        return

    if 'in' in args['args']:
        if 'short' in args['names']:
            print('inbox:')
            plump.show_in_summary(plump.get_path(plump.DIR_00))
            print('import:')
            plump.show_in_summary(plump.get_path(plump.DIR_01))
        else:
            print('inbox:')
            plump.show_in(plump.get_path(plump.DIR_00))
            print('import:')
            plump.show_in(plump.get_path(plump.DIR_01))
        return

    if 'tasks' in args['args']:
        if 'short' in args['names']:
            plump.show_tasks_summary()
        else:
            plump.show_tasks()
        return

    if 'task' in args['args'] or len(args['args']) == 0:
        if task.get_actual() is None:
            print('No actual task. ' +
            'Use "task --create <task>" to create one.')
        else:
            print('Actual task is ' + task.get_actual()['task'] + '.')
            if 'short' in args['names']:
                plump.show_task_summary(plump.get_path(plump.DIR_02) + '/'
                    + task.get_actual()['task'])
            else:
                plump.show_task(plump.get_path(plump.DIR_02) + '/'
                    + task.get_actual()['task'])
        return


def cmd_config(_arg_struct):
    """
    Set or delete a config item
    """

    atom_delete = dict(name='delete', short='d', args=2)
    atom_list = dict(name='list', short='l', args=1)
    atom_none = dict(name='', short='', args=0)
    atom_set = dict(name='set', short='s', args=2)

    #atomNone must be mandatory for rules with more than one path
    rules = [[dict(atom=atom_none, obligat=True)],

             [dict(atom=atom_list, obligat=True)],

             [dict(atom=atom_delete, obligat=True)],

             [dict(atom=atom_set, obligat=True)]]

    if not check_params(_arg_struct, rules, 'config'):
        return

    #Normalize for easy access: -t -> --test etc.
    #args = {names=[<option1>,...], args=[<arg1>,...]}
    args = plump.normalizeArgs(_arg_struct, rules)

    settings = plump.readConfig()

    if 'delete' in args['names']:
        del settings[args['args'][0]]
        #settings[args['args'][0]] = 'None'
        plump.writeConfig(settings)
        return

    if 'list' in args['names'] or len(args['names']) == 0:
        if len(args['args']) == 0:
            items = list(settings.items())
            items.sort()
            for key, value in items:
                print((key + ' = ' + str(value)))
        else:
            print((settings[args['args'][0]]))

    if 'set' in args['names']:
        (key, value) = args['args'][0].split('=')
        settings[key] = value
        plump.writeConfig(settings)


def cmd_init(_arg_struct):
    """
    Initializes the fow. Call this once.
    """

    atomForce = dict(name='force', short='f', args=0)
    atomNone = dict(name='', short='', args=0)

    #Set atomNone as non-obligat, otherwise check will fail
    rules = [[dict(atom=atomNone, obligat=True),
                dict(atom=atomForce, obligat=False)]]

    if not check_params(_arg_struct, rules, 'init'):
        return

    #Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)
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
                plump.BACKUP_PATH: None,
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
        cmd_help(plump.toArgStruct(cmds[1:]))

    elif cmds[0] == 'config':
        cmd_config(plump.toArgStruct(cmds[1:]))

    elif cmds[0] == 'init':
        cmd_init(plump.toArgStruct(cmds[1:]))

    elif cmds[0] == 'backup':
        cmd_backup(plump.toArgStruct(cmds[1:]))

    elif cmds[0] == 'task':
        cmd_task(plump.toArgStruct(cmds[1:]))

    elif cmds[0] == 'show':
        cmd_show(plump.toArgStruct(cmds[1:]))

    elif cmds[0] == 'export':
        cmd_export(plump.toArgStruct(cmds[1:]))

    elif cmds[0] == 'rename':
        cmd_rename(plump.toArgStruct(cmds[1:]))

    else:
        print('Unknown command. Use help to list all commands.')


def showHelp(_arg_struct):
    """
    generate help and show it. For specific command help, there has to be one
    file for each command with name help_<command>.txt. The first line of this
    file must be the abstract of the command.
    """
    atomNone = dict(name='', short='', args=1)

    #For commands with only one path atomNone must be non-obligatory!
    rules = [[dict(atom=atomNone, obligat=True)]]

    if not check_params(_arg_struct, rules, ''):
        return

    #Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)
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


def cmd_help(_arg_struct):
    """
    Show man page. For specific command help, there has to be one
    file for each command with name fow-<command>. The first line of this
    file must be the abstract of the command.
    """
    atomNone = dict(name='', short='', args=1)

    #For commands with only one path atomNone must be non-obligatory!
    rules = [[dict(atom=atomNone, obligat=True)]]

    if not check_params(_arg_struct, rules, ''):
        return

    ##Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)
    #help
    if len(args['args']) == 0:

        #Get all help files in the help dir, stored as man page
        try:
            pattern = re.compile('fow-\w+.1.gz')
            #print('pattern=' + str(pattern))
            #print('dir=' + str(plump.getHelpFileDir()))
            #print('listdir=' + str(os.listdir(plump.getHelpFileDir())))
            names = [f for f in os.listdir(plump.getHelpFileDir())
                        if os.path.isfile(os.path.join(
                        plump.getHelpFileDir(), f))
                        and pattern.match(f)]
            #print('names=' + str(names))
            print(('fow commands:'))
            out = ''
            for f in names:
                with gzip.open(os.path.join(
                    plump.getHelpFileDir(), f), 'rt') as help_file:
                    help_file.readline()
                    help_file.readline()
                    help_file.readline()
                    help_file.readline()
                    #print(help_file.readline())
                    out = help_file.readline().replace('\-', '-')
                    print(out[0:-1])
        except:
            print('Uuups, could not find the help files in directory "' +
                plump.getHelpFileDir()
                + '". Please, check your fow installation. There must be ' +
                'the key HELP_FILE_DIR in the config file with the path ' +
                'to the man dirs, e.g. ')
            print('    HELP_FILE_DIR=/usr/share/man/man1')
            return

    #help <command>
    elif len(args['args']) == 1:
            try:
                #For developing call man page local, without index db
                if plump.readFowConfig('MAN_DIRECT'):
                    os.system('man -l ' + plump.getHelpFileDir() +
                    '/fow-' + args['args'][0] + '.1.gz')
                else:
                    os.system('man ' + 'fow-' + args['args'][0])
            except:
                print(args['args'][0] + ' is unknown. ' +
                'Use help to see all commands.')


