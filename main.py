# -*- coding: utf-8 -*-
import gzip
import os
import re
import shutil
from datetime import datetime

import export
import fow_exif
import load
import plump
import rename
import show
import task
import fow_gps
import config
import xe2hack

from argument_checker import check_rules
from plump import NONE_PARAM, MANDATORY_PARAM, OPTIONAL_PARAM


def cmd_xe2hack(cmd_list):
    """
    Change exif model for raw files in 01_import
    """

    atom_none = dict(name='', short='', args=NONE_PARAM)
    atom_revert = dict(name='revert', short='r', args=NONE_PARAM)
    atom_test = dict(name='test', short='t', args=NONE_PARAM)

    ret = check_rules(cmd_list,
                      [
                          [
                              dict(atom=atom_none, obligat=True),
                              dict(atom=atom_revert, obligat=False),
                              dict(atom=atom_test, obligat=False)
                          ]
                      ])

    if ret['message'] is not None:
        return

    if 'revert' in ret['options']:
        from_model = 'X-E2'
        to_model = 'X-E2S'
    else:
        from_model = 'X-E2S'
        to_model = 'X-E2'

    analysis = xe2hack.analyse(plump.get_path(plump.DIR_01),
                               from_model, to_model)
    # print('rename() analysis=' + str(analysis))

    # --test
    if 'test' in ret['options']:
        xe2hack.test(analysis)
        return

    # rename
    else:
        xe2hack.do(analysis)


def cmd_gps(cmd_list):
    """
    Adds geo locations from gps files
    """

    atom_none = dict(name='', short='', args=NONE_PARAM)
    atom_path = dict(name='path', short='p', args=MANDATORY_PARAM)
    atom_source = dict(name='source', short='s', args=MANDATORY_PARAM)
    atom_write = dict(name='write', short='w', args=NONE_PARAM)
    atom_test = dict(name='test', short='t', args=NONE_PARAM)
    atom_map = dict(name='map', short='m', args=NONE_PARAM)
    atom_force = dict(name='force', short='f', args=NONE_PARAM)
    atom_verbose = dict(name='verbose', short='v', args=NONE_PARAM)

    ret = check_rules(cmd_list,
                      [
                          [
                              dict(atom=atom_none, obligat=True),
                              dict(atom=atom_source, obligat=False),
                              dict(atom=atom_write, obligat=False),
                              dict(atom=atom_test, obligat=False),
                              dict(atom=atom_write, obligat=False),
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
                      ])

    if ret['message'] is not None:
        return

    # print('cmd_gps() options_matrix=' + str(options_matrix))
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

    # elif ret['options'][''] is not None:
    #     key = 'gps.{}'.format(ret['options'][''])
    #     if config.read_item(key) is None:
    #         print(
    #             "Value {0} not configured. Maybe you have to set it first with
    # config -s '{0}=fow-subdir-to-images'".format(
    #                 key))
    #         return
    #     if not os.path.exists(plump.get_path(config.read_item(key))):
    #         print((("Destination points to a non existing sub dir: '{0}'. " +
    #                 "Maybe the directory is temporary not available or you have to" +
    #                 " change the destination with 'config -s {1}=fow-subdir-to-images'"))
    #               .format(str(config.read_item(key)), key))
    #         return
    #     # Validated absolute path to the images
    #     image_path = plump.get_path(config.read_item(key))

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

    # gps --write
    if 'write' in ret['options']:
        if not os.path.exists(os.path.join(task.get_actual()['path'], plump.DIR_WORK)):
            print("Missing sub directory {}.".format(plump.DIR_WORK))
            return
        else:
            write_path = os.path.join(task.get_actual()['path'], plump.DIR_WORK)
    else:
        write_path = None

    analysis = fow_gps.analyse(track_path, image_path, write_path)
    # print('cmd_gps() analysis=' + str(analysis))

    # gps --verbose
    if 'verbose' in ret['options']:
        verbose = True
    else:
        verbose = False

    # gps --test
    if 'test' in ret['options']:
        fow_gps.test(analysis, verbose, write_path)
        return

    # gps
    else:
        fow_gps.do(analysis, True, verbose, write_path)


def cmd_rename(cmd_list):
    """
    Move an rename in files.
    """

    atom_none = dict(name='', short='', args=NONE_PARAM)
    atom_force = dict(name='force', short='f', args=NONE_PARAM)
    atom_test = dict(name='test', short='t', args=NONE_PARAM)
    atom_verbose = dict(name='verbose', short='v', args=NONE_PARAM)

    ret = check_rules(cmd_list,
                      [
                          [
                              dict(atom=atom_none, obligat=True),
                              dict(atom=atom_force, obligat=False),
                              dict(atom=atom_test, obligat=False),
                              dict(atom=atom_verbose, obligat=False)
                          ]
                      ])

    if ret['message'] is not None:
        return

    analysis = rename.analyse(plump.get_path(plump.DIR_00),
                              plump.get_path(plump.DIR_01))
    # print('rename() analysis=' + str(analysis))

    # --verbose option
    verbose = 'verbose' in ret['options']
    force = 'force' in ret['options']

    # rename --test
    if 'test' in ret['options']:
        rename.test(analysis, verbose, force)
        return

    # rename
    else:
        rename.do(analysis, verbose, force)


def cmd_load(cmd_list):
    """
    Copy or moves files from external destinations.
    """

    # 0: No param allowed, 1: param optional, 2: param obligatory
    # if not checkArgs(_arg_dict,
    #    {'-t': 0, '--test': 0, '-p': 2, '--path': 2}):
    #    return
    atom_path = dict(name='path', short='p', args=MANDATORY_PARAM)
    atom_move = dict(name='move', short='m', args=NONE_PARAM)
    atom_force = dict(name='force', short='f', args=NONE_PARAM)
    atom_verbose = dict(name='verbose', short='v', args=NONE_PARAM)
    atom_test = dict(name='test', short='t', args=NONE_PARAM)
    atom_none = dict(name='', short='', args=MANDATORY_PARAM)

    ret = check_rules(cmd_list,
                      [
                          [
                              dict(atom=atom_path, obligat=True),
                              dict(atom=atom_force, obligat=False),
                              dict(atom=atom_verbose, obligat=False),
                              dict(atom=atom_move, obligat=False),
                              dict(atom=atom_test, obligat=False)
                          ],
                          [
                              dict(atom=atom_none, obligat=True),
                              dict(atom=atom_force, obligat=False),
                              dict(atom=atom_verbose, obligat=False),
                              dict(atom=atom_move, obligat=False),
                              dict(atom=atom_test, obligat=False)
                          ]
                      ])

    if ret['message'] is not None:
        return

    # Get source
    if 'path' in ret['options']:
        src = ret['options']['path']
    else:
        try:
            key = '{0}.{1}'.format(plump.LOAD_PREFIX, ret['options'][''])
            if key in config.read_pickle():
                src = config.read_pickle()['{0}.{1}'.format(
                    plump.LOAD_PREFIX, ret['options'][''])]
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
    processing_flags = dict(verbose='verbose' in ret['options'],
                            move='move' in ret['options'],
                            force='force' in ret['options'])

    # print("cmd_load() processing_flags={}".format(processing_flags))

    # [dict(name='image001.jpg', exists='true')]
    analysis = load.analyse(src, dest)
    if 'test' in ret['options']:
        load.test(analysis, src, dest, processing_flags)
        return

    # load
    else:
        load.do(analysis, src, dest, processing_flags)

    return


def cmd_exif(cmd_list):
    """
    Set exif values
    """
    atom_none = dict(name='', short='', args=OPTIONAL_PARAM)
    atom_title = dict(name='title', short='t', args=MANDATORY_PARAM)
    atom_description = dict(name='description', short='d', args=MANDATORY_PARAM)
    atom_author = dict(name='author', short='a', args=NONE_PARAM)
    atom_check = dict(name='check', short='c', args=NONE_PARAM)
    atom_force = dict(name='force', short='f', args=NONE_PARAM)
    atom_verbose = dict(name='verbose', short='v', args=NONE_PARAM)

    # If none has an optional parameter, no other option in the same rule should have an optional parameter, too.
    ret = check_rules(cmd_list,
                      [
                          [
                              dict(atom=atom_none, obligat=True),
                              dict(atom=atom_verbose, obligat=False),
                          ],
                          [
                              dict(atom=atom_none, obligat=True),
                              dict(atom=atom_title, obligat=True),
                              dict(atom=atom_description, obligat=False),
                              dict(atom=atom_author, obligat=False),
                              dict(atom=atom_check, obligat=False),
                              dict(atom=atom_force, obligat=False),
                              dict(atom=atom_verbose, obligat=False),
                          ],
                          [
                              dict(atom=atom_none, obligat=True),
                              dict(atom=atom_title, obligat=False),
                              dict(atom=atom_description, obligat=True),
                              dict(atom=atom_author, obligat=False),
                              dict(atom=atom_check, obligat=False),
                              dict(atom=atom_force, obligat=False),
                              dict(atom=atom_verbose, obligat=False),
                          ],
                          [
                              dict(atom=atom_none, obligat=True),
                              dict(atom=atom_title, obligat=False),
                              dict(atom=atom_description, obligat=False),
                              dict(atom=atom_author, obligat=True),
                              dict(atom=atom_check, obligat=False),
                              dict(atom=atom_force, obligat=False),
                              dict(atom=atom_verbose, obligat=False),
                          ]
                      ])

    if ret['message'] is not None:
        return

    # Get author
    if 'author' in ret['options']:
        try:
            author = config.read_pickle()["{}.{}".format(plump.EXIF_PREFIX, 'author')]
            if len(str(author)) == 0:
                print("Destination value not defined. Create it with config -s '{}.author=<value>' first."
                      .format(plump.EXIF_PREFIX))
                return
            # Replace year
            author = author.replace("{YYYY}", str(datetime.now().year))

        except (TypeError, KeyError):
            print("xDestination value not defined. Create it with config -s '{}.author=<value>' first."
                  .format(plump.EXIF_PREFIX))
            return
    else:
        author = None

    if not task.check_actual():
        return

    src_dir = task.get_actual()['task'] + '/' + plump.DIR_FINAL
    src_path = task.get_task_path(src_dir)

    # None, '*', 1,2,3 or a file name
    files = fow_exif.check_images(src_path, ret['options'][''])
    # print("cmd_exif() files={}".format(str(files)))
    if files is None:
        print("No images found")
        return

    if 'title' in ret['options']:
        title = ret['options']['title']
    else:
        title = None

    if 'description' in ret['options']:
        description = ret['options']['description']
    else:
        description = None

    analysis = fow_exif.analyse(src_path, files, title, description, author)

    # print("cmd_exif() value=" + str(analysis))

    if title is None and description is None and author is None:
        fow_exif.show(analysis, src_dir, 'verbose' in ret['options'])
        return

    if 'check' in ret['options']:
        fow_exif.test(analysis, src_dir, title is not None, description is not None, author is not None,
                      'force' in ret['options'], 'verbose' in ret['options'])
        return

    # exif --force
    if 'force' not in ret['options']:
        overwritten_tags = [a for a in analysis if a['title']['overwrite'] or a['description']['overwrite']
                            or a['author']['overwrite']]
        if len(overwritten_tags) > 0:
            print("Value(s) would be overwritten, use --force to to this.")
            return

    # Do it!
    fow_exif.do(analysis, src_path, title is not None, description is not None, author is not None,
                'verbose' in ret['options'])


def cmd_export(cmd_list):
    """
    Copy finals to external destinations.
    """
    # 0: No param allowed, 1: param optional, 2: param obligatory
    # if not checkArgs(_arg_dict,
    #    {'-t': 0, '--test': 0, '-p': 2, '--path': 2}):
    #    return
    atom_path = dict(name='path', short='p', args=MANDATORY_PARAM)
    atom_force = dict(name='force', short='f', args=NONE_PARAM)
    atom_test = dict(name='test', short='t', args=NONE_PARAM)
    atom_none = dict(name='', short='', args=MANDATORY_PARAM)

    ret = check_rules(cmd_list,
                      [
                          [
                              dict(atom=atom_path, obligat=True),
                              dict(atom=atom_force, obligat=False),
                              dict(atom=atom_test, obligat=False)
                          ],
                          [
                              dict(atom=atom_none, obligat=True),
                              dict(atom=atom_force, obligat=False),
                              dict(atom=atom_test, obligat=False)
                          ]
                      ])

    if ret['message'] is not None:
        return

    # Get destination
    if 'path' in ret['options']:
        destination = ret['options']['path']
    else:
        try:
            destination = config.read_pickle()[plump.EXPORT_PREFIX + '.' + ret['options']['']]
        except:
            print("Destination value not defined. Create it with config -s='export.{}' first."
                  .format(ret['options']['']))
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
    if 'test' in ret['options']:
        export.test(analysis, src_dir, destination)
        return

    # export --force
    if 'force' in ret['options']:
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


def cmd_task(cmd_list):
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
    atom_none = dict(name='', short='', args=NONE_PARAM)
    atom_create = dict(name='create', short='c', args=MANDATORY_PARAM)
    atom_activate = dict(name='activate', short='a', args=MANDATORY_PARAM)
    atom_next = dict(name='next', short='n', args=NONE_PARAM)
    atom_previous = dict(name='previous', short='p', args=NONE_PARAM)
    atom_short = dict(name='short', short='s', args=NONE_PARAM)
    atom_long = dict(name='long', short='l', args=NONE_PARAM)
    atom_raw_import = dict(name='raw-import', short='r', args=NONE_PARAM)
    atom_fill_final = dict(name='fill-final', short='f', args=NONE_PARAM)
    atom_test = dict(name='test', short='t', args=NONE_PARAM)

    ret = check_rules(cmd_list,
                      [
                          [
                              dict(atom=atom_create, obligat=True)
                          ],
                          [
                              dict(atom=atom_activate, obligat=True)
                          ],
                          [
                              dict(atom=atom_none, obligat=True),
                              dict(atom=atom_short, obligat=False)
                          ],
                          [
                              dict(atom=atom_none, obligat=True),
                              dict(atom=atom_long, obligat=False)
                          ],
                          [
                              dict(atom=atom_next, obligat=True)
                          ],
                          [
                              dict(atom=atom_previous, obligat=True)
                          ],
                          [
                              dict(atom=atom_raw_import, obligat=True),
                              dict(atom=atom_test, obligat=False)
                          ],
                          [
                              dict(atom=atom_fill_final, obligat=True),
                              dict(atom=atom_test, obligat=False)
                          ]
                      ])

    if ret['message'] is not None:
        return

    # print("cmd_task() ret={}".format(str(ret)))

    # --- Options to change the actual task (activate or create)---#
    if 'create' in ret['options'] or 'activate' in ret['options']:
        if 'create' in ret['options']:
            path_arg = ret['options']['create']
        else:
            path_arg = ret['options']['activate']

        # arg for option '' is the path, Path may not end with '/'
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
        if 'create' in ret['options']:
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

        if 'activate' in ret['options']:
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
    if 'short' in ret['options'] or 'long' in ret['options'] or len(ret['options']) == 1:
        if task.get_actual() is None:
            print('No actual task. ' +
                  'Use "task --create <task>" to create one.')
        else:
            if 'short' in ret['options']:
                print('Actual task {}. Showing a summary.'.format(task.get_actual()['task']))
                show.task_summary(
                    plump.get_path(plump.DIR_02) + '/'
                    + task.get_actual()['task'])
            elif 'long' in ret['options']:
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
    if 'raw-import' in ret['options']:
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
            + '/' + plump.DIR_RAW, 'test' in ret['options'])
        return

    # task --fill-final
    # task --fill-final --test
    if 'fill-final' in ret['options']:
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
            'test' in ret['options'])
        return

    # task --next
    # task --previous
    if 'next' in ret['options'] or 'previous' in ret['options']:
        if 'previous' in ret['options']:
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


def cmd_backup(cmd_list):
    """
    Backup data to external file system. Input is the argument structure.
    """
    atom_none = dict(name='', short='', args=NONE_PARAM)
    atom_path = dict(name='path', short='p', args=MANDATORY_PARAM)
    atom_test = dict(name='test', short='t', args=NONE_PARAM)

    ret = check_rules(cmd_list,
                      [
                          [
                              dict(atom=atom_none, obligat=True),
                              dict(atom=atom_path, obligat=False),
                              dict(atom=atom_test, obligat=False)
                          ]
                      ])

    if ret['message'] is not None:
        return

    # backup --path <path>
    if 'path' in ret['options']:
        path = ret['options']['path']
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
    if 'test' in ret['options']:
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


def cmd_show(cmd_list):
    """
    Processing step reporting
    """

    atom_short = dict(name='short', short='s', args=NONE_PARAM)
    atom_none = dict(name='', short='', args=OPTIONAL_PARAM)

    # atomNone must be mandatory for rules with more than one path
    ret = check_rules(cmd_list,
                      [
                          [
                              dict(atom=atom_none, obligat=True),
                              dict(atom=atom_short, obligat=False)
                          ]
                      ])
    if ret['message'] is not None:
        return

    if ret['options'][''] == 'inbox':
        if 'short' in ret['options']:
            show.in_summary(plump.get_path(plump.DIR_00))
        else:
            show.show_in(plump.get_path(plump.DIR_00))
        return

    if ret['options'][''] == 'import':
        if 'short' in ret['options']:
            show.in_summary(plump.get_path(plump.DIR_01))
        else:
            show.show_in(plump.get_path(plump.DIR_01))
        return

    if ret['options'][''] == 'in':
        if 'short' in ret['options']:
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

    if ret['options'][''] == 'tasks':
        if 'short' in ret['options']:
            show.tasks_summary()
        else:
            show.tasks()
        return

    # if 'task' in args['args'] or len(args['args']) == 0:
    if ret['options'][''] in ('task', None):
        if task.get_actual() is None:
            print('No actual task. ' +
                  'Use "task --create <task>" to create one.')
        else:
            print('Actual task is ' + task.get_actual()['task'] + '.')
            if 'short' in ret['options']:
                show.task_summary(plump.get_path(plump.DIR_02) + '/'
                                  + task.get_actual()['task'])
            else:
                show.show_task(plump.get_path(plump.DIR_02) + '/'
                               + task.get_actual()['task'], False)
        return


def cmd_config(cmd_list):
    """
    Set or delete a config item
    """

    # Restrictions for rule building:
    # - If none has OPTIONAL_PARAMETER, avoid a second OPTIONAL_PARAMETER
    atom_none = dict(name='', short='', args=NONE_PARAM)
    atom_list = dict(name='list', short='l', args=OPTIONAL_PARAM)
    atom_set = dict(name='set', short='s', args=MANDATORY_PARAM)
    atom_delete = dict(name='delete', short='d', args=MANDATORY_PARAM)

    ret = check_rules(cmd_list,
                      [
                          [
                              dict(atom=atom_none, obligat=True)
                          ],
                          [
                              dict(atom=atom_list, obligat=True)
                          ],
                          [
                              dict(atom=atom_delete, obligat=True)
                          ],
                          [
                              dict(atom=atom_set, obligat=True)
                          ]
                      ])

    if ret['message'] is not None:
        return

    settings = config.read_pickle()
    unknown_msg = "Key '{0}' not found."

    if 'delete' in ret['options']:
        arg = ret['options']['delete']
        if arg in settings:
            del settings[arg]
            config.create_pickle(settings)
        else:
            print(unknown_msg.format(arg))

        return

    if 'set' in ret['options']:
        arg = ret['options']['set']
        (key, value) = arg.split('=')
        settings[key] = value
        config.create_pickle(settings)

        return

    if 'list' in ret['options'] or '' in ret['options']:
        if 'list' in ret['options']:
            arg = ret['options']['list']
        else:
            arg = ret['options']['']

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


def cmd_init(cmd_list):
    """
    Initializes the fow. Call this once.
    """

    atom_force = dict(name='force', short='f', args=NONE_PARAM)
    atom_none = dict(name='', short='', args=NONE_PARAM)

    ret = check_rules(cmd_list,
                      [
                          [
                              dict(atom=atom_none, obligat=True),
                              dict(atom=atom_force, obligat=False)
                          ]
                      ])

    if ret['message'] is not None:
        return

    if 'force' not in ret['options']:
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
        cmd_help(cmds)

    elif cmds[0] == 'config':
        cmd_config(cmds)

    elif cmds[0] == 'init':
        cmd_init(cmds)

    elif cmds[0] == 'backup':
        cmd_backup(cmds)

    elif cmds[0] == 'task':
        cmd_task(cmds)

    elif cmds[0] == 'show':
        cmd_show(cmds)

    elif cmds[0] == 'export':
        cmd_export(cmds)

    elif cmds[0] == 'exif':
        cmd_exif(cmds)

    elif cmds[0] == 'load':
        cmd_load(cmds)

    elif cmds[0] == 'rename':
        cmd_rename(cmds)

    elif cmds[0] == 'xe2hack':
        cmd_xe2hack(cmds)

    elif cmds[0] == 'gps':
        cmd_gps(cmds)

    else:
        print('Unknown command. Use help to list all commands.')


def cmd_help(cmd_list):
    """
    Show man page. For specific command help, there has to be one
    file for each command with name fow-<command>. The first line of this
    file must be the abstract of the command.
    """
    atom_none = dict(name='', short='', args=OPTIONAL_PARAM)

    ret = check_rules(cmd_list,
                      [
                          [dict(atom=atom_none, obligat=True)
                           ]
                      ])

    if ret['message'] is not None:
        return

    # help <command>
    if ret['options'][''] is not None:
        i = 0
        # try:
        # For developing call man page local, without index db
        if config.read_installation_item('MAN_DIRECT'):
            i = os.system('man -l ' + config.get_help_file_dir() +
                          '/fow-' + ret['options'][''] + '.1.gz')
        else:
            i = os.system('man ' + 'fow-' + ret['options'][''])
        # except:
        #     # Does't work, no exception thrown
        #     print(ret['options'][''] + ' is unknown. ' + 'Use help to see all commands.')
        if i != 0:
            print("See 'fow help'.")

    # help
    else:

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
