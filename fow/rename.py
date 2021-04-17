import os

import sys

from plump import DIR_JPG, list_jpg, image_get_time, DIR_RAW, list_raw, DIR_VIDEO, list_video, video_get_time, \
    progress_prepare


def analyse(src_path, dest_path):
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
    files = list_jpg(src_path + '/' + subdir)
    index = 0
    progress = progress_prepare(len(files), 'Processing', subdir)
    for each in files:
        # print(str(image_get_time(path)))
        index += 1
        sys.stdout.write(progress['back'] + progress['formatting'].format(str(index)))
        sys.stdout.flush()
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
    sys.stdout.write('\n')

    subdir = DIR_RAW
    files = list_raw(src_path + '/' + subdir)
    index = 0
    progress = progress_prepare(len(files), 'Processing', subdir)
    for each in files:
        # print(str(image_get_time(path)))
        index += 1
        sys.stdout.write(progress['back'] + progress['formatting'].format(str(index)))
        sys.stdout.flush()
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
    sys.stdout.write('\n')

    subdir = DIR_VIDEO
    files = list_video(src_path + '/' + subdir)
    index = 0
    progress = progress_prepare(len(files), 'Processing', subdir)
    for each in files:
        # print(str(image_get_time(path)))
        index += 1
        sys.stdout.write(progress['back'] + progress['formatting'].format(str(index)))
        sys.stdout.flush()
        old_name = each
        time_str = video_get_time(src_path + '/' + subdir + '/' + each)
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

    sys.stdout.write('\n')

    return dict(src_path=src_path, dest_path=dest_path, files=ret)


def test(analysis, verbose, force):
    """
    Dry run of rename command.
    verbose - boolean
    """
    cnt_ok = 0
    cnt_nok = 0
    for each in analysis['files']:
        if not each['exists']:
            cnt_ok += 1
            if verbose:
                status = '  OK  '
                print(status + each['subdir'] + ' ' + each['old_name']
                      + ' --> ' + each['new_name'])
        else:
            cnt_nok += 1
            if verbose:
                if force:
                    status = '! OVR '
                    print(status + each['subdir'] + '/' + each['new_name']
                          + ' exists')
                else:
                    status = '! NOK '
                    print(status + each['subdir'] + ' '
                          + 'File already exists: ' + each['new_name'])

    if cnt_nok > 0:
        if force:
            print("{0}/{1} file(s) already exists an will be overwritten!"
                  .format(cnt_nok, len(analysis['files'])))
        else:
            print(("{0}/{1} file(s) already exists. Remove them first from " +
                   "destination or overwrite file(s) by using --force.")
                  .format(cnt_nok, len(analysis['files'])))
    else:
        print("{0} files will be moved and renamed.".format(cnt_ok))


def do(analysis, verbose, force):
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
            # print(status + each['subdir'] + ' ' + each['old_name']
            # + ' --> ' + each['new_name'])
            print('{0}/{1} file(s) moved.'.format(cntMoved,
                                                  len(analysis['files'])))
            return

    if cntOverwritten > 0:
        print('{0} file(s) moved, which {1} were overwritten.'
              .format(cntMoved, cntOverwritten))
    else:
        print('{0} file(s) moved.'.format(cntMoved))