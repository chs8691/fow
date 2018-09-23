# -*- coding: utf-8 -*-
import gzip
import os
import re
import shutil

import export
import load
import plump
import rename
import show
import task
import fow_gps
import config

import xe2hack
from argument_checker import check_params


def cmd_xe2hack(_arg_struct):
    """
    Change exif model for raw files in 01_import
    """

    # #0: No param allowed, 1: param optional, 2: param obligatory
    # if not checkArgs(_arg_dict,
    #    {'-t': 0, '--test': 0, '-p': 2, '--path': 2}):
    #    return
    atom_none = dict(name='', short='', args=0)
    atom_revert = dict(name='revert', short='r', args=0)
    atom_test = dict(name='test', short='t', args=0)

    # print('export() _arg_struct=' + str(_arg_struct))
    rules = [
        [dict(atom=atom_none, obligat=True),
         dict(atom=atom_revert, obligat=False),
         dict(atom=atom_test, obligat=False)]
    ]

    if not check_params(_arg_struct, rules, 'x2ehack'):
        return

    # Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)

    if 'revert' in args['names']:
        from_model = 'X-E2'
        to_model = 'X-E2S'
    else:
        from_model = 'X-E2S'
        to_model = 'X-E2'

    analysis = xe2hack.analyse(plump.get_path(plump.DIR_01),
                               from_model, to_model)
    # print('rename() analysis=' + str(analysis))

    # --test
    if 'test' in args['names']:
        xe2hack.test(analysis)
        return

    # rename
    else:
        xe2hack.do(analysis)


def cmd_gps(_arg_struct):
    """
    Adds geo locations from gps files
    """

    # 0: No param allowed, 1: param optional, 2: param obligatory
    atom_none = dict(name='', short='', args=1)
    atom_path = dict(name='path', short='p', args=2)
    atom_source = dict(name='source', short='s', args=2)
    atom_test = dict(name='test', short='t', args=0)
    atom_map = dict(name='map', short='m', args=0)
    atom_force = dict(name='force', short='f', args=0)
    atom_verbose = dict(name='verbose', short='v', args=0)

    rules = [
        [dict(atom=atom_none, obligat=True),
         dict(atom=atom_force, obligat=False),
         dict(atom=atom_verbose, obligat=False)
         ],
        [dict(atom=atom_source, obligat=True),
         dict(atom=atom_force, obligat=False),
         dict(atom=atom_verbose, obligat=False)
         ],
        [dict(atom=atom_path, obligat=True),
         dict(atom=atom_source, obligat=False),
         dict(atom=atom_force, obligat=False),
         dict(atom=atom_verbose, obligat=False)
         ],
        [dict(atom=atom_none, obligat=True),
         dict(atom=atom_test, obligat=True),
         dict(atom=atom_verbose, obligat=False)
         ],
        [dict(atom=atom_path, obligat=True),
         dict(atom=atom_test, obligat=True),
         dict(atom=atom_verbose, obligat=False)
         ],
        [dict(atom=atom_path, obligat=True),
         dict(atom=atom_map, obligat=True)
         ],
        [dict(atom=atom_none, obligat=True),
         dict(atom=atom_map, obligat=True)
         ],
    ]
    print('_arg_struct=' + str(_arg_struct))

    if not check_params(_arg_struct, rules, 'gps'):
        return

    # Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)

    print("cmp_gps() {}".format(str(args)))
    # get path
    if 'path' in args['names']:
        image_path = args['args'][0]
    # if 'source' in args['names']:
    #     source_path =
    elif len(args['args']) == 1:
        key = 'gps.{}'.format(args['args'][0])
        if config.read_item(key) is None:
            print('Value {0} not configured. Maybe you have to set it first with config -s {0}=yourPath'.format(key))
            return
        else:
            image_path = plump.get_path(config.read_item(key))
    else:
        if task.get_actual() is None:
            print('No active task.')
            return
        else:
            # print('cmd_gps() {}'.format(str(task.get_actual())))
            image_path = '{}/{}'.format(task.get_actual()['path'], plump.DIR_FINAL)

    if not os.path.exists(image_path):
        print("Invalid path '{}'".format(str(image_path)))
        return

    # Now we have a valid, existing absolute path to the images
    # Just show map
    if 'map' in args['names']:
        fow_gps.map(image_path)
        return;

    track_path = config.read_item(plump.GPS_TRACK_PATH)
    if track_path is None:
        print('{0} not set. Define the path to tracks folder with config -s {0}=/your/tracks/path'
              .format(plump.GPS_TRACK_PATH))
        return
    elif not os.path.exists(track_path):
        print(("Invalid path to track files: '{0}'. May the directory is temporary not available or you have to" +
               " change it with 'config -s {1}=/your/tracks/path'").format(str(track_path), plump.GPS_TRACK_PATH))
        return

    # Now we have both valid path
    # print("cmp_gps() images={0}, tracks={1}".format(str(image_path), str(track_path)))

    analysis = fow_gps.analyse(track_path, image_path)
    # print('cmd_gps() analysis=' + str(analysis))

    # gps --verbose
    if 'verbose' in args['names']:
        verbose = True
    else:
        verbose = False

    # gps --test
    if 'test' in args['names']:
        fow_gps.test(analysis, verbose)
        return

    # gps
    else:
        fow_gps.do(analysis, True, verbose)


def cmd_rename(_arg_struct):
    """
    Move an rename in files.
    """

    # 0: No param allowed, 1: param optional, 2: param obligatory
    # if not checkArgs(_arg_dict,
    #    {'-t': 0, '--test': 0, '-p': 2, '--path': 2}):
    #    return
    atom_none = dict(name='', short='', args=0)
    atom_force = dict(name='force', short='f', args=0)
    atom_test = dict(name='test', short='t', args=0)
    atom_verbose = dict(name='verbose', short='v', args=0)

    # print('export() _arg_struct=' + str(_arg_struct))
    rules = [
        [dict(atom=atom_none, obligat=True),
         dict(atom=atom_force, obligat=False),
         dict(atom=atom_test, obligat=False),
         dict(atom=atom_verbose, obligat=False)]
    ]

    if not check_params(_arg_struct, rules, 'rename'):
        return

    # Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)

    analysis = rename.analyse(plump.get_path(plump.DIR_00),
                              plump.get_path(plump.DIR_01))
    # print('rename() analysis=' + str(analysis))

    # --verbose option
    verbose = 'verbose' in args['names']
    force = 'force' in args['names']

    # rename --test
    if 'test' in args['names']:
        rename.test(analysis, verbose, force)
        return

    # rename
    else:
        rename.do(analysis, verbose, force)


def cmd_load(_arg_struct):
    """
    Copy or moves files from external destinations.
    """

    # 0: No param allowed, 1: param optional, 2: param obligatory
    # if not checkArgs(_arg_dict,
    #    {'-t': 0, '--test': 0, '-p': 2, '--path': 2}):
    #    return
    atom_path = dict(name='path', short='p', args=2)
    atom_move = dict(name='move', short='m', args=0)
    atom_force = dict(name='force', short='f', args=0)
    atom_verbose = dict(name='verbose', short='v', args=0)
    atom_test = dict(name='test', short='t', args=0)
    atom_none = dict(name='', short='', args=2)

    # print('export() _arg_struct=' + str(_arg_struct))
    rules = [
        [dict(atom=atom_path, obligat=True),
         dict(atom=atom_force, obligat=False),
         dict(atom=atom_verbose, obligat=False),
         dict(atom=atom_move, obligat=False),
         dict(atom=atom_test, obligat=False)],

        [dict(atom=atom_none, obligat=True),
         dict(atom=atom_force, obligat=False),
         dict(atom=atom_verbose, obligat=False),
         dict(atom=atom_move, obligat=False),
         dict(atom=atom_test, obligat=False)]
    ]

    if not check_params(_arg_struct, rules, 'load'):
        return

    # Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)

    # Get srcination
    if 'path' in args['names']:
        src = args['args'][0]
    else:
        try:
            src = config.read_pickle()['{0}.{1}'.format(
                plump.LOAD_PREFIX, args['args'][0])]
        except:
            print('Source value not defined. Create it with ' +
                  '"config -s load.' + args['args'][0] + '=<sourceDir>" first.')
            return

    if src is None:
        print('Source not valid. See "help load".')
        return

    if not os.path.exists(src):
        print('Source directory not reachable: ' + src)
        return

    if not task.check_actual():
        return

    dest = '{0}{1}'.format(plump.get_fow_root(), plump.DIR_00)

    # Get additional options
    options = dict(verbose='verbose' in args['names'],
                   move='move' in args['names'],
                   force='force' in args['names'])

    # [dict(name='image001.jpg', exists='true')]
    analysis = load.analyse(src, dest)
    if 'test' in args['names']:
        load.test(analysis, src, dest, options)
        return

    # load
    else:
        load.do(analysis, src, dest, options)

    return


def cmd_export(_arg_struct):
    """
    Copy finals to external destinations.
    """
    # 0: No param allowed, 1: param optional, 2: param obligatory
    # if not checkArgs(_arg_dict,
    #    {'-t': 0, '--test': 0, '-p': 2, '--path': 2}):
    #    return
    atom_path = dict(name='path', short='p', args=2)
    atom_force = dict(name='force', short='f', args=0)
    atom_test = dict(name='test', short='t', args=0)
    atom_none = dict(name='', short='', args=2)

    # print('export() _arg_struct=' + str(_arg_struct))
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

    # Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)

    # Get destination
    if 'path' in args['names']:
        destination = args['args'][0]
    else:
        try:
            destination = config.read_pickle()[plump.EXPORT_PREFIX
                                        + '.' + args['args'][0]]
        except:
            print('Destination value not defined. Create it with ' +
                  '"config -s export.' + args['args'][0] + '" first.')
            return

    if destination is None:
        print('Destination not valid. See "help export".')
        return

    # Extract task specific subdirectory {1} or {2}, if given
    m = re.compile('(.*)(/{[12]}/?)').match(destination)

    # Direct path
    if m is None:
        if not os.path.exists(destination):
            print('Destination directory not reachable: ' + destination)
            return

    # Task specific path
    else:
        root_dir = m.group(1)
        if os.path.exists(m.group(1)):
            # Resolve subdirectory placeholder: task name
            if destination.endswith(('{1}', '{1}/')):
                destination = root_dir + '/' + task.get_actual()['name']
            # Resolve subdirectory placeholder: folder + task name
            elif destination.endswith(('{2}', '{2}/')):
                destination = root_dir + '/' + task.get_actual()['task']
        else:
            print('Destination root directory not reachable: ' + root_dir)
            return

    print('destination={}'.format(destination))
    if not task.check_actual():
        return

    src_dir = task.get_actual()['task'] + '/' + plump.DIR_FINAL
    src_path = task.get_task_path(src_dir)
    files = plump.list_jpg(src_path)

    # [dict(name='image001.jpg', exists='true')]
    analysis = export.analyse(task.get_actual(), destination)
    if 'test' in args['names']:
        export.test(analysis, src_dir, destination)
        return

    # export --force
    if 'force' in args['names']:
        print(str(len(files)) + ' images in ' + task.get_actual()['task']
              + '/' + plump.DIR_FINAL)
        print('Destination: ' + destination)
        export.copy(analysis, src_path, destination)

    # export
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
            print('Destination: ' + destination)
            export.copy(analysis, src_path, destination)


def cmd_task(_arg_struct):
    """
    Task manipulation.
    """

    # Command needs an existing fow.
    if not plump.is_fow():
        return

    # 0: No param allowed, 1: param optional, 2: param obligatory
    # if not checkArgs(_arg_dict,
    #    {'-t': 0, '--test': 0, '-p': 2, '--path': 2}):
    #    return
    atom_create = dict(name='create', short='c', args=2)
    atom_activate = dict(name='activate', short='a', args=2)
    atom_next = dict(name='next', short='n', args=0)
    atom_previous = dict(name='previous', short='p', args=0)
    atom_short = dict(name='short', short='s', args=0)
    atom_long = dict(name='long', short='l', args=0)
    atom_raw_import = dict(name='raw-import', short='r', args=0)
    atom_fill_final = dict(name='fill-final', short='f', args=0)
    atom_test = dict(name='test', short='t', args=0)
    atom_none = dict(name='', short='', args=0)

    # print('_arg_struct=' + str(_arg_struct))
    rules = [
        [dict(atom=atom_none, obligat=True)],

        [dict(atom=atom_create, obligat=True)],

        [dict(atom=atom_activate, obligat=True)],

        [dict(atom=atom_next, obligat=True)],

        [dict(atom=atom_previous, obligat=True)],

        [dict(atom=atom_raw_import, obligat=True),
         dict(atom=atom_test, obligat=False)],

        [dict(atom=atom_fill_final, obligat=True),
         dict(atom=atom_test, obligat=False)],

        [dict(atom=atom_short, obligat=True)],

        [dict(atom=atom_long, obligat=True)]
    ]

    if not check_params(_arg_struct, rules, 'task'):
        return

    # Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)
    # print('args=' + str(args))

    # print('Params=' + str(arg_dict))

    # --- Options for the actual task ---#

    # task --short
    # task
    # task --long
    if 'short' in args['names'] or 'long' in args['names'] \
            or len(args['names']) == 0:
        if task.get_actual() is None:
            print('No actual task. ' +
                  'Use "task --create <task>" to create one.')
        else:
            if 'short' in args['names']:
                print('Actual task {}. Showing a summary.'.format(task.get_actual()['task']))
                show.task_summary(
                    plump.get_path(plump.DIR_02) + '/'
                    + task.get_actual()['task'])
            elif 'long' in args['names']:
                print('Actual task is {}. Listing all image files.'.format(task.get_actual()['task']))
                show.show_task(
                    plump.get_path(plump.DIR_02) + '/'
                    + task.get_actual()['task'], False)
            else:
                print('Actual task is {}. Listing image files in final.'.format(task.get_actual()['task']))
                show.show_task(plump.get_path(plump.DIR_02) + '/'
                               + task.get_actual()['task'], True)
        return

    # task --raw-import
    # task --raw-import --test
    if 'raw-import' in args['names'] or 'missing-raws' in args['names']:
        if task.get_actual() is None:
            print('No actual task set, please specify the folder, too: ' +
                  '[' + plump.get_path(plump.DIR_02) + '/]<folder>/<task>')
            return

        task.move_corresponding_raws(
            plump.get_path(plump.DIR_02) + '/'
            + task.get_actual()['task']
            + '/' + plump.DIR_JPG,
            plump.get_path(plump.DIR_01) + '/' + plump.DIR_RAW,
            plump.get_path(plump.DIR_02) + '/' + task.get_actual()['task']
            + '/' + plump.DIR_RAW, 'test' in args['names'])
        return

    # task --fill-final
    # task --fill-final --test
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

    # task --next
    # task --previous
    if 'next' in args['names'] or 'previous' in args['names']:
        if 'previous' in args['names']:
            offset = -1
        else:
            offset = 1
        old_triple = task.get_task_triple(offset)
        if old_triple is None:
            print('No actual task found.')
            return

        if old_triple['p_task'] is None:
            print('Seems to be only one task. Switching not possible.')
            return

        config.set_item(plump.TASK,
                        '{0}/{1}'.format(old_triple['a_task']['subdir'],
                                         old_triple['a_task']['task']))

        new_triple = task.get_task_triple(0)

        print('   {0}/{1}'.format(str(new_triple['p_task']['subdir']),
                                  str(new_triple['p_task']['task'])))
        print('*  {0}/{1}'.format(str(new_triple['a_task']['subdir']),
                                  str(new_triple['a_task']['task'])))
        print('   {0}/{1}'.format(str(new_triple['n_task']['subdir']),
                                  str(new_triple['n_task']['task'])))
        return

    # --- Options to change the actual task ---#

    # arg 0 is the path, Path may not end with '/'
    if len(args['args'][0]) > 0 and args['args'][0][-1] == '/':
        args['args'][0] = args['args'][0][0:-1]

    # Extract folder and task name
    if args['args'][0].count('/') > 2:
        print('Path too long, use [[' + plump.DIR_02 + ']/<folder>/]]<task>')
        return

    # Dictionary with all task parts
    path = dict(folder=None, task=None, ft=None, path=None)
    if args['args'][0].count('/') == 2:
        # print(args['args'][0])
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

    # If only task is given, take the active folder
    if path['folder'] is None:
        if task.get_actual() is None:
            print('No actual task set, please specify the folder, too: ' +
                  '[[' + plump.DIR_02 + '/]<folder>/]]<task>')
            return
        path['folder'] = task.get_actual()['folder']

    # For conveniencly usage
    path['ft'] = path['folder'] + '/' + path['task']
    path['path'] = plump.get_path(plump.DIR_02) + '/' + path['ft']

    # task --create <task>
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
        os.mkdir(path['path'] + '/' + plump.DIR_VIDEO)
        config.set_item(plump.TASK, path['ft'])
        return

    if 'activate' in args['names']:
        # print('path =' + str(path))
        if not os.path.exists(path['path']):
            print('task ' + path['ft'] + ' does not exist.' +
                  ' To create a new task use "task --create [<folder>/]<task>"')
            return

        config.set_item(plump.TASK, path['ft'])


def cmd_backup(_arg_struct):
    """
    Backup data to external file system. Input is the argument structure.
    """
    # 0: No param allowed, 1: param optional, 2: param obligatory
    # if not checkArgs(_arg_dict,
    #    {'-t': 0, '--test': 0, '-p': 2, '--path': 2}):
    #    return

    atom_test = dict(name='test', short='t', args=0)
    atom_path = dict(name='path', short='p', args=2)
    atom_none = dict(name='', short='', args=0)

    # atomNone must be mandatory for rules with more than one path
    rules = [
        [dict(atom=atom_path, obligat=True),
         dict(atom=atom_test, obligat=False)],

        [dict(atom=atom_none, obligat=True),
         dict(atom=atom_test, obligat=False)]
    ]

    if not check_params(_arg_struct, rules, 'backup'):
        return

    # Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)
    # print('args=' + str(args))

    # backup --path <path>
    if 'path' in args['names']:
        path = args['args'][0]
    # backup
    else:
        if plump.BACKUP_PATH not in config.read_pickle() or \
                        config.read_pickle()[plump.BACKUP_PATH] == 'None' or \
                        config.read_pickle()[plump.BACKUP_PATH] is None:
            print('Backup directory not set. Use "backup <path>" for this ' +
                  'call or set backup path with "config backupDir <path>".')
            return
        else:
            path = config.read_pickle()[plump.BACKUP_PATH]

    # backup --test
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

    # atomNone must be mandatory for rules with more than one path
    rules = [[dict(atom=atom_none, obligat=True)],
             [dict(atom=atom_short, obligat=False)]]

    if not check_params(_arg_struct, rules, 'show'):
        return

    # Normalize for easy access: -t -> --test etc.
    # args = {names=[<option1>,...], args=[<arg1>,...]}
    args = plump.normalizeArgs(_arg_struct, rules)

    # print(str(args))

    if 'inbox' in args['args']:
        if 'short' in args['names']:
            show.in_summary(plump.get_path(plump.DIR_00))
        else:
            show.show_in(plump.get_path(plump.DIR_00))
        return

    if 'import' in args['args']:
        if 'short' in args['names']:
            show.in_summary(plump.get_path(plump.DIR_01))
        else:
            show.show_in(plump.get_path(plump.DIR_01))
        return

    if 'in' in args['args']:
        if 'short' in args['names']:
            print('inbox:')
            show.in_summary(plump.get_path(plump.DIR_00))
            print('import:')
            show.in_summary(plump.get_path(plump.DIR_01))
        else:
            print('inbox:')
            show.show_in(plump.get_path(plump.DIR_00))
            print('import:')
            show.show_in(plump.get_path(plump.DIR_01))
        return

    if 'tasks' in args['args']:
        if 'short' in args['names']:
            show.tasks_summary()
        else:
            show.tasks()
        return

    if 'task' in args['args'] or len(args['args']) == 0:
        if task.get_actual() is None:
            print('No actual task. ' +
                  'Use "task --create <task>" to create one.')
        else:
            print('Actual task is ' + task.get_actual()['task'] + '.')
            if 'short' in args['names']:
                show.task_summary(plump.get_path(plump.DIR_02) + '/'
                                  + task.get_actual()['task'])
            else:
                show.show_task(plump.get_path(plump.DIR_02) + '/'
                               + task.get_actual()['task'], False)
        return


def cmd_config(_arg_struct):
    """
    Set or delete a config item
    """

    atom_delete = dict(name='delete', short='d', args=2)
    atom_list = dict(name='list', short='l', args=1)
    atom_none = dict(name='', short='', args=0)
    atom_set = dict(name='set', short='s', args=2)

    # atomNone must be mandatory for rules with more than one path
    rules = [[dict(atom=atom_none, obligat=True)],

             [dict(atom=atom_list, obligat=True)],

             [dict(atom=atom_delete, obligat=True)],

             [dict(atom=atom_set, obligat=True)]]

    if not check_params(_arg_struct, rules, 'config'):
        return

    # Normalize for easy access: -t -> --test etc.
    # args = {names=[<option1>,...], args=[<arg1>,...]}
    args = plump.normalizeArgs(_arg_struct, rules)

    settings = config.read_pickle()

    if 'delete' in args['names']:
        del settings[args['args'][0]]
        # settings[args['args'][0]] = 'None'
        config.create_pickle(settings)
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
        config.create_pickle(settings)


def cmd_init(_arg_struct):
    """
    Initializes the fow. Call this once.
    """

    atom_force = dict(name='force', short='f', args=0)
    atom_none = dict(name='', short='', args=0)

    # Set atomNone as non-obligat, otherwise check will fail
    rules = [[dict(atom=atom_none, obligat=True),
              dict(atom=atom_force, obligat=False)]]

    if not check_params(_arg_struct, rules, 'init'):
        return

    # Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)
    # print('args=' + str(args))

    if not 'force' in args['names']:
        for my_dir in plump.getAllFowDirs().values():
            if plump.exist_dir(my_dir):
                print('"' + my_dir + '" already exists. ' + 'Use -f option to ' +
                      'force deleting all existings fow-directories.')
                return

    for my_dir in plump.getAllFowDirs().values():
        if plump.exist_dir(my_dir):
            shutil.rmtree(my_dir)

    os.mkdir(plump.DIR_FOW)
    settings = dict()
    config.create_pickle(settings)

    os.mkdir(plump.DIR_00)
    os.mkdir(plump.DIR_00 + '/' + plump.DIR_JPG)
    os.mkdir(plump.DIR_00 + '/' + plump.DIR_RAW)
    os.mkdir(plump.DIR_00 + '/' + plump.DIR_VIDEO)

    os.mkdir(plump.DIR_01)
    os.mkdir(plump.DIR_01 + '/' + plump.DIR_JPG)
    os.mkdir(plump.DIR_01 + '/' + plump.DIR_RAW)
    os.mkdir(plump.DIR_01 + '/' + plump.DIR_VIDEO)

    os.mkdir(plump.DIR_02)

    # Define all settings and initialize them
    config.create_pickle({plump.GPS_TRACK_PATH: None,
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

    # print('args=' + str(args))
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

    elif cmds[0] == 'load':
        cmd_load(plump.toArgStruct(cmds[1:]))

    elif cmds[0] == 'rename':
        cmd_rename(plump.toArgStruct(cmds[1:]))

    elif cmds[0] == 'xe2hack':
        cmd_xe2hack(plump.toArgStruct(cmds[1:]))

    elif cmds[0] == 'gps':
        cmd_gps(plump.toArgStruct(cmds[1:]))

        # elif cmds[0] == 'cd':
        # cmd_cd(plump.toArgStruct(cmds[1:]))

    else:
        print('Unknown command. Use help to list all commands.')


def show_help(_arg_struct):
    """
    generate help and show it. For specific command help, there has to be one
    file for each command with name help_<command>.txt. The first line of this
    file must be the abstract of the command.
    """
    atomNone = dict(name='', short='', args=1)

    # For commands with only one path atomNone must be non-obligatory!
    rules = [[dict(atom=atomNone, obligat=True)]]

    if not check_params(_arg_struct, rules, ''):
        return

    # Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)
    # help
    if len(args['args']) == 0:
        # Get all help files in the help dir

        try:
            pattern = re.compile('help_\w+.txt')
            names = [f for f in os.listdir(config.get_help_file_dir())
                     if os.path.isfile(os.path.join(
                    config.get_help_file_dir(), f))
                     and pattern.match(f)]
            print('fow commands:')
            out = ''
            for f in names:
                with open(os.path.join(
                        config.get_help_file_dir(), f)) as help_file:
                    out += help_file.readline()
                    # print(help_file.readline(), end='')
            print(out[0:-1])
        except:
            print('Uuups, could not find the help files in directory "' +
                  config.get_help_file_dir()
                  + '". Please, check your fow installation.')
            return

    # help <command>
    elif len(args['args']) == 1:
        try:
            with open(os.path.join(config.get_help_file_dir(),
                                   'help_' + args['args'][0] + '.txt'), 'r') as data:
                out = ''
                for each_line in data:
                    out += each_line
                    # print(each_line, end='')
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

    # For commands with only one path atomNone must be non-obligatory!
    rules = [[dict(atom=atomNone, obligat=True)]]

    if not check_params(_arg_struct, rules, ''):
        return

    ##Normalize for easy access: -t -> --test etc.
    args = plump.normalizeArgs(_arg_struct, rules)
    # help
    if len(args['args']) == 0:

        # Get all help files in the help dir, stored as man page
        try:
            pattern = re.compile('fow-\w+.1.gz')
            # print('pattern=' + str(pattern))
            # print('dir=' + str(plump.getHelpFileDir()))
            # print('listdir=' + str(os.listdir(plump.getHelpFileDir())))
            names = [f for f in os.listdir(config.get_help_file_dir())
                     if os.path.isfile(os.path.join(
                    config.get_help_file_dir(), f))
                     and pattern.match(f)]
            names.sort()
            # print('names=' + str(names))
            print(('fow commands:'))
            out = ''
            for f in names:
                with gzip.open(os.path.join(
                        config.get_help_file_dir(), f), 'rt') as help_file:
                    help_file.readline()
                    help_file.readline()
                    help_file.readline()
                    help_file.readline()
                    # print(help_file.readline())
                    out = help_file.readline().replace('\-', '-')
                    print(out[0:-1])
        except:
            print('Uuups, could not find the help files in directory "' +
                  config.get_help_file_dir()
                  + '". Please, check your fow installation. There must be ' +
                  'the key HELP_FILE_DIR in the config file with the path ' +
                  'to the man dirs, e.g. ')
            print('    HELP_FILE_DIR=/usr/share/man/man1')
            return

    # help <command>
    elif len(args['args']) == 1:
        try:
            # For developing call man page local, without index db
            if config.read_installation_item('MAN_DIRECT'):
                os.system('man -l ' + config.get_help_file_dir() +
                          '/fow-' + args['args'][0] + '.1.gz')
            else:
                os.system('man ' + 'fow-' + args['args'][0])
        except:
            print(args['args'][0] + ' is unknown. ' +
                  'Use help to see all commands.')
