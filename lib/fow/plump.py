# -*- coding: utf-8 -*-
import pickle
import os
import sys

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

#####################################################################
# Conventions:
# - A 'path' is an absolute path within the system. On the other
#   hand is a 'subdir' a subdirectory within a fow.
#####################################################################


# configuration file for this fow installation, read once with readFowConfig()
fow_config = None


#def get_subdir(path):
    #"""
    #Extracts subdir from the given path within a fow.
    #Returns None, if path is not within a fow.
    #Example:
    #get_subdir('/home/chris/myfow/02_Progress/weekly')
        #return '02_Progress/weekly'
    #"""
    #if get_fow_root() is None:
        #return None

    #return path.replace(get_fow_root(),'')


def get_fow_root():
    """
    The root directory of a fow must have a .fow directory.
    Returns String with path of the root directory of this fow with
    and ending '/'.
    Or, if actual directory is not within a fow, None will be returned.
    """
    actual = os.getcwd()
    root = None
    parts = [x for x in actual.split('/') if len(x) > 0]
    #print('parts=' + str(parts))

    paths = []
    tpath = '/'
    for i in range(0, len(parts)):
        tpath = tpath + parts[i] + '/'
        paths.append(tpath)
    #print(str(paths))

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
    Returns a dictionary with setting.pickle.
    """
    settings = dict()
    try:
        with open(get_fow_root() + '/' + DIR_FOW + '/setting.pickle',
                    'rb') as data:
            settings = pickle.load(data)
    except:
        print('setting.pickle not found but will be created with next writing.')
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


def list_jpg(path):
    """
    Like os.listdir, a list with jpg files will be returned.
    Supported suffixes are jpg, JPG.
    """
    suffixes = ['jpg', 'JPG']
    return [f for f in os.listdir(path) for s in suffixes
        if filename_get_suffix(f) == s]


def list_raw(path):
    """
    Like os.listdir, a list with raw files will be returned.
    Supported suffixes are jpg, JPG.
    """
    suffixes = ['RAW', 'raw', 'RAF', 'raf', 'cr2', 'CR2']
    return [f for f in os.listdir(path) for s in suffixes
        if filename_get_suffix(f) == s]


def get_status(path):
    """
    Returns a list of dictionaries with the status about a task in
    sub folder 'path', based by the image name. Example for return:
        return [dict(image='image1', final=False, jpg=True, raw=True )]
        name: Image name without suffix
        final, jpg, raw: True, if a file of this image is this subfolder
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

    stats = []
    for each_image in images:
        is_in_final = each_image in final_images
        is_in_jpg = each_image in jpg_images
        is_in_raw = each_image in raw_images
        stat = dict(image=each_image, final=is_in_final,
            jpg=is_in_jpg, raw=is_in_raw)
        stats.append(stat)

    return stats


def show_in_summary(path):
    """
    Reports a short summary about inbox or import (sub folder 'path').
    path must be a fow relative subdir
    """
    stats = get_status(path)
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

    return get_fow_root() + '/' + subdir


def show_tasks():
    """
    Reports infos about all tasks.
    """
    actual = getActualTask()
    for each_folder in os.listdir(get_path(DIR_02)):
        print(' ' + each_folder)
        for each_task in os.listdir(get_path(DIR_02) + '/' + each_folder):
            stats = get_status(get_path(DIR_02) + '/' + each_folder + '/'
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
            stats = get_status(get_path(DIR_02) + '/' + each_folder + '/'
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

    stats = get_status(path)

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
    stats = get_status(path)
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


def show_task(path):
    """
    Reports infos about a task in sub folder 'path'.
    """

    stats = get_status(path)

    for each_stat in stats:
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

        print(jpg + raw + final + ' ' + each_stat['image'])


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


def getActualTask():
    """
    Returns dictionary with keys 'task' (foldername/taskname),
    'name' (task name), 'folder' (folder name)
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

