# -*- coding: utf-8 -*-
import pickle
import os
import sys
import task
import shutil
import time
import subprocess

DIR_00 = '00_Inbox'
DIR_01 = '01_Import'
DIR_02 = '02_Progress'
DIR_FOW = '.fow'
DIR_VIDEO = 'video'
DIR_JPG = 'jpg'
DIR_RAW = 'raw'
DIR_FINAL = 'final'
DIR_WORK = 'work'
VERSION = '1.1.3'
BACKUP_PATH = 'backup.path'
GPX_DIR = 'gpxDir'
TASK = 'task'
TYPE_RAW = 'raw'
TYPE_JPG = 'jpg'
TYPE_TIF = 'tif'

#Groups all exports destinations together. The have to start with 'export.'
EXPORT_PREFIX = 'export'
#Groups all load destinations together. The have to start with 'load.'
LOAD_PREFIX = 'load'

#####################################################################
# Conventions:
# - A 'path' is an absolute path within the system. On the other
#   hand is a 'subdir' a subdirectory within a fow.
#####################################################################


# configuration file for this fow installation, read once with readFowConfig()
fow_config = None


#def cd_do(_args):
    #"""
    #cd execution.
    #"""
    ##print('cd_do: args={0}'.format(str(_args)))
    #args = _args['args']

    #if len(args) == 0:
        #print('no args')
        #sys_cd(get_fow_root())
        #print('no args')
    #elif args[0] == 't' or args[0] == 'task':
        #print('cd task')
    #elif args[0] == '0'or args[0] == 'inbox':
        #print('cd 0')
    #elif args[0] == '1'or args[0] == 'import':
        #print('cd 1')
    #else:
        #print('Unknown destination. See help cd for more infos.')

    #return

#Das geht alles nicht. Funktion nicht machen!!
#def sys_cd(path):
    #"""
    #system execution for cd.
    #"""
    #print('cwd={0}'.format(os.getcwd()))
    #os.system('cd {0}'.format(path))
    #print(os.getcwd())
    #return

    ##prevdir = os.getcwd()
    #cmd = '{0}'.format(os.path.expanduser(path))
    #print('syst_cd: {0}'.format(str(cmd)))
    #os.chdir('/')
    #try:
        #print('yield...')
        #yield
        #print(os.getcwd())
    #finally:
        #print('finally')
        #os.chdir(prevdir)
    ##try:
        #subprocess.check_output(
                #cmd,
                #stderr=subprocess.STDOUT,
                #shell=True,
                #universal_newlines=True)
    #except subprocess.CalledProcessError as err:
    ##except subprocess.CalledProcessError:
        #print(str(err))
        #return None


def get_task_triple(offset):
    """
    Returns dict with three tasks active, previous, next.
    Offset: offset value the actual task. For instance, offset=-1 would return
    the tasks -2, -1 and 0 relative to the active task.
    Actual: the active task or, if offset<> 0, the relative task. If
    there is no task active, the first task will be returned.
    If there is just one task, this one will be returned
    Returns None, if there are no tasks.
    next and previous are set to None, if there is only one task
    The task list is seen as a ring list, the task 'last+1' will be set to
    task 0 and, on the otherhand, the task -1 will be set to last task.

    Example:
        return dict=(
        a_task=dict(subdir='family',task='holidays',active=true),
        p_task=dict(subdir='family',task='birthday',active=False),
        n_task=dict(subdir='weekly',task='20160101',active=False))

    """
    tasks = []

    dir02 = os.listdir(get_path(DIR_02))
    dir02.sort()
    active = task.get_actual()

    for each_folder in dir02:
        task_dirs = os.listdir(get_path(DIR_02) + '/' + each_folder)
        task_dirs.sort()
        for each_task in task_dirs:
            if active['folder'] == each_folder and \
                active['name'] == each_task:
                is_active = True
            else:
                is_active = False

            tasks.append(dict(subdir=each_folder, task=each_task,
                active=is_active))

    #print('get_next_task() ' + str(tasks))

     #Just one or none task
    if len(tasks) == 0:
        return None
    elif len(tasks) == 1:
        return dict(a_task=tasks[0], n_task=None, p_task=None)

     # Find active item
    max_i = len(tasks) - 1

    active_i = -1
    for i in range(0, max_i + 1):
        #print('i={0}'.format(i))
        if tasks[i]['active']:
            active_i = i
            break
    #print('active_i={0}, offset={1}'.format(active_i, offset))

    i_active = active_i + offset
    i1 = i_active - 1
    i2 = i_active + 1
    #if(backwards):
        #i_active = active_i - 1
        #i1 = active_i - 2
        #i2 = active_i
    #else:
        #i_active = active_i + 1
        #i1 = active_i
        #i2 = active_i + 2
    #print('get_next_task() p={0} a={1} n={2}'.format(i1, i_active, i2))

    #Handle out of ranges
    if i_active < 0:
        i_active = max_i + i_active + 1
    elif i_active >= max_i:
        i_active = i_active - max_i - 1
    if i1 < 0:
        i1 = max_i + i1 + 1
    elif i1 >= max_i:
        i1 = i1 - max_i - 1
    if i2 < 0:
        i2 = max_i - i2 + 1
    elif i2 >= max_i:
        i2 = i2 - max_i - 1

    #print('get_next_task() p={0} a={1} n={2}'.format(i1, i_active, i2))
    return dict(a_task=tasks[i_active], p_task=tasks[i1],
        n_task=tasks[i2])


def xe2hack_analyse(path, from_model, to_model):
    """
    Analyses for xe2hack command for all RAW files in the given path.
    Returns a list with a dict for every file. List can be empty.
    revert: Set true to revert naming (X-E2S to XE2)
    Example with explanations:
    dict=(path=path, from_model='X-E2S', to_model='X-E2', files=
        [dict=(
            subdir='RAW'
            file_name='img001.raf'),               #file name of X-E2 image
            dict=(...), ...
        ])
    """
    ret = []

    subdir = DIR_RAW
    for each in list_raw(path + '/' + subdir):
        file_path = path + '/' + subdir + '/' + each
        #print(file_path + '=' + str(image_get_model(file_path)))
        file_name = each
        model = image_get_model(file_path)
        if model == from_model:
            ret.append(dict(subdir=subdir, file_name=file_name))

    return dict(path=path, from_model=from_model, to_model=to_model,
        files=ret)


def xe2hack_do(analysis):
    """
    Rename execution.
    """
    print('Root path is: {0}'.format(analysis['path']))
    print('Changing model from "{0}" to "{1}":'
        .format(analysis['from_model'], analysis['to_model']))
    for each in analysis['files']:
        cmd = 'exiftool -overwrite_original -Model="{0}" {1}/{2}/{3}'.format(
                        analysis['to_model'],
                    analysis['path'], each['subdir'], each['file_name'])
        #print('xe2hack_do(): cmd={0}'.format(cmd))
        try:
            subprocess.check_output(
                    cmd,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    universal_newlines=True)
        #except subprocess.CalledProcessError as err:
        except subprocess.CalledProcessError:
            #print(str(err))
            return None

        print('{0} {1}'.format(each['subdir'], each['file_name']))

    print('{0} file(s) changed.'.format(len(analysis['files'])))


def xe2hack_test(analysis):
    """
    Dry run of rename command.
    verbose - boolean
    """
    print('Dry-run. Root path is: {0}'.format(analysis['path']))
    print('Changing model from "{0}" to "{1}":'.format(
        analysis['from_model'], analysis['to_model']))
    for each in analysis['files']:
        print('{0} {1}'.format(each['subdir'], each['file_name']))
    print('{0} file(s) would be changed.'.format(len(analysis['files'])))


def rename_analyse(src_path, dest_path):
    """
    Analyses for renaming command for all image files in the given path.
    Returns a list with a dict for every file. List can be empty.
    Supported image file types are: jpg, raw and videos; it will be
    always search for every image type. Other files will be untouched
    (XMP, tiff).
    Example with explanations:
    dict=(src_path=src_path, dest_path=dest_path, files=
        [dict=(
            subdir='RAW'
            old_name='img001.raf',                 #file name in src_path
            new_name='20161131-123456-img001.raf', #new image name
            exists=True),                      #False, if no file name conflict
                                                   #in dest_path
            dict=(...), ...
        ]
    """
    ret = []

    subdir = DIR_JPG
    for each in list_jpg(src_path + '/' + subdir):
        #print(str(image_get_time(path)))
        old_name = each
        time_str = image_get_time(src_path + '/' + subdir + '/' + each)
        if time_str is None:
            new_name = old_name
        else:
            new_name = time_str + '-' + old_name

        if os.path.exists(dest_path + '/' + subdir + '/' + new_name):
            exists = True
        else:
            exists = False

        ret.append(dict(subdir=subdir, old_name=old_name, new_name=new_name,
            exists=exists))

    subdir = DIR_RAW
    for each in list_raw(src_path + '/' + subdir):
        #print(str(image_get_time(path)))
        old_name = each
        time_str = image_get_time(src_path + '/' + subdir + '/' + each)
        if time_str is None:
            new_name = old_name
        else:
            new_name = time_str + '-' + old_name

        if os.path.exists(dest_path + '/' + subdir + '/' + new_name):
            exists = True
        else:
            exists = False

        ret.append(dict(subdir=subdir, old_name=old_name, new_name=new_name,
            exists=exists))

    subdir = DIR_VIDEO
    for each in list_video(src_path + '/' + subdir):
        #print(str(image_get_time(path)))
        old_name = each
        time_str = image_get_time(src_path + '/' + subdir + '/' + each)
        if time_str is None:
            new_name = old_name
        else:
            new_name = time_str + '-' + old_name

        if os.path.exists(dest_path + '/' + subdir + '/' + new_name):
            exists = True
        else:
            exists = False

        ret.append(dict(subdir=subdir, old_name=old_name, new_name=new_name,
            exists=exists))

    return dict(src_path=src_path, dest_path=dest_path, files=ret)


def rename_do(analysis, verbose, force):
    """
    Rename execution.
    """

    errs = [each for each in analysis['files'] if each['exists'] is True]
    if len(errs) > 0:
        if not force:
            print(('{0} file(s) would be overwritten! Remove them or use '
                + '--force to overwrite file(s). '
                + 'Use rename -t -v to list conflicts.').format(len(errs)))
            return

    cntMoved = 0
    cntOverwritten = 0

    for each in analysis['files']:
        try:
            os.rename(analysis['src_path'] + '/' + each['subdir'] + '/'
                + each['old_name'],
                analysis['dest_path'] + '/' + each['subdir'] + '/'
                + each['new_name'])
            cntMoved += 1
            if verbose:
                if each['exists']:
                    status = '! OVR '
                    cntOverwritten += 1
                else:
                    status = '  OK  '
                print(status + each['subdir'] + ' ' + each['old_name']
                    + ' --> ' + each['new_name'])

        except OSError as e:
            print(str(e))
            status = '! NOK '
            #print(status + each['subdir'] + ' ' + each['old_name']
                #+ ' --> ' + each['new_name'])
            print('{0}/{1} file(s) moved.'.format(cntMoved,
                len(analysis['files'])))
            return

    if cntOverwritten > 0:
        print('{0} file(s) moved, which {1} were overwritten.'
            .format(cntMoved, cntOverwritten))
    else:
        print('{0} file(s) moved.'.format(cntMoved))


def rename_test(analysis, verbose, force):
    """
    Dry run of rename command.
    verbose - boolean
    """
    cntOk = 0
    cntNok = 0
    for each in analysis['files']:
        if not each['exists']:
            cntOk += 1
            if verbose:
                status = '  OK  '
                print(status + each['subdir'] + ' ' + each['old_name']
                    + ' --> ' + each['new_name'])
        else:
            cntNok += 1
            if verbose:
                if force:
                    status = '! OVR '
                    print(status + each['subdir'] + '/' + each['new_name']
                        + ' exists')
                else:
                    status = '! NOK '
                    print(status + each['subdir'] + ' '
                    + 'File already exists: ' + each['new_name'])

    if cntNok > 0:
        if force:
            print(("{0}/{1} file(s) already exists an will be overwritten!")
                .format(cntNok, len(analysis['files'])))
        else:
            print(("{0}/{1} file(s) already exists. Remove them first from " +
                "destination or overwrite file(s) by using --force.")
                .format(cntNok, len(analysis['files'])))
    else:
        print("{0} files will be moved and renamed.".format(cntOk))


def export_copy(analysis, src_dir, dest):
    """
    Copies files.
    """
    name = ''
    try:
        for item in analysis:
            name = item['name']
            shutil.copy2(src_dir + '/' + item['name'], dest)
            print('Copying ' + name + '. Done.')
    except IOError as err:
        print('Copying ' + name + '. Error!')
        print("I/O error: {0}".format(err))
        return
    except:
        print('Copying ' + name + '. Error!')
        print("Unexpected error:", sys.exc_info()[0])
        return


def export_test(analysis, src_dir, dest):
    """
    Prints an export test run.
    """
    #print(str(analysis))
    print('Destination: ' + dest)
    print(str(len(analysis)) + ' files in ' + src_dir)

    max_name_len = dictlist_get_max_length(analysis, 'name')

    for item in analysis:
        time_str = ''
        if item['exists']:
            status = 'o '
            time_str = time_readable(item['src_time']) + ' -> ' + \
                time_readable(item['dst_time'])
        else:
            status = '+ '
            time_str = time_readable(item['src_time'])
        print(status + item['name'].ljust(max_name_len) +
               ' ' + time_str)


def dictlist_get_max_length(analysis, fieldname):
    """
    Returns max string lenght for 'name' in list of dicts.
    """
    names = []
    for item in analysis:
        names.append(item[fieldname])

    return string_get_max_length(names)


def load_analyse(_src, _dest_root):
    """
    Checks load from external source tree to 00_Import sub directories
    jpg, raw and video.
    _src - absolut path to external root directory
    _dest - root directory for destination's sub
    Returns dict for every source file type jpg, raw and video.
    Every dict has a list with an dict for every file with fields
        file - file name
        path - absolut path of the source file
        time - timestamp of the source file
        exist - True, if file exists in destination directory
        desttime - None, if exist is None. Otherwise timestamp of dest file

    For instance:
    { 'jpg'  : [
            { 'file'    : 'img34.jpg',
              'path'    : 'loadtest/DCIM/0001'
              'time'    : 1485803027.9297857
              'exist'   : False
              'desttime': False}', ...],
      'raw'  : [...],
      'video': [...]
    }
    """
    #print('load_analyse() _src={0}'.format(_src))

    dest_jpg = '{0}/{1}'.format(_dest_root, DIR_JPG)
    dest_raw = '{0}/{1}'.format(_dest_root, DIR_RAW)
    dest_video = '{0}/{1}'.format(_dest_root, DIR_VIDEO)
    files_jpg = list_jpg(dest_jpg)
    files_raw = list_raw(dest_raw)
    files_video = list_video(dest_video)

    values = dict(jpg=[], raw=[], video=[])
    scan_tree(_src, values)
    #print('load_analyse() files_video={0}'.format(str(files_video)))

    #Add existing info
    for each_value in values['jpg']:
        #print('each_value {0}'.format(str(each_value)))
        each_value['exist'] = False
        each_value['desttime'] = None
        for each in [e for e in files_jpg if each_value['file'] == e]:
            each_value['exist'] = True
            each_value['desttime'] = os.path.getatime('{0}/{1}'.format(
                dest_jpg, each))

    for each_value in values['raw']:
        #print('each_value {0}'.format(str(each_value)))
        each_value['exist'] = False
        each_value['desttime'] = None
        for each in [e for e in files_raw if each_value['file'] == e]:
            each_value['exist'] = True
            each_value['desttime'] = os.path.getatime('{0}/{1}'.format(
                dest_raw, each))

    for each_value in values['video']:
        #print('each_value {0}'.format(str(each_value)))
        each_value['exist'] = False
        each_value['desttime'] = None
        for each in [e for e in files_video if each_value['file'] == e]:
            each_value['exist'] = True
            each_value['desttime'] = os.path.getatime('{0}/{1}'.format(
                dest_video, each))

    #print('values {0}'.format(str(values)))

    return values


def load_do(analysis, src, dest, options):
    """
    Executes command load.
    """
    #print('load_do() analysis={0}'.format(str(analysis)))
    #print('load_do() options={0}'.format(str(options)))
    #print('load_do() dest={0}'.format(str(dest)))
    done = 0
    error = 0
    overwritten = 0
    ignored = 0
    if options['move']:
        verb_past = 'moved'
        verb_present = 'move'
    else:
        verb_past = 'copied'
        verb_present = 'copy'

    ret = load_execute(analysis['jpg'], DIR_JPG, dest, options, verb_present)
    done += ret['done']
    error += ret['error']
    overwritten += ret['overwritten']
    ignored += ret['ignored']

    ret = load_execute(analysis['raw'], DIR_RAW, dest, options, verb_present)
    done += ret['done']
    error += ret['error']
    overwritten += ret['overwritten']
    ignored += ret['ignored']

    ret = load_execute(analysis['video'], DIR_VIDEO, dest, options,
        verb_present)
    done += ret['done']
    error += ret['error']
    overwritten += ret['overwritten']
    ignored += ret['ignored']

    if options['force']:
        if error:
            print(('{0}/{1} files {2} ({3} overwritten),' +
                ' but {4} errors occurred.')
                .format(done, done + error, verb_past, overwritten, error))
        elif done > 0:
            print('All {0} files {1} ({2} files overwritten).'
                .format(done + error, verb_past, overwritten))
        else:
            print('No files to {0}, nothing done.'
                .format(verb_present))
    else:
        if error:
            print('{0}/{1} files {2} ({3} ignored, but {4} errors occurred.'
                .format(done, done + error, verb_past, ignored, error))
        elif done > 0:
            print('All {0} files {1} ({2} existing files ignored).'
                .format(done + error, verb_past, ignored))
        elif ignored > 0:
            print('No files to {0}, but {1} existing files were ignored.'
                .format(verb_present, ignored))
        else:
            print('No files to {0}, nothing done.'
                .format(verb_present))


def load_execute(analysis, subdir, dest, options, verb_present):
    """
    Executes the load (copy or move), for a specific kind of image files
    (jpg, raw of videos).
    analysis: one part of the analyse dict; jpg, raw od video
    subdir: e.g. DIR_JPG
    dest: destination path
    verb_present: text 'move' or 'copy' for printing error
    Returns dictionary with statistic.
    Example
    return dict(done=1, overwritten=0, error=0, ignored=1)
    """
    ret = dict(done=0, overwritten=0, error=0, ignored=0)
    for each in analysis:
        source = '{0}/{1}'.format(each['path'], each['file'])
        destination = '{0}/{1}/{2}'.format(dest, subdir, each['file'])
        if not each['exist'] or options['force']:
            try:
                if options['move']:
                    os.rename(source, destination)
                else:
                    shutil.copy2(source, destination)
                ret['done'] += 1
                if each['exist']:
                    ret['overwritten'] += 1

            except:
                print('Failed to {0} file {1}'
                    .format(verb_present, str(each['file'])))
                ret['error'] += 1
        else:
            ret['ignored'] += 1

    return ret


def load_test(analysis, src, dest, options):
    """
    Prints an load test run.
    """
    if options['move']:
        kind = 'moved'
    else:
        kind = 'copied'

    print('Dry run, no files will be {0}.'.format(kind))
    print('Source     : {0}'.format(str(src)))
    print('Destination: {0}'.format(str(dest)))

    max_name_len = get_max_name_length(analysis, 'jpg', 'file')
    max_name_len2 = get_max_name_length(analysis, 'raw', 'file')
    max_name_len3 = get_max_name_length(analysis, 'video', 'file')
    if max_name_len2 > max_name_len:
        max_name_len = max_name_len2
    if max_name_len3 > max_name_len:
        max_name_len = max_name_len3

    #max_name_len = 30
    if options['verbose']:
        load_test_print(analysis['jpg'], max_name_len, 'JPG')
        load_test_print(analysis['raw'], max_name_len, 'RAW')
        load_test_print(analysis['video'], max_name_len, 'MOV')

    cntExists = len([i for i in analysis['jpg'] if i['exist']])
    cntExists += len([i for i in analysis['raw'] if i['exist']])
    cntExists += len([i for i in analysis['video'] if i['exist']])

    if options['move']:
        kind = 'moved'
    else:
        kind = 'copied'

    print(('Dry run. {0} JPGs, {1} RAWs and {2} videos in source ' +
        'directory {3} are ready to be {4}.').format(
        str(len(analysis['jpg'])), str(len(analysis['raw'])),
        str(len(analysis['video'])), src, kind))

    if cntExists > 0:
        if options['force']:
            print(('{0} files already exist and will be overwritten.')
                .format(cntExists))
        else:
            print(('{0} files already exist. Use option --force to ' +
                'overwrite them.').format(cntExists))


def load_test_print(files, max_name_len, type):
    """
    Prints info for the load analyse list of, e.g. for jpgs.
    """
    for item in files:
        time_str = ''
        if item['exist']:
            status = 'o'
            time_str = time_readable(item['time']) + ' -> ' + \
                time_readable(item['desttime'])
        else:
            status = ' '
            time_str = time_readable(item['time'])

        print('{0} {1} {2} {3}'.format(status, type,
            item['file'].ljust(max_name_len), time_str))

    return


def get_max_name_length(analysis, keyname, fieldname):
    """
    Returns max string lenght of all items in the dict with list of dicts.
    """
    names = []
    for item in analysis[keyname]:
        names.append(item[fieldname])

    return string_get_max_length(names)


def scan_tree(path, values):
    """
    Reads directory tree search image files recursive.
    Expands dict with a list for 'jpg', 'raw' and 'video'.
    path: absolut path
    values: dict to be expanded
    Example:
        values= dict(jpg=[dict(path='/img/sub' file='img01.jpg'), ...],
            raw=[dict(path='/img/sub' file='img01.raf'), ...],
            video=[dict(path='/img/sub' file='mov01.mp4'), ...])
    """
    #print('scan_tree() dir={0}'.format(str(path)))
    dirs = [d for d in os.listdir(path) if os.path.isdir('{0}/{1}'
        .format(path, d))]

    for f in list_jpg(path):
        atime = os.path.getatime('{0}/{1}'.format(path, f))
        values['jpg'].append(dict(path=path, file=f, time=atime))
    for f in list_raw(path):
        atime = os.path.getatime('{0}/{1}'.format(path, f))
        values['raw'].append(dict(path=path, file=f, time=atime))
    for f in list_video(path):
        atime = os.path.getatime('{0}/{1}'.format(path, f))
        values['video'].append(dict(path=path, file=f, time=atime))

    for d in dirs:
        scan_tree('{0}/{1}'.format(path, d), values)


def string_get_max_length(list):
    """
    For the given list with strings, the lenght of the max. String will be
    returned.
    For instance:
        string_get_max_length(['A', '123'])
            return 3
    """
    maxlen = 0
    for item in list:
        if len(item) > maxlen:
            maxlen = len(item)

    return maxlen


def export_analyse(_task, _dest):
    """
    Checks export to dest from given task.
    task: dictionary with keys 'task' (foldername/taskname),
                                'name' (task name),
                                'folder' (folder name)
    dest: String with absolut path
    Returns list with dict() for every source file, for instance:
        return [dict(name='image001.jpg', exists='true',
                src_time=1474878288.2156258,
                dst_time=1474878288.2156258)] or dst_time=None
    """
    src_dir = task.get_path(task.get_actual()['task']) + '/' + DIR_FINAL
    files = list_jpg(src_dir)
    #for file in files:
        #print('export_analyse() file=' + str(file) + ' '
            #+ time_readable(os.path.getatime(src_dir + '/' + file)))

    ret = []
    for file in files:
        exists = os.path.exists(_dest + '/' + file)
        if(exists):
            dst_time = os.path.getatime(_dest + '/' + file)
        else:
            dst_time = None

        ret.append(dict(
            name=file,
            exists=exists,
            src_time=os.path.getatime(src_dir + '/' + file),
            dst_time=dst_time
            ))

    #print('export_analyse() ret=' + str(ret))

    return ret


def time_readable(seconds):
    """
    Returns String with readable time for the given timestamp.
    Example:
        time_redable(1474878288.2156258)
            return Mon, 26 Sep 2016 10:24:48
    """
    return time.strftime("%a, %d %b %Y %H:%M:%S",
                time.localtime(seconds))


def get_fow_root():
    """
    The root directory of a fow must have a .fow directory.
    Returns String with path of the root directory of this fow with
    and ending '/'.
    Or, if actual directory is not within a fow, None will be returned.
    """
    actual = os.getcwd()
    parts = [x for x in actual.split('/') if len(x) > 0]
    #print('parts=' + str(parts))

    paths = []
    tpath = '/'
    for i in range(0, len(parts)):
        tpath = tpath + parts[i] + '/'
    #print(str(paths))
        paths.append(tpath)

    for i in range(0, len(paths) - 1):
        #print(paths[len(paths) - 1 - i])
        path = paths[len(paths) - 1 - i]
        files = [x for x in os.listdir(path)
                 if x == DIR_FOW]
        if len(files) == 1:
            return path

    # No .fow found
    return None


def is_fow_root(path):
    """
    Return True, if the path is the root directory of a fow,
    otherwise False.
    """
    for each_file in os.listdir(path):
        #print('each_file=' + each_file)
        if each_file == '.fow':
            return True

    return False


def is_fow():
    """
    If the actual directory is within a fow, True will be returned
    silently. Otherwise a message wil be printed and False will be returned.
    """
    #print(str(get_fow_root()))
    if get_fow_root() is None:
        print('Actual path is not within a fow. See "help init" how to ' +
                'create a new fow here or change your actual directory ' +
                'to a fow.')
        return False

    return True


def getHelpFileDir():
    """
    Returns the string path to the help files. In this directory, there has
    to be a file for every command.
    """
    #return 'helpFiles'
    #return 'man'
    #return '/usr/share/man/man1'

    #print('HELP_FILE_DIR=' + readFowConfig('HELP_FILE_DIR'))
    return readFowConfig('HELP_FILE_DIR')


def readFowConfig(_key):
    """
    Returns String with value of installation specific key value pairs.
    First access will read file 'config' in the lib directory.
    If file doesn't exists, exit(1) will be executed.
    If key doesn't exists, empty string will be returned.
    """
    global fow_config
    if fow_config is None:
        fow_config = dict()
        try:
            with open(sys.path[0] + '/config', 'r') as config:
                for each_line in config:
                    if len(each_line) > 1 and not each_line[0] == '#' \
                        and '=' in each_line:
                        (key, value) = each_line.split('=', 1)
                        if len(value) > 1 and value[-1] == '\n':
                            value = value[0:-1]
                        fow_config[key] = value
        except IOError as e:
            print(str(e))
            exit(1)
            return('')
        #print(str(fow_config))

    try:
        return fow_config[_key]
    except:
        return ''


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
    Returns a dictionary from setting.pickle.
    Returns None, if setting not found
    Example:
        return dict(task='w/kw05', export.pc='/media/diskstation/photo/w')
    """
    settings = dict()
    try:
        with open(get_fow_root() + '/' + DIR_FOW + '/setting.pickle',
                    'rb') as data:
            settings = pickle.load(data)
    except:
        print('setting.pickle not found but will be created with next writing.')
        return None

    return settings


def copy_missing_jpgs(src_dir, dest_dir, dry_run):
    """
    Copies all jpgs from source directory to destination directory, if they
    didn't already exist there.
    src_dir is the /row directory with raws to move.
    dest_dir is the target directory.
    """
    #print('src=' + src_dir)
    #print('dst=' + dest_dir)

    srcs = get_files_as_dict(list_jpg(src_dir))
    #print(str(srcs))

    dests = get_files_as_dict(list_jpg(dest_dir))
    #print(str(dests))

#    files = [s for s in srcs if not s in dests]
    files = []
    for each_src in srcs:
        found = False
        for each_dest in dests:
            if each_dest['name'] == each_src['name']:
                found = True
                break
        if not found:
            files.append(each_src['filename'])

    #print(str(files))

    if len(files) == 0:
        print('No JPGs to copy.')
        return

    if dry_run:
        print('JPG files to copy (missing files):')
        for each_file in files:
            print(str(each_file))
    else:
        for each_file in files:
            os.system('cp ' + src_dir + '/' + each_file +
                      ' ' + dest_dir + '/' + each_file)


def move_corresponding_raws(jpg_dir, src_dir, dest_dir, dry_run):
    """
    Moves all corresponding raws from source directory to destination directory.
    jpg_dir is the /jpg directory with corresponding jpg files.
    src_dir is the /row directory with raws to move.
    dest_dir is the target directory.
    """
    #print('jpg=' + jpg_dir)
    #print('src=' + src_dir)
    #print('dst=' + dest_dir)

    jpgs = list_jpg(jpg_dir)
    #print(str(jpgs))

    raws = list_raw(src_dir)
    #print(str(raws))
    files = [r for r in raws for j in jpgs
                if filename_get_name(r) == filename_get_name(j)]

    if len(files) == 0:
        print('No RAWs to move.')
        return

    if dry_run:
        print('raw files to move (may already exists):')
        for each_file in files:
            print(str(each_file))
    else:
        for each_file in files:
            os.rename(src_dir + '/' + each_file, dest_dir + '/' + each_file)


def path_get_subdir(path):
    """
    Returns the last segment of the path,
     or "", if path has no segments.
    Does not care, if last path segment is a file or a subdir.
    """
    if path.rfind('/', 1) == -1:
        return ""

    (parent, subdir) = path.rsplit('/', 1)

    return subdir


def path_get_parent(path):
    """
    Returns the path without the file or last sub directory,
     or "", if path if path has no segments.
    Does not care, if last path segment is a file or a subdir.
    """
    if path.rfind('/', 1) == -1:
        return ""

    (parent, subdir) = path.rsplit('/', 1)

    return parent


def filename_get_suffix(filename):
    """
    Returns the suffix of the give file without its optional suffix.
    """
    if filename.rfind('.', 1) == -1:
        return ""

    (name, suffix) = filename.rsplit('.', 1)

    return suffix


def filename_get_name(filename):
    """
    Returns the name of the give file without its optional suffix.
    """
    if filename.rfind('.', 1) == -1:
        return filename

    (name, suffix) = filename.rsplit('.', 1)

    return name


def get_files_as_dict(files):
    """
    For the given list of file names, a list of dictionaries
    will be retured with fields 'file', 'name' and 'suffix'
    will be returned.
    Example: get_files_as_dict(['img1.jpg'] returns
        [dict(filename='img1.jpg', name='img1', suffix='jpg')]
    """
    #print('files=' + str(files))
    ret = []
    for each_file in files:
        ret.append(dict(filename=each_file,
                         name=filename_get_name(each_file),
                         suffix=filename_get_suffix(each_file)))

    #print(str('ret=' + str(ret)))
    return ret


def filename_get_type(filename):
    """
    Returns the type of a file. Supported types are:
        RAW, JPG, TIF
    Or, if other
    """
    suffixes = ['jpg', 'JPG']
    for s in suffixes:
        if filename_get_suffix(filename) == s:
            return TYPE_JPG

    suffixes = ['RAW', 'raw', 'RAF', 'raf', 'cr2', 'CR2']
    for s in suffixes:
        if filename_get_suffix(filename) == s:
            return TYPE_RAW

    suffixes = ['tif', 'TIF']
    for s in suffixes:
        if filename_get_suffix(filename) == s:
            return TYPE_TIF

    return None


def list_jpg(path):
    """
    Like os.listdir, a list with jpg files will be returned.
    Supported suffixes: jpg, JPG.
    """
    suffixes = ['jpg', 'JPG']
    return [f for f in os.listdir(path) for s in suffixes
        if filename_get_suffix(f) == s]


def list_raw(path):
    """
    Like os.listdir, a list with raw files will be returned.
    Supported suffixes: 'RAW', 'raw', 'RAF', 'raf', 'cr2', 'CR2'.
    """
    suffixes = ['RAW', 'raw', 'RAF', 'raf', 'cr2', 'CR2']
    return [f for f in os.listdir(path) for s in suffixes
        if filename_get_suffix(f) == s]


def list_video(path):
    """
    Like os.listdir, a list with video files will be returned.
    Supported suffixes: 'MOV', 'mov', 'MP4', 'mp4'.
    """
    suffixes = ['MOV', 'mov', 'MP4', 'mp4']
    return [f for f in os.listdir(path) for s in suffixes
        if filename_get_suffix(f) == s]


def DEPRECATED_get_status(path):
    """
    Returns a list (sorted by name) of dictionaries with the status about a
    task in sub folder 'path', based by the image name. Example for return:
        return [dict(image='image1', final=False, jpg=True, raw=True,
                        title='Lonely man in the park' )]
        name: Image name without suffix
        final, jpg, raw: True, if a file of this image is this subfolder
        title: title of the final image
    path must be a subdir
    """
    path_final = path + '/' + DIR_FINAL
    path_jpg = path + '/' + DIR_JPG
    path_raw = path + '/' + DIR_RAW
    dirs = os.listdir(path)

    if DIR_FINAL in dirs:
        final_files = os.listdir(path_final)
    else:
        final_files = []
    if DIR_JPG in dirs:
        jpg_files = list_jpg(path_jpg)
    else:
        jpg_files = []
    if DIR_RAW in dirs:
        raw_files = list_raw(path_raw)
    else:
        raw_files = []

    images = []
    final_images = []
    jpg_images = []
    raw_images = []
    for each_file in final_files:
        images.append(filename_get_name(each_file))
        final_images.append(filename_get_name(each_file))
    for each_file in jpg_files:
        images.append(filename_get_name(each_file))
        jpg_images.append(filename_get_name(each_file))
    for each_file in raw_files:
        images.append(filename_get_name(each_file))
        raw_images.append(filename_get_name(each_file))

    #Remove duplicate names
    images = set(images)
    images = list(images)

    #Return list has to bo sorted by file names
    images.sort()

    stats = []
    for each_image in images:
        is_in_final = each_image in final_images
        is_in_jpg = each_image in jpg_images
        is_in_raw = each_image in raw_images

        stat = dict(image=each_image, final=is_in_final,
            jpg=is_in_jpg, raw=is_in_raw)
        stats.append(stat)

    return stats


def get_status2(path):
    """
    Returns a list (sorted by name) of dictionaries with the status about a
    task in sub folder 'path', based by the image name. Example for return:
        return [dict(image='image1', final=False, jpg=True, raw=True,
            location=dict(lat='54.318340N', lon='18.428409E')
            title='Lonely man in the park' )]
        name: Image name without suffix
        final, jpg, raw: True, if a file of this image is this subfolder
        title: title of the final image
    path must be a subdir
    """
    path_final = path + '/' + DIR_FINAL
    path_jpg = path + '/' + DIR_JPG
    path_raw = path + '/' + DIR_RAW
    dirs = os.listdir(path)

    if DIR_FINAL in dirs:
        final_files = os.listdir(path_final)
    else:
        final_files = []
    if DIR_JPG in dirs:
        jpg_files = list_jpg(path_jpg)
    else:
        jpg_files = []
    if DIR_RAW in dirs:
        raw_files = list_raw(path_raw)
    else:
        raw_files = []

    images = []
    final_images = []
    jpg_images = []
    raw_images = []
    titles = dict()
    locations = dict()

    for each_file in jpg_files:
        images.append(filename_get_name(each_file))
        jpg_images.append(filename_get_name(each_file))
        title = image_get_title(path + '/' + DIR_JPG + '/' + each_file)
        titles[filename_get_name(each_file)] = title
        location_dict = image_get_location(path + '/' + DIR_JPG + '/'
            + each_file)
        locations[filename_get_name(each_file)] = location_dict

    for each_file in raw_files:
        images.append(filename_get_name(each_file))
        raw_images.append(filename_get_name(each_file))
        #Up to now, we don't read side car files (xmp)
        titles[filename_get_name(each_file)] = None
        location_dict = image_get_location(path + '/' + DIR_RAW + '/'
            + each_file)
        locations[filename_get_name(each_file)] = location_dict

    for each_file in final_files:
        images.append(filename_get_name(each_file))
        final_images.append(filename_get_name(each_file))
        title = image_get_title(path + '/' + DIR_FINAL + '/' + each_file)
        titles[filename_get_name(each_file)] = title
        location_dict = image_get_location(path + '/' + DIR_FINAL + '/'
            + each_file)
        locations[filename_get_name(each_file)] = location_dict

    #Remove duplicate names
    images = set(images)
    images = list(images)

    #Return list has to bo sorted by file names
    images.sort()

    stats = []
    #print('get_status2: titles=' + str(titles))
    #print('get_status2: images=' + str(images))
    #print('get_status2: locations=' + str(locations))
    for each_image in images:
        is_in_final = each_image in final_images
        is_in_jpg = each_image in jpg_images
        is_in_raw = each_image in raw_images

        stat = dict(image=each_image, final=is_in_final,
            jpg=is_in_jpg, raw=is_in_raw, title=titles[each_image],
            location=locations[each_image])
        stats.append(stat)

    return stats


def image_get_location(filename):
    """
    Returns the human readable geo location as dictionary with two keys lat
    and lon of an image, if exists, otherwise None.
    Location must be stored in Exif.GPSInfo.GPSLatitude and
    Exif.GPSInfo.GPSLatitudeRef. Key Xmp.exif.GPSLatitude
    is not supported. Height not supported.
    Up to now, sidecar files (XMP) are not supported.
    Example
        return dict(lan=1.0, lat=49,54.318340N)
    """
    #lat_value = image_get_tag(filename, 'Xmp.exif.GPSLatitude')
    lat_value = image_get_gps_tag(filename, 'Exif.GPSInfo.GPSLatitude')
    #print('image_get_location() lat ' + filename + ' ' + str(lat_value))
    if lat_value is None:
        return None

    (key, sep, lat_value) = str(lat_value).partition(',')

    lon_value = image_get_gps_tag(filename, 'Exif.GPSInfo.GPSLongitude')
    #print('image_get_location() lon ' + filename + ' ' + str(lon_value))
    if lon_value is None:
        return None

    (key, sep, lon_value) = str(lon_value).partition(',')

    ret = dict(lat=lat_value.replace('\n', ''),
        lon=lon_value.replace('\n', ''))
    #print('image_get_location() ' + filename + ' ' + str(ret))

    return ret


def image_get_gps_tag(filename, tagname):
    """
    Reads the GPS data of the given file and returns the value as string.
    Returns None, if not found.
    Adds both tags tagname and tagnameRef together: e.g. returns values space
    separated values from GPSLatitudeRef and GPSLatitude
    For example:
        image_get_gps_tag('img01.jpg', 'GPSLatitude')
        return 'Norden 50deg 7.46417'
    """
    cmd = 'exiv2 -pt -K {} {}'.format(tagname, filename)
    try:
        b = subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                shell=True,
                universal_newlines=True)
    except subprocess.CalledProcessError:
        #print('image_get_gps_tag() exiv2 failed for {}'.format(cmd))
        return None

    parts = str(b).split(' ')
    if len(parts) < 3:
        return None

    value1 = '{} {}'.format(parts[-3], parts[-2])

    cmd = 'exiv2 -pt -K {}Ref {}'.format(tagname, filename)
    try:
        b = subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                shell=True,
                universal_newlines=True)
    except subprocess.CalledProcessError:
        #print('image_get_gps_tag() exiv2 failed for {}'.format(cmd))
        return None

    parts = str(b).split(' ')
    if len(parts) < 3:
        return None

    value2 = '{} {}'.format(value1, parts[-2])

    #print('image_get_gps_tag return=' + str(value2))
    return str(value2)


def image_get_xmp_tag(filename, tagname):
    """
    Reads the xmp-exif data of the given file and returns the value as string.
    Returns None, if not found.
    """
    try:
        b = subprocess.check_output(
                'exiv2 -PXt -K ' + tagname + ' ' + filename,
                stderr=subprocess.STDOUT,
                shell=True,
                universal_newlines=True)
    except subprocess.CalledProcessError:
        #print('exiv2 failed for ' + filename)
        return None

    #print('image_get_title return=' + title)

    return str(b)


def image_get_time(filename):
    """
    Reads the exif date and time of the given file and returns the value as
    string in format yyyymmtt-hhmmss
    Returns None, if not found.
    Example:
        return '20161231-235959'
    """
    #print('image_get_time() filename=' + filename)
    try:
        b = subprocess.check_output(
               # 'exiv2 -K Exif.Photo.DateTimeOriginal -Pt '
                'exiv2 -Pt -g xif.Photo.DateTimeOriginal '
                + filename,
                stderr=subprocess.STDOUT,
                shell=True,
                universal_newlines=True)
    #except subprocess.CalledProcessError as err:
    except subprocess.CalledProcessError:
        #print(str(err))
        return None
    #print('image_get_time(): ' + str(b))

    parts = str(b).split(' ')
    if parts is None:
        return None

    if len(parts) < 2:
        return None

    ret = parts[0] + '-' + parts[1]
    ret = ret.replace(':', '')
    ret = ret.replace('\n', '')

    return ret


def image_get_model(filename):
    """
    Reads the exif model of the given file and returns the value as string
    Returns None, if not found.
    Example:
        return 'X-E2S'
    """
    #print('image_get_time() filename=' + filename)
    try:
        b = subprocess.check_output(
                'exiftool -model '
                + filename,
                stderr=subprocess.STDOUT,
                shell=True,
                universal_newlines=True)
    #except subprocess.CalledProcessError as err:
    except subprocess.CalledProcessError:
        #print(str(err))
        return None
    #print('image_get_time(): ' + str(b))

    parts = str(b).split(': ')
    if parts is None:
        return None

    if len(parts) < 2:
        return None

    ret = parts[1]
    ret = ret.replace('\n', '')

    return ret


def image_get_title(filename):
    """
    Returns the title of an image, if exists, otherwise  None.
    """
    b = image_get_xmp_tag(filename, 'Xmp.dc.title')
    if b is None:
        return None

    #Xmp.dc.title contains lang='x-default' My title of the image/n
    (lang, sep, title) = str(b).partition(' ')

    return title[0:-1]


def get_images(path):
    """
    path: absolut path of an dictionory
    Returns list with image-dictionary
    """
    ret = []
    for each_file in os.listdir(path):
        #print('get_images: ' + each_file)
        ret.extend(get_image(path + '/' + each_file))

    return ret


def get_image(file_path):
    """
    file_path: absolut path of the image file
    Returns dictionary with meta data of the file.
        path: absolut path of the file   '/images'
        file: file name                  'image01.JPG'
        image: image name                'image01'
        type: image type or None          TYPE_JPG
        location: dictionary or None     'dict(lon='1.1', lat='2.2')
        title: title or None             'Old man in the park'
    Example:
        return dict(path='/images', file='img01.jpg',
            title='old man in the park',
            location=dict(lon='1.1', lat='2.2'))
    In error case, None will be returned.
    """
    if file_path is None:
        return None

    stat = os.stat(file_path)
    if stat is None:
        return None

    meta = dict()
    meta['path'] = path_get_parent(file_path)
    meta['file'] = path_get_subdir(file_path)
    meta['image'] = filename_get_name(file_path)
    meta['type'] = filename_get_type(file_path)
    meta['location'] = None
    meta['title'] = None

    print('get_image: ' + str(meta))
    return meta


def show_in_summary(path):
    """
    Reports a short summary about inbox or import (sub folder 'path').
    path must be a fow relative subdir
    """
    stats = get_status2(path)
    dirs = os.listdir(path)

    if not DIR_JPG in dirs:
        print('Subdirectory missing: ' + DIR_JPG)
    if not DIR_RAW in dirs:
        print('Subdirectory missing: ' + DIR_RAW)

    print('Files in subdirs: ' +
        str(len([s for s in stats if s['jpg']])) + ' jpgs, ' +
        str(len([s for s in stats if s['raw']])) + ' raws.')


def get_path(subdir):
    """
    Creates an absolute path to the given relative path
    for the fow. The actual directory must be within an fow.
    subdir may not start or end with an '/'.
    Returns String with full path without ending '/'
    Example:
    get_path('02_Progress')
        return '/home/chris/myfow/02_Progress'
    """
    if subdir is None or len(subdir) == 0:
        return get_fow_root()

    if len(subdir) > 1 and subdir[-1] == '/':
        subdir = subdir[0:-1]

    return get_fow_root() + subdir


def show_tasks():
    """
    Reports infos about all tasks.
    """
    actual = task.get_actual()
    dir02 = os.listdir(get_path(DIR_02))
    dir02.sort()
    for each_folder in dir02:
        print(' ' + each_folder)
        tasks = os.listdir(get_path(DIR_02) + '/' + each_folder)
        tasks.sort()
        for each_task in tasks:
            stats = get_status2(get_path(DIR_02) + '/' + each_folder + '/'
                + each_task)
            jpgs = len([s for s in stats if s['jpg']])
            raws = len([s for s in stats if s['raw']])
            finals = len([s for s in stats if s['final']])
            if jpgs == 0:
                jtext = '---'
            else:
                jtext = '{:>3}'.format(str(jpgs))
            if raws == 0:
                rtext = '---'
            else:
                rtext = '{:>3}'.format(str(raws))
            if finals == 0:
                ftext = '---'
            else:
                ftext = '{:>3}'.format(str(finals))

            if actual['folder'] == each_folder and \
                actual['name'] == each_task:
                start = '*    '
            else:
                start = '     '

            print(start + jtext + ' ' + rtext + ' ' + ftext + ' '
                + str(each_task))


def show_tasks_summary():
    """
    Reports short infos about all tasks.
    """
    for each_folder in os.listdir(get_path(DIR_02)):
        jpgs = 0
        raws = 0
        finals = 0
        tasks = 0
        for each_task in os.listdir(get_path(DIR_02) + '/' + each_folder):
            stats = get_status2(get_path(DIR_02) + '/' + each_folder + '/'
                + each_task)
            tasks += 1
            jpgs += len([s for s in stats if s['jpg']])
            raws += len([s for s in stats if s['raw']])
            finals += len([s for s in stats if s['final']])

        print(each_folder + ': ' + str(tasks) + ' tasks with ' + str(jpgs)
            + ' jpgs, ' + str(raws) + ' raws, ' + str(finals) + ' finals.')


def show_in(path):
    """
    Reports infos about import or inbox (sub folder 'path').
    Path must be relative subdir
    """

    stats = get_status2(path)

    for each_stat in stats:
        if each_stat['jpg']:
            jpg = 'j'
        else:
            jpg = '-'
        if each_stat['raw']:
            raw = 'r'
        else:
            raw = '-'

        print(jpg + raw + ' ' + each_stat['image'])


def show_task_summary(path):
    """
    Reports a short summary about a task in sub folder 'path'.
    """
    stats = get_status2(path)
    dirs = os.listdir(path)

    if not DIR_FINAL in dirs:
        print('Subdirectory missing: ' + DIR_FINAL)
    if not DIR_JPG in dirs:
        print('Subdirectory missing: ' + DIR_JPG)
    if not DIR_RAW in dirs:
        print('Subdirectory missing: ' + DIR_RAW)

    print('Files in subdirs: ' +
        str(len([s for s in stats if s['jpg']])) + ' jpgs, ' +
        str(len([s for s in stats if s['raw']])) + ' raws, ' +
        str(len([s for s in stats if s['final']])) + ' finals.')


def show_task(path, final_only):
    """
    Reports infos about a task in sub folder 'path'.
    final_only: If True, just final directory is shown
    """

    stats = get_status2(path)
    #print('show_task() ' + str(stats))
    name_col_len = 15

    for each_stat in stats:
        #print('show_task() ' + str(each_stat))
        #Column length for image name
        if len(each_stat['image']) > name_col_len:
            name_col_len = len(each_stat['image'])
        if each_stat['jpg']:
            jpg = 'j'
        else:
            jpg = '-'
        if each_stat['final']:
            final = 'f'
        else:
            final = '-'
        if each_stat['raw']:
            raw = 'r'
        else:
            raw = '-'
        if each_stat['title']:
            title_flag = 't'
            title = each_stat['title']
        else:
            title_flag = '-'
            title = ''
        if each_stat['location'] is None:
            location_flag = '-'
        else:
            location_flag = 'g'

        #print('show_task() ' + str(location_flag))

        formatting = '{}{}{}{}{} {:<' + str(name_col_len) + '} {}'
        if final_only is False or (final_only is True and final == 'f'):
            print(formatting.format(jpg, raw, final, title_flag, location_flag,
                each_stat['image'], title))


def _exist_dir(dir_name):
    """
    Returns True, if the directory exists. dir_name may not be a path
    """
    dirs = os.listdir('.')
    #print('dirs=' + str(dirs))
    for dir in dirs:
        if dir == dir_name:
            return True
    return False


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

    #If no option, add a none one. Maybe this is a bad idea
    #if len(names) + len(shorts) == 0:
    #   names.append('none')

    return dict(names=names, shorts=shorts, args=args)


def setConfig(key, value):
    """
    Updates or creates the specific value in the config pickle.
    Returns True, if item could be updated, otherwise False.
    """
    settings = readConfig()
    settings[key] = value

    return writeConfig(settings)


def writeConfig(settings):
    """
    Rewrites complete config pickle. Do set a specific config value,
    use setConfig()
    Returns True if setting.pickle could be written, otherwise Talse
    """
    try:
        with open(get_fow_root() + '/.fow/setting.pickle', 'wb') as data:
            pickle.dump(settings, data)
    except IOError as err:
        print('Could not save settings to setting.pickle: ' + str(err))
        return False
    return True

