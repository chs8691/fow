import os

from plump import DIR_JPG, DIR_RAW, DIR_VIDEO, list_jpg, list_raw, list_video, scan_tree, get_max_name_length, \
    load_test_print, load_execute


def analyse(_src, _dest_root):
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
    # print('load_analyse() _src={0}'.format(_src))

    dest_jpg = '{0}/{1}'.format(_dest_root, DIR_JPG)
    dest_raw = '{0}/{1}'.format(_dest_root, DIR_RAW)
    dest_video = '{0}/{1}'.format(_dest_root, DIR_VIDEO)
    files_jpg = list_jpg(dest_jpg)
    files_raw = list_raw(dest_raw)
    files_video = list_video(dest_video)

    values = dict(jpg=[], raw=[], video=[])
    scan_tree(_src, values)
    # print('load_analyse() files_video={0}'.format(str(files_video)))

    # Add existing info
    for each_value in values['jpg']:
        # print('each_value {0}'.format(str(each_value)))
        each_value['exist'] = False
        each_value['desttime'] = None
        for each in [e for e in files_jpg if each_value['file'] == e]:
            each_value['exist'] = True
            each_value['desttime'] = os.path.getatime('{0}/{1}'.format(
                dest_jpg, each))

    for each_value in values['raw']:
        # print('each_value {0}'.format(str(each_value)))
        each_value['exist'] = False
        each_value['desttime'] = None
        for each in [e for e in files_raw if each_value['file'] == e]:
            each_value['exist'] = True
            each_value['desttime'] = os.path.getatime('{0}/{1}'.format(
                dest_raw, each))

    for each_value in values['video']:
        # print('each_value {0}'.format(str(each_value)))
        each_value['exist'] = False
        each_value['desttime'] = None
        for each in [e for e in files_video if each_value['file'] == e]:
            each_value['exist'] = True
            each_value['desttime'] = os.path.getatime('{0}/{1}'.format(
                dest_video, each))

    # print('values {0}'.format(str(values)))

    return values


def test(analysis, src, dest, options):
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

    # max_name_len = 30
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


def do(analysis, src, dest, options):
    """
    Executes command load.
    """
    # print('load_do() analysis={0}'.format(str(analysis)))
    # print('load_do() options={0}'.format(str(options)))
    # print('load_do() dest={0}'.format(str(dest)))
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