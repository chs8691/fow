# -*- coding: utf-8 -*-
import os
import shutil
import subprocess
import time
import sys

DIR_00 = '00_Inbox'
DIR_01 = '01_Import'
DIR_02 = '02_Progress'
DIR_FOW = '.fow'
DIR_VIDEO = 'video'
DIR_JPG = 'jpg'
DIR_RAW = 'raw'
DIR_FINAL = 'final'
DIR_WORK = 'work'
VERSION = '1.1.6 Build 201712201517'
BACKUP_PATH = 'backup.path'
TASK = 'task'
TYPE_RAW = 'raw'
TYPE_JPG = 'jpg'
TYPE_TIF = 'tif'


# Groups all exports destinations together. The have to start with 'export.'
EXPORT_PREFIX = 'export'
# Groups all gpx keys together. The have to start with 'gpx.'
GPS_PREFIX = 'gps'

# Key for path to gps track folder
GPS_TRACK_PATH = 'gps.tracks'

# Groups all load destinations together. The have to start with 'load.'
LOAD_PREFIX = 'load'

#####################################################################
# Conventions:
# - A 'path' is an absolute path within the system. On the other
#   hand is a 'subdir' a subdirectory within a fw.
#####################################################################


def progress_prepare(max_index, action, what):
    """
    Prepares progress output and writes to stdout. Returns dict with
    needed values. Output: 'Processing <what> <max_index>: 0'. To update
    progress use:
        sys.stdout.write(ret['back'] + ret['formatting'].format(str(index)))
        sys.stdout.flush()
    Parameters
    ----------
    max_lines: Integer
        Progress maximum, e.g. '123'
    action: String
        Name of the action, e.g. 'Processing', should start in upper case
    what: String
        Output text, e.g. 'RAW'
    :return: Dictionary with keys 'back' and 'formatting' for output
    Example
    -------
    progress_prepare(123, 'RAW')
    return dict(back=3, formatting=' {:<' + str(len(max_index)) + '}'
    """
    digits = len(str(max_index))
    formatting = ' {:<' + str(digits) + '}'
    formatting2 = '{} {} {:<' + str(digits) + '}:' + formatting
    sys.stdout.write(formatting2.format(action, what, str(max_index), str(0)))
    back = '\b'
    for i in str(max_index):
        back += '\b'

    return dict(back=back, formatting=formatting)


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
    for each in file_names:
    """
    ret = dict(done=0, overwritten=0, error=0, ignored=0)

    # Progress output 'Processing RAW 123: 1'
    index = 0
    progress = progress_prepare(len(analysis),  'Processing', subdir)

    for each in analysis:
        index += 1
        sys.stdout.write(progress['back'] + progress['formatting'].format(str(index)))
        sys.stdout.flush()

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

    sys.stdout.write('\n')
    return ret


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
    # print('scan_tree() dir={0}'.format(str(path)))
    # dirs = [d for d in os.listdir(path) if os.path.isdir('{0}/{1}'
    #                                                      .format(path, d))]
    dirs = [d.name for d in os.scandir(path) if d.is_dir()]

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
    # print('parts=' + str(parts))

    paths = []
    tpath = '/'
    for i in range(0, len(parts)):
        tpath = tpath + parts[i] + '/'
        # print(str(paths))
        paths.append(tpath)

    for i in range(0, len(paths) - 1):
        # print(paths[len(paths) - 1 - i])
        path = paths[len(paths) - 1 - i]
        files = [x for x in os.listdir(path)
                 if x == DIR_FOW]
        if len(files) == 1:
            return path

    # No .fw found
    return None


def is_fow_root(path):
    """
    Return True, if the path is the root directory of a fow,
    otherwise False.
    """
    for each_file in os.listdir(path):
        # print('each_file=' + each_file)
        if each_file == '.fow':
            return True

    return False


def is_fow():
    """
    If the actual directory is within a fow, True will be returned
    silently. Otherwise a message wil be printed and False will be returned.
    """
    # print(str(get_fow_root()))
    if get_fow_root() is None:
        print('Actual path is not within a fow. See "help init" how to ' +
              'create a new fow here or change your actual directory ' +
              'to a fow.')
        return False

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
    # print('_actual=' + str(_actual))
    ret = _actual.copy()
    founds = set()
    # print('copy=' + str(ret))
    for short in _actual['shorts']:
        # print('short=' + short)
        for path in rules:
            # print('path=' + str(path))
            for node in path:
                # print('node=' + str(node))
                if short == node['atom']['short']:
                    # print('found short ' + short)
                    if not node['atom']['name'] in ret['names']:
                        ret['names'].append(node['atom']['name'])
                    # Delete only one time
                    if short in ret['shorts']:
                        founds.add(short)
                        # ret['shorts'].remove(short)

    # print('founds=' + str(founds))

    # print('ret=' + str(ret))
    return ret


def copy_missing_jpgs(src_dir, dest_dir, dry_run):
    """
    Copies all jpgs from source directory to destination directory, if they
    didn't already exist there.
    src_dir is the /row directory with raws to move.
    dest_dir is the target directory.
    """
    # print('src=' + src_dir)
    # print('dst=' + dest_dir)

    srcs = get_files_as_dict(list_jpg(src_dir))
    # print(str(srcs))

    dests = get_files_as_dict(list_jpg(dest_dir))
    # print(str(dests))

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

    # print(str(files))

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
    # print('files=' + str(files))
    ret = []
    for each_file in files:
        ret.append(dict(filename=each_file,
                        name=filename_get_name(each_file),
                        suffix=filename_get_suffix(each_file)))

    # print(str('ret=' + str(ret)))
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


def get_exif_status(path):
    """
    Returns a list (sorted by name) of dictionaries with the status incl. EXIF information about
    all image files in sub folder 'path', based by the image name. Example for return:
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
    path_video = path + '/' + DIR_VIDEO
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
    if DIR_VIDEO in dirs:
        video_files = list_video(path_video)
    else:
        video_files = []

    images = []
    final_images = []
    jpg_images = []
    raw_images = []
    video_images = []
    titles = dict()
    locations = dict()
    descriptions = dict()

    jpg_exifs = images_get_exifs('{}/{}'.format(path, DIR_JPG), jpg_files)
    raw_exifs = images_get_exifs('{}/{}'.format(path, DIR_RAW), raw_files)
    video_exifs = images_get_exifs('{}/{}'.format(path, DIR_VIDEO), video_files)
    final_exifs = images_get_exifs('{}/{}'.format(path, DIR_FINAL), final_files)
    # print('get_status2() {}'.format(str(jpg_exifs)))

    # for each_file in jpg_files:
    #     images.append(filename_get_name(each_file))
    #     jpg_images.append(filename_get_name(each_file))

    for each_exifs in jpg_exifs:
        titles[filename_get_name(each_exifs['name'])] = each_exifs['title']
        descriptions[filename_get_name(each_exifs['name'])] = each_exifs['description']
        locations[filename_get_name(each_exifs['name'])] = each_exifs['gps']
        images.append(filename_get_name(each_exifs['name']))
        jpg_images.append(filename_get_name(each_exifs['name']))

    for each_exifs in raw_exifs:
        titles[filename_get_name(each_exifs['name'])] = each_exifs['title']
        descriptions[filename_get_name(each_exifs['name'])] = each_exifs['description']
        locations[filename_get_name(each_exifs['name'])] = each_exifs['gps']
        images.append(filename_get_name(each_exifs['name']))
        raw_images.append(filename_get_name(each_exifs['name']))

    for each_exifs in video_exifs:
        titles[filename_get_name(each_exifs['name'])] = each_exifs['title']
        descriptions[filename_get_name(each_exifs['name'])] = each_exifs['description']
        locations[filename_get_name(each_exifs['name'])] = each_exifs['gps']
        images.append(filename_get_name(each_exifs['name']))
        video_images.append(filename_get_name(each_exifs['name']))

    for each_exifs in final_exifs:
        titles[filename_get_name(each_exifs['name'])] = each_exifs['title']
        descriptions[filename_get_name(each_exifs['name'])] = each_exifs['description']
        locations[filename_get_name(each_exifs['name'])] = each_exifs['gps']
        images.append(filename_get_name(each_exifs['name']))
        final_images.append(filename_get_name(each_exifs['name']))

    # Remove duplicate names
    images = set(images)
    images = list(images)

    # Return list has to bo sorted by file names
    images.sort()

    stats = []
    for each_image in images:
        is_in_final = each_image in final_images
        is_in_jpg = each_image in jpg_images
        is_in_raw = each_image in raw_images
        is_in_video = each_image in video_images

        stat = dict(image=each_image, final=is_in_final,
                    jpg=is_in_jpg, raw=is_in_raw, video=is_in_video, title=titles[each_image],
                    description=descriptions[each_image],
                    location=locations[each_image])
        stats.append(stat)

    # print('get_status2() {}'.format(str(stats)))
    return stats


def get_exif_status_final_only(path):
    """
    TODO Es kommen nicht die informationen aus jpg und raw/Verzeichnis
    Like get_exif_status, but only for images in final
    Example for return:
        return [dict(image='image1', final=True, jpg=True, raw=True,
            location=dict(lat='54.318340N', lon='18.428409E')
            title='Lonely man in the park' )]
        name: Image name without suffix
        final, jpg, raw: True, if a file of this image is this subfolder
        title: title of the final image
    path must be a subdir
    """
    path_final = path + '/' + DIR_FINAL
    dirs = os.listdir(path)

    if DIR_FINAL in dirs:
        final_files = os.listdir(path_final)
    else:
        final_files = []

    images = []
    final_images = []
    titles = dict()
    locations = dict()
    descriptions = dict()

    final_exifs = images_get_exifs('{}/{}'.format(path, DIR_FINAL), final_files)

    jpg_images = [filename_get_name(f) for f in list_jpg(path + '/' + DIR_JPG)]
    raw_images = [filename_get_name(f) for f in list_raw(path + '/' + DIR_RAW)]
    video_images = [filename_get_name(f) for f in list_video(path + '/' + DIR_VIDEO)]

    for each_exifs in final_exifs:
        titles[filename_get_name(each_exifs['name'])] = each_exifs['title']
        descriptions[filename_get_name(each_exifs['name'])] = each_exifs['description']
        locations[filename_get_name(each_exifs['name'])] = each_exifs['gps']
        images.append(filename_get_name(each_exifs['name']))
        final_images.append(filename_get_name(each_exifs['name']))

    # Remove duplicate names
    images = set(images)
    images = list(images)

    # Return list has to bo sorted by file names
    images.sort()

    stats = []
    for each_image in images:
        is_in_final = each_image in final_images
        is_in_jpg = each_image in jpg_images
        is_in_raw = each_image in raw_images
        is_in_video = each_image in video_images

        stat = dict(image=each_image, final=is_in_final,
                    jpg=is_in_jpg, raw=is_in_raw, video=is_in_video, title=titles[each_image],
                    description=descriptions[each_image],
                    location=locations[each_image])
        stats.append(stat)

    # print('get_status2() {}'.format(str(stats)))
    return stats


def get_short_status(path):
    """
    Returns a list (sorted by name) of dictionaries with the status without EXIF information about
    all image files in sub folder 'path', based by the image name. Example for return:
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
    path_video = path + '/' + DIR_VIDEO
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
    if DIR_VIDEO in dirs:
        video_files = list_video(path_video)
    else:
        video_files = []

    images = []
    final_images = []
    jpg_images = []
    raw_images = []
    video_images = []

    for each in jpg_files:
        images.append(filename_get_name(each))
        jpg_images.append(filename_get_name(each))

    for each in raw_files:
        images.append(filename_get_name(each))
        raw_images.append(filename_get_name(each))

    for each in video_files:
        images.append(filename_get_name(each))
        video_images.append(filename_get_name(each))

    for each in final_files:
        images.append(filename_get_name(each))
        final_images.append(filename_get_name(each))

    # Remove duplicate names
    images = set(images)
    images = list(images)

    # Return list has to bo sorted by file names
    images.sort()

    stats = []
    for each_image in images:
        is_in_final = each_image in final_images
        is_in_jpg = each_image in jpg_images
        is_in_raw = each_image in raw_images
        is_in_video = each_image in video_images

        stat = dict(image=each_image, final=is_in_final,
                    jpg=is_in_jpg, raw=is_in_raw, video=is_in_video)
        stats.append(stat)

    # print('get_status2() {}'.format(str(stats)))
    return stats


def image_write_gps(image_path, gpx_path):
    """
    Update the gps exifs of the image by the given track file.
    Returns True, if gps found in track file, otherwise false
    """

    cmd = 'exiftool -geotag {0} {1} -overwrite_original'.format(gpx_path, image_path)
    # print('image_write_gps() cmd={}'.format(cmd))
    try:
        b = subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.STDOUT,
            universal_newlines=False)
        cmd_ret = str(b)
        cmd_ret = cmd_ret[0:len(cmd_ret) - 1]
        # print('image_write_gps() value={}'.format(str(cmd_ret)))
    except subprocess.CalledProcessError as e:
        # print(str(e))
        return False

    return True


def images_get_exifs(path, file_names):
    """
    Returns a list of dictionaries with all supported exif information for the give files.
    file_names: List with file names without a path
    path: Path to the files
    Example
        return [
        dict(name='img01.jpg', gps=dict(lan=1.0, lat=49,54.318340N), title='A huge tree',
            description='Very short description'
            createdate='2017:06:19 08:16:11',
        ... ]
    """
    ret = []
    # print('Reading images', end='')

    index = 0
    progress = progress_prepare(len(file_names), 'Reading', path)

    for each in file_names:
        index += 1
        sys.stdout.write(progress['back'] + progress['formatting'].format(str(index)))
        sys.stdout.flush()

        cmd = 'exiftool -T -filename -gpslatitude -gpslongitude -title -createdate -description {}/{}'.format(path, each)
        #     print('images_get_exifs() cmd={}'.format(cmd))
        try:
            b = subprocess.check_output(
                cmd,
                shell=True,
                universal_newlines=True)
            cmd_ret = str(b)
            cmd_ret = cmd_ret[0:len(cmd_ret) - 1]
            # print('images_get_exifs() value={}'.format(str(cmd_ret)))
        except subprocess.CalledProcessError as e:
            ret.append(dict(name=each, title=None, gps=None, createdate=None))
            # print(str(e))
            continue

        values = cmd_ret.split('\t')
        # print('images_get_exifs() value_list={}'.format(str(values)))

        # Not really nice and error prone but null values are set to '-', so we have to change this
        if values[4] == '-':
            createdate = None
        else:
            createdate = values[4]

        if values[3] == '-':
            title = None
        else:
            title = values[3]

        if values[5] == '-':
            description = None
        else:
            description = values[5]

        if values[1] == '-' and values[2] == '-':
            gps = None
        else:
            gps = dict(lat=values[1], lon=values[2])

        ret.append(dict(name=values[0], title=title, description=description, gps=gps, createdate=createdate))

    # print('Done.')
    sys.stdout.write('\n')
    sys.stdout.flush()

    return ret


def image_get_exifs(path, file_name):
    """
    Returns a dictionary with all supported exif information for the give file. Non existing attributes will return
    value None.
    file_name: file name without a path
    path: Path to the file
    Example
        return
        dict(name='img01.jpg', gps=dict(lan=1.0, lat=49,54.318340N), title='A huge tree',
            createdate='2017:06:19 08:16:11')
    """
    cmd = 'exiftool -T -filename -gpslatitude -gpslongitude -title -createdate {}/{}'.format(path, file_name)
    #     print('images_get_exifs() cmd={}'.format(cmd))
    try:
        b = subprocess.check_output(
            cmd,
            shell=True,
            universal_newlines=True)
        cmd_ret = str(b)
        cmd_ret = cmd_ret[0:len(cmd_ret) - 1]
        # print('images_get_exifs() value={}'.format(str(cmd_ret)))
    except subprocess.CalledProcessError as e:
        return dict(name=file_name, title=None, gps=None, createdate=None)
        # print(str(e))

    values = cmd_ret.split('\t')
    # print('images_get_exifs() value_list={}'.format(str(values)))

    # Not really nice and error prone but null values are set to '-', so we have to change this
    if values[4] == '-':
        createdate = None
    else:
        createdate = values[4]

    if values[3] == '-':
        title = None
    else:
        title = values[3]

    if values[1] == '-' and values[2] == '-':
        gps = None
    else:
        gps = dict(lat=values[1], lon=values[2])

    return dict(name=values[0], title=title, gps=gps, createdate=createdate)


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
        # print('exiv2 failed for ' + filename)
        return None

    # print('image_get_title return=' + title)

    return str(b)


def image_get_time(filename):
    """
    Reads the exif date and time of the given file and returns the value as
    string in format yyyymmtt-hhmmss
    Returns None, if not found.
    Example:
        return '20161231-235959'
    """
    # print('image_get_time() filename=' + filename)
    try:
        b = subprocess.check_output(
            # 'exiv2 -Pt -g xif.Photo.DateTimeOriginal '
            'exiftool -DateTimeOriginal -T {}'.format(filename),
            stderr=subprocess.STDOUT,
            shell=True,
            universal_newlines=True)
    # except subprocess.CalledProcessError as err:
    except subprocess.CalledProcessError:
        # print(str(err))
        return None
    # print('image_get_time(): ' + str(b))

    parts = str(b).split(' ')
    if parts is None:
        return None

    if len(parts) < 2:
        return None

    ret = parts[0] + '-' + parts[1]
    ret = ret.replace(':', '')
    ret = ret.replace('\n', '')

    # print('image_get_time(): ' + str(b))
    return ret


def video_get_time(filename):
    """
    Reads the exif date and time of the given file and returns the value as
    string in format yyyymmtt-hhmmss
    Returns None, if not found.
    Example:
        return '20161231-235959'
    """
    # print('image_get_time() filename=' + filename)
    try:
        b = subprocess.check_output(
            'exiftool -T -createdate '
            + filename,
            stderr=subprocess.STDOUT,
            shell=True,
            universal_newlines=True)
    # except subprocess.CalledProcessError as err:
    except subprocess.CalledProcessError:
        # print(str(err))
        return None
    # print('image_get_time(): ' + str(b))

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
    # print('image_get_time() filename=' + filename)
    try:
        b = subprocess.check_output(
            'exiftool -model '
            + filename,
            stderr=subprocess.STDOUT,
            shell=True,
            universal_newlines=True)
    # except subprocess.CalledProcessError as err:
    except subprocess.CalledProcessError:
        # print(str(err))
        return None
    # print('image_get_time(): ' + str(b))

    parts = str(b).split(': ')
    if parts is None:
        return None

    if len(parts) < 2:
        return None

    ret = parts[1]
    ret = ret.replace('\n', '')

    return ret


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


def exist_dir(dir_name):
    """
    Returns True, if the directory exists. dir_name may not be a path
    """
    dirs = os.listdir('.')
    # print('dirs=' + str(dirs))
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
        # print('cmds i = ' + cmds[i])
        # print('cmds i = ' + cmds[i][0:2])
        if len(cmds[i]) >= 2 and cmds[i][0:2] == '--':
            names.append(cmds[i][2:])
        elif len(cmds[i]) >= 1 and cmds[i][0] == '-':
            shorts.append(cmds[i][1:])
        else:
            args.append(cmds[i])

    # If no option, add a none one. Maybe this is a bad idea
    # if len(names) + len(shorts) == 0:
    #   names.append('none')

    return dict(names=names, shorts=shorts, args=args)


