# -*- coding: utf-8 -*-
import gzip
import os
import re
import shutil

import argument_checker
import export
import load
import plump
import rename
import show
import task
import fow_gps
import config

from plump import NONE_PARAM, MANDATORY_PARAM, OPTIONAL_PARAM

import xe2hack
from argument_checker import check_options, get_arg_by_name



def cmd_xe2hack(options_matrix):
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

    # print('export() options_matrix=' + str(options_matrix))
    rules = [
        [dict(atom=atom_none, obligat=True),
         dict(atom=atom_revert, obligat=False),
         dict(atom=atom_test, obligat=False)]
    ]

    # Normalize for easy access: -t -> --test etc.
    options = argument_checker.normalize_option_matrix(options_matrix, rules)

    if not check_options(options, rules, 'x2ehack'):
        return

    if 'revert' in options['names']:
        from_model = 'X-E2'
        to_model = 'X-E2S'
    else:
        from_model = 'X-E2S'
        to_model = 'X-E2'

    analysis = xe2hack.analyse(plump.get_path(plump.DIR_01),
                               from_model, to_model)
    # print('rename() analysis=' + str(analysis))

    # --test
    if 'test' in options['names']:
        xe2hack.test(analysis)
        return

    # rename
    else:
        xe2hack.do(analysis)


def cmd_gps(options_matrix, cmd_list):
    """
    Adds geo locations from gps files
    """

    atom_none = dict(name='', short='', args=NONE_PARAM)
    atom_path = dict(name='path', short='p', args=MANDATORY_PARAM)
    atom_source = dict(name='source', short='s', args=MANDATORY_PARAM)
    atom_test = dict(name='test', short='t', args=NONE_PARAM)
    atom_map = dict(name='map', short='m', args=NONE_PARAM)
    atom_force = dict(name='force', short='f', args=NONE_PARAM)
    atom_verbose = dict(name='verbose', short='v', args=NONE_PARAM)

    args = argument_checker.normalize_commands(cmd_list, [atom_none, atom_path, atom_source, atom_test, atom_map,
                                                          atom_force, atom_verbose])

    # Restrictions for rule building:
    # - atom_none should only used as obligatory.
    # - if atom_none has an optional argument, no other rule item may have an option argument
    rules = [
        [
            dict(atom=atom_none, obligat=True),
            dict(atom=atom_source, obligat=False),
            dict(atom=atom_test, obligat=False),
            dict(atom=atom_verbose, obligat=False),
            dict(atom=atom_force, obligat=False)
        ],
        [
            dict(atom=atom_path, obligat=True),
            dict(atom=atom_source, obligat=False),
            dict(atom=atom_test, obligat=False),
            dict(atom=atom_verbose, obligat=False),
            dict(atom=atom_force, obligat=False)
        ],
        [
            dict(atom=atom_map, obligat=True),
            dict(atom=atom_path, obligat=False)
         ]
    ]

    ret = argument_checker.analyze_rules(args, rules)
    # print('cmd_gps() ret=' + str(ret))
    if ret['message'] is not None:
        print(ret['message'])
        return

    # print('cmd_gps() options_matrix=' + str(options_matrix))

    # Normalize for easy access: -t -> --test etc.
    # options = argument_checker.normalize_option_matrix(options_matrix, rules)
    # print("cmd_gps() args={}".format(str(options)))

    # if not check_options(options, rules, 'gps'):
    #     return

    # print("cmp_gps() {}".format(str(options)))
    # Possible arguments, None, if not given

    # arg validation
    # image path as destination
    # image path as path argument
    # if 'path' in options['names']:
    if 'path' in ret['options']:
        if not os.path.exists(plump.get_path(ret['options'][''])):
            print((("'{0}' is not an existing sub dir within this fow. " +
                    "Maybe the directory is temporary not available or you have to " +
                    "write the correct path."))
                  .format(str(ret['options'][''])))
            return
        # Validated absolute path to the images
        image_path = plump.get_path(ret['options'][''])

    elif ret['options'][''] is not None:
        key = 'gps.{}'.format(ret['options'][''])
        if config.read_item(key) is None:
            print(
                "Value {0} not configured. Maybe you have to set it first with config -s '{0}=fow-subdir-to-images'".format(key))
            return
        if not os.path.exists(plump.get_path(config.read_item(key))):
            print((("Destination points to a non existing sub dir: '{0}'. " +
                    "Maybe the directory is temporary not available or you have to" +
                    " change the destination with 'config -s {1}=fow-subdir-to-images'"))
                  .format(str(config.read_item(key)), key))
            return
        # Validated absolute path to the images
        image_path = plump.get_path(config.read_item(key))

    # image path is the actual final
    else:
        if task.get_actual() is None:
            print('No active task.')
            return
        elif not os.path.exists(task.get_actual()['path']):
            print("Actual task '{0}' is not an existing sub dir within this fow."
                  .format(str(task.get_actual()['path'])))
            return
        else:
            image_path = '{}/{}'.format(task.get_actual()['path'], plump.DIR_FINAL)

    # Now we have a valid, existing absolute path to the images
    # Just show map
    if 'map' in ret['options']:
        fow_gps.map(image_path)
        return

    # track path as source argument
    if 'source' in ret['options']:
        if not os.path.exists(ret['options']['source']):
            print("'{0}' is not an existing, accessible directory. "
                  .format(str(ret['options']['source'])))
            return
        # Validated absolute path to the images
        track_path = ret['options']['source']

    else:
        if config.read_item(plump.GPS_TRACK_PATH) is None:
            print('{0} not set. Define the path to tracks folder with config -s {0}=/your/tracks/path'
                  .format(plump.GPS_TRACK_PATH))
            return
        elif not os.path.exists(config.read_item(plump.GPS_TRACK_PATH)):
            print(("Invalid path to track files: '{0}'. May the directory is temporary not available or you have to" +
                   " change it with 'config -s {1}=/your/tracks/path'")
                  .format(str(config.read_item(plump.GPS_TRACK_PATH)), plump.GPS_TRACK_PATH))
            return
        # Validated absolute path to the images
        track_path = config.read_item(plump.GPS_TRACK_PATH)

    analysis = fow_gps.analyse(track_path, image_path)
    # print('cmd_gps() analysis=' + str(analysis))

    # gps --verbose
    if 'verbose' in ret['options']:
        verbose = True
    else:
        verbose = False

    # gps --test
    if 'test' in ret['options']:
        fow_gps.test(analysis, verbose)
        return

    # gps
    else:
        fow_gps.do(analysis, True, verbose)


def cmd_rename(options_matrix):
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

    # print('export() options_matrix=' + str(options_matrix))
    rules = [
        [dict(atom=atom_none, obligat=True),
         dict(atom=atom_force, obligat=False),
         dict(atom=atom_test, obligat=False),
         dict(atom=atom_verbose, obligat=False)]
    ]

    # Normalize for easy access: -t -> --test etc.
    options = argument_checker.normalize_option_matrix(options_matrix, rules)

    if not check_options(options, rules, 'rename'):
        return

    analysis = rename.analyse(plump.get_path(plump.DIR_00),
                              plump.get_path(plump.DIR_01))
    # print('rename() analysis=' + str(analysis))

    # --verbose option
    verbose = 'verbose' in options['names']
    force = 'force' in options['names']

    # rename --test
    if 'test' in options['names']:
        rename.test(analysis, verbose, force)
        return

    # rename
    else:
        rename.do(analysis, verbose, force)


def cmd_load(options_matrix):
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

    # print('export() options_matrix=' + str(options_matrix))
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

    # Normalize for easy access: -t -> --test etc.
    options = argument_checker.normalize_option_matrix(options_matrix, rules)

    if not check_options(options, rules, 'load'):
        return

    # Get source
    if 'path' in options['names']:
        src = get_arg_by_name(options, 'path')
    else:
        try:
            key = '{0}.{1}'.format(plump.LOAD_PREFIX, get_arg_by_name(options, ''))
            if key in config.read_pickle():
                src = config.read_pickle()['{0}.{1}'.format(
                    plump.LOAD_PREFIX, get_arg_by_name(options, ''))]
            else:
                print("'{0}' not found. Create it with fow config -s='{0}=yourValue' first.".format(key))
                return
        except TypeError:
            print("Now fow configuration found in the actual directory. Create a fow with 'fow init' first. ")
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
    processing_flags = dict(verbose='verbose' in options['names'],
                            move='move' in options['names'],
                            force='force' in options['names'])

    print("cmd_load() processing_flags={}".format(processing_flags))

    # [dict(name='image001.jpg', exists='true')]
    analysis = load.analyse(src, dest)
    if 'test' in options['names']:
        load.test(analysis, src, dest, processing_flags)
        return

    # load
    else:
        load.do(analysis, src, dest, processing_flags)

    return


def cmd_export(options_matrix):
    """
    Copy finals to external destinations.
    """
    # 0: No param allowed, 1: param optional, 2: param obligatory
    # if not checkArgs(_arg_dict,
    #    {'-t': 0, '--test': 0, '-p': 2, '--path': 2}):
    #    return
    atom_path = dict(name='path', short='p', args=0)
    atom_force = dict(name='force', short='f', args=0)
    atom_test = dict(name='test', short='t', args=0)
    atom_param = dict(name='', short='', args=2)
    atom_none = dict(name='', short='', args=2)

    # print('export() options_matrix=' + str(options_matrix))
    rules = [
        [dict(atom=atom_path, obligat=True),
         dict(atom=atom_param, obligat=True),
         dict(atom=atom_force, obligat=False),
         dict(atom=atom_test, obligat=False)],

        [dict(atom=atom_none, obligat=True),
         dict(atom=atom_force, obligat=False),
         dict(atom=atom_test, obligat=False)]
    ]

    # Normalize for easy access: -t -> --test etc.
    options = argument_checker.normalize_option_matrix(options_matrix, rules)

    if not check_options(options_matrix, rules, 'export'):
        return

    # Get destination
    if 'path' in options['names']:
        destination = get_arg_by_name(options, '')
    else:
        try:
            destination = config.read_pickle()[plump.EXPORT_PREFIX + '.' + get_arg_by_name(options, '')]
        except:
            print("Destination value not defined. Create it with config -s='export.{}' first."
                  .format(get_arg_by_name(options, '')))
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
    if 'test' in options['names']:
        export.test(analysis, src_dir, destination)
        return

    # export --force
    if 'force' in options['names']:
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


def cmd_task(options_matrix):
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
    atom_create = dict(name='create', short='c', args=0)
    atom_activate = dict(name='activate', short='a', args=0)
    atom_next = dict(name='next', short='n', args=0)
    atom_previous = dict(name='previous', short='p', args=0)
    atom_short = dict(name='short', short='s', args=0)
    atom_long = dict(name='long', short='l', args=0)
    atom_raw_import = dict(name='raw-import', short='r', args=0)
    atom_fill_final = dict(name='fill-final', short='f', args=0)
    atom_test = dict(name='test', short='t', args=0)
    atom_none = dict(name='', short='', args=0)
    atom_param = dict(name='', short='', args=2)

    # print('options_matrix=' + str(options_matrix))
    rules = [
        [dict(atom=atom_create, obligat=True),
         dict(atom=atom_param, obligat=True)],

        [dict(atom=atom_activate, obligat=True),
         dict(atom=atom_param, obligat=True)],

        [dict(atom=atom_none, obligat=True),
         dict(atom=atom_short, obligat=False)],

        [dict(atom=atom_none, obligat=True),
         dict(atom=atom_long, obligat=False)],

        [dict(atom=atom_next, obligat=True)],

        [dict(atom=atom_previous, obligat=True)],

        [dict(atom=atom_raw_import, obligat=True),
         dict(atom=atom_test, obligat=False)],

        [dict(atom=atom_fill_final, obligat=True),
         dict(atom=atom_test, obligat=False)]
    ]

    # Normalize for easy access: -t -> --test etc.
    options = argument_checker.normalize_option_matrix(options_matrix, rules)
    # print('options=' + str(options))

    if not check_options(options, rules, 'task'):
        return

    # --- Options to change the actual task (activate or create)---#
    if 'create' in options['names'] or 'activate' in options['names']:
        # print("cmd_task() processing change options")
        # print("cmd_task() options={}".format(str(options)))

        # arg for option '' is the path, Path may not end with '/'
        # if len(options['args'][0]) > 0 and options['args'][0][-1] == '/':
        #
        path_arg = get_arg_by_name(options, '')
        # if 'activate' in options['names']:
        #     path_arg = get_arg_by_name(options, 'activate')
        # elif 'create' in options['names']:
        #     path_arg = get_arg_by_name(options, 'create')
        # else:
        #     print("Option 'activate' or 'create' expected.")
        #     return

        # print("cmd_task() path_arg={}".format(str(path_arg)))

        if path_arg is not None and len(path_arg) > 0 and path_arg[-1] == '/':
            path_arg = path_arg[0:-1]

        # Extract folder and task name
        if path_arg.count('/') > 2:
            print('Path too long, use [[' + plump.DIR_02 + ']/<folder>/]]<task>')
            return

        # print("cmd_task() path_arg={}".format(str(path_arg)))

        # Dictionary with all task parts
        path = dict(folder=None, task=None, ft=None, path=None)
        if path_arg.count('/') == 2:
            # print(args['args'][0])
            if not path_arg.startswith(plump.DIR_02 + '/'):
                print('Invalid path. Try [[' + plump.DIR_02 +
                      '/]<folder>/]]<task>.')
                return
            else:
                parts = path_arg.split('/')
                path['folder'] = parts[-2]
                path['task'] = parts[-1]

        elif path_arg.count('/') == 1:
            parts = path_arg.split('/')
            path['folder'] = parts[-2]
            path['task'] = parts[-1]

        else:
            path['task'] = path_arg

        # If only task is given, take the active folder
        if path['folder'] is None:
            if task.get_actual() is None:
                print('No actual task set, please specify the folder, too: ' +
                      '[[' + plump.DIR_02 + '/]<folder>/]]<task>')
                return
            path['folder'] = task.get_actual()['folder']

        # For convenience usage
        path['ft'] = path['folder'] + '/' + path['task']
        path['path'] = plump.get_path(plump.DIR_02) + '/' + path['ft']

        # task --create <task>
        if 'create' in options['names']:
            if os.path.exists(path['path']):
                print('task ' + str(path['ft']) + ' already exists.' +
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

        if 'activate' in options['names']:
            # print('path =' + str(path))
            if not os.path.exists(path['path']):
                print('task ' + str(path['ft']) + ' does not exist.' +
                      ' To create a new task use "task --create [<folder>/]<task>"')
                return

            config.set_item(plump.TASK, path['ft'])
            return

    # --- Options for the actual task ---#

    # task --short
    # task
    # task --long
    if 'short' in options['names'] or 'long' in options['names'] or '' in options['names']:
        if task.get_actual() is None:
            print('No actual task. ' +
                  'Use "task --create <task>" to create one.')
        else:
            if 'short' in options['names']:
                print('Actual task {}. Showing a summary.'.format(task.get_actual()['task']))
                show.task_summary(
                    plump.get_path(plump.DIR_02) + '/'
                    + task.get_actual()['task'])
            elif 'long' in options['names']:
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
    if 'raw-import' in options['names'] or 'missing-raws' in options['names']:
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
            + '/' + plump.DIR_RAW, 'test' in options['names'])
        return

    # task --fill-final
    # task --fill-final --test
    if 'fill-final' in options['names']:
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
            'test' in options['names'])
        return

    # task --next
    # task --previous
    if 'next' in options['names'] or 'previous' in options['names']:
        if 'previous' in options['names']:
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


def cmd_backup(option_matrix):
    """
    Backup data to external file system. Input is the argument structure.
    """
    # 0: No param allowed, 1: param optional, 2: param obligatory
    # if not checkArgs(_arg_dict,
    #    {'-t': 0, '--test': 0, '-p': 2, '--path': 2}):
    #    return

    atom_test = dict(name='test', short='t', args=0)
    atom_path = dict(name='path', short='p', args=0)
    atom_none = dict(name='', short='', args=0)
    atom_param = dict(name='', short='', args=2)

    # atomNone must be mandatory for rules with more than one path
    rules = [
        [dict(atom=atom_path, obligat=True),
         dict(atom=atom_param, obligat=True),
         dict(atom=atom_test, obligat=False)],

        [dict(atom=atom_none, obligat=False),
         dict(atom=atom_test, obligat=False)]
    ]

    # Normalize for easy access: -t -> --test etc.
    options = argument_checker.normalize_option_matrix(option_matrix, rules)

    if not check_options(option_matrix, rules, 'backup'):
        return

    # backup --path <path>
    if 'path' in options['names']:
        path = get_arg_by_name(options, '')
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
    if 'test' in options['names']:
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


def cmd_show(options_matrix):
    """
    Processing step reporting
    """

    atom_short = dict(name='short', short='s', args=0)
    atom_none = dict(name='', short='', args=1)

    # atomNone must be mandatory for rules with more than one path
    rules = [[dict(atom=atom_none, obligat=True),
             dict(atom=atom_short, obligat=False)]]

    # Normalize for easy access: -t -> --test etc.
    # args = {names=[<option1>,...], args=[<arg1>,...]}
    options = argument_checker.normalize_option_matrix(options_matrix, rules)

    # print("cmd_show{}".format(str(options)))

    if not check_options(options, rules, 'show'):
        return

    if 'inbox' in options['args']:
        if 'short' in options['names']:
            show.in_summary(plump.get_path(plump.DIR_00))
        else:
            show.show_in(plump.get_path(plump.DIR_00))
        return

    if 'import' in options['args']:
        if 'short' in options['names']:
            show.in_summary(plump.get_path(plump.DIR_01))
        else:
            show.show_in(plump.get_path(plump.DIR_01))
        return

    if 'in' in options['args']:
        if 'short' in options['names']:
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

    if 'tasks' in options['args']:
        if 'short' in options['names']:
            show.tasks_summary()
        else:
            show.tasks()
        return

    # if 'task' in args['args'] or len(args['args']) == 0:
    if get_arg_by_name(options, '') in ('task', None):
        if task.get_actual() is None:
            print('No actual task. ' +
                  'Use "task --create <task>" to create one.')
        else:
            print('Actual task is ' + task.get_actual()['task'] + '.')
            if 'short' in options['names']:
                show.task_summary(plump.get_path(plump.DIR_02) + '/'
                                  + task.get_actual()['task'])
            else:
                show.show_task(plump.get_path(plump.DIR_02) + '/'
                               + task.get_actual()['task'], False)
        return


def cmd_config(option_matrix, cmd_list):
    """
    Set or delete a config item
    """

    atom_delete = dict(name='delete', short='d', args=MANDATORY_PARAM)
    atom_list = dict(name='list', short='l', args=OPTIONAL_PARAM)
    atom_none = dict(name='', short='', args=NONE_PARAM)
    atom_set = dict(name='set', short='s', args=MANDATORY_PARAM)

    # atomNone must be mandatory for rules with more than one path
    rules = [
        [dict(atom=atom_none, obligat=True)],

        [dict(atom=atom_list, obligat=True)],

        [dict(atom=atom_delete, obligat=True)],

        [dict(atom=atom_set, obligat=True)]
    ]

    # options = argument_checker.normalize_option_matrix(option_matrix, rules)
    args = argument_checker.normalize_commands(cmd_list, [atom_delete, atom_list, atom_none, atom_set])

    if not argument_checker.find_rule(args, rules):
        return

    return
    if not check_options(options, rules, 'config'):
        return

    settings = config.read_pickle()
    unknown_msg = "Key '{0}' not found."

    if 'delete' in options['names']:
        arg = get_arg_by_name(options, '')
        if arg in settings:
            del settings[arg]
            config.create_pickle(settings)
        else:
            print(unknown_msg.format(arg))

        return

    if 'set' in options['names']:
        arg = get_arg_by_name(options, '')
        (key, value) = arg.split('=')
        settings[key] = value
        config.create_pickle(settings)

        return

    if 'list' in options['names'] or '' in options['names']:
        # if 'list' in options['names']:
        #     arg = get_arg_by_name(options, 'list')
        # else:
        arg = get_arg_by_name(options, '')

        if arg is None:
            items = list(settings.items())
            items.sort()
            for key, value in items:
                print((key + ' = ' + str(value)))
        elif arg in settings:
            print((settings[arg]))
        else:
            print(unknown_msg.format(arg))

        return



def cmd_init(options_matrix):
    """
    Initializes the fow. Call this once.
    """

    atom_force = dict(name='force', short='f', args=0)
    atom_none = dict(name='', short='', args=0)

    # Set atomNone as non-obligat, otherwise check will fail
    rules = [[dict(atom=atom_none, obligat=True),
              dict(atom=atom_force, obligat=False)]]

    # Normalize for easy access: -t -> --test etc.
    options = argument_checker.normalize_option_matrix(options_matrix, rules)
    # print('args=' + str(args))

    if not check_options(options, rules, 'init'):
        return

    if 'force' not in options['names']:
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

    cmds = args[1:]
    # print('fow() cmds=' + str(cmds))

    if cmds[0] == 'help':
        cmd_help(plump.to_arg_struct(cmds[1:]))

    elif cmds[0] == 'config':
        cmd_config(plump.to_arg_struct(cmds[1:]), cmds)

    elif cmds[0] == 'init':
        cmd_init(plump.to_arg_struct(cmds[1:]))

    elif cmds[0] == 'backup':
        cmd_backup(plump.to_arg_struct(cmds[1:]))

    elif cmds[0] == 'task':
        cmd_task(plump.to_arg_struct(cmds[1:]))

    elif cmds[0] == 'show':
        cmd_show(plump.to_arg_struct(cmds[1:]))

    elif cmds[0] == 'export':
        cmd_export(plump.to_arg_struct(cmds[1:]))

    elif cmds[0] == 'load':
        cmd_load(plump.to_arg_struct(cmds[1:]))

    elif cmds[0] == 'rename':
        cmd_rename(plump.to_arg_struct(cmds[1:]))

    elif cmds[0] == 'xe2hack':
        cmd_xe2hack(plump.to_arg_struct(cmds[1:]))

    elif cmds[0] == 'gps':
        cmd_gps(plump.to_arg_struct(cmds[1:]), cmds)

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

    if not check_options(_arg_struct, rules, ''):
        return

    # Normalize for easy access: -t -> --test etc.
    args = argument_checker.normalize_option_matrix(_arg_struct, rules)
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


def cmd_help(options_matrix):
    """
    Show man page. For specific command help, there has to be one
    file for each command with name fow-<command>. The first line of this
    file must be the abstract of the command.
    """
    atom_none = dict(name='', short='', args=1)

    # For commands with only one path atomNone must be non-obligatory!
    rules = [[dict(atom=atom_none, obligat=True)]]

    # Normalize for easy access: -t -> --test etc.
    options = argument_checker.normalize_option_matrix(options_matrix, rules)

    # print("cmd_help() options={}".format(str(options)))

    if not check_options(options, rules, ''):
        return

    # help
    if len(options['args']) == 0:

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
            print('fow commands:')
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
    elif len(options['args']) == 1:
        i = 0
        try:
            # For developing call man page local, without index db
            if config.read_installation_item('MAN_DIRECT'):
                i = os.system('man -l ' + config.get_help_file_dir() +
                              '/fow-' + options['args'][0] + '.1.gz')
            else:
                i = os.system('man ' + 'fow-' + options['args'][0])
        except:
            # Does't work, no exception thrown
            print(options['args'][0] + ' is unknown. ' + 'Use help to see all commands.')
        if i != 0:
            print("See 'fow help'.")

    else:
        print("Too many arguments. See 'fow help'.")
