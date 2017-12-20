import os

import task
from plump import get_short_status, DIR_JPG, DIR_RAW, DIR_VIDEO, get_exif_status, get_path, DIR_02, DIR_FINAL, \
    get_exif_status_final_only


def in_summary(path):
    """
    Reports a short summary about inbox or import (sub folder 'path').
    path must be a fow relative subdir
    """
    stats = get_short_status(path)
    # dirs = os.listdir(path)
    dirs = [f.name for f in os.scandir(path) if f.is_dir()]

    if not DIR_JPG in dirs:
        print('Subdirectory missing: ' + DIR_JPG)
    if not DIR_RAW in dirs:
        print('Subdirectory missing: ' + DIR_RAW)
    if not DIR_VIDEO in dirs:
        print('Subdirectory missing: ' + DIR_VIDEO)

    print('Files in subdirs: ' +
          str(len([s for s in stats if s['jpsg']])) + ' jpgs, ' +
          str(len([s for s in stats if s['raw']])) + ' raws, ' +
          str(len([s for s in stats if s['video']])) + ' videos.')


def show_in(path):
    """
    Reports infos about import or inbox (sub folder 'path').
    Path must be relative subdir
    """

    stats = get_exif_status(path)

    name_col_len = 1
    # Column length for image name
    for each_stat in stats:
        if len(each_stat['image']) > name_col_len:
            name_col_len = len(each_stat['image'])

    for each_stat in stats:
        # print('show_task() ' + str(each_stat))
        if each_stat['jpg']:
            jpg = 'j'
        else:
            jpg = '-'
        if each_stat['raw']:
            raw = 'r'
        else:
            raw = '-'
        if each_stat['video']:
            video = 'v'
        else:
            video = '-'
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

        # print('show_task() ' + str(location_flag))

        formatting = '{}{}{}{}{} {:<' + str(name_col_len) + '} {}'
        print(formatting.format(jpg, raw, video, title_flag, location_flag,
                                each_stat['image'], title))


def tasks_summary():
    """
    Reports short infos about all tasks.
    """
    for each_folder in [f.name for f in os.scandir(get_path(DIR_02)) if f.is_dir()]:
        jpgs = 0
        raws = 0
        finals = 0
        tasks = 0
        # for each_task in os.listdir(get_path(DIR_02) + '/' + each_folder):
        for each_task in [f.name for f in os.scandir(get_path(DIR_02) + '/' + each_folder) if f.is_dir()]:
            stats = get_short_status(get_path(DIR_02) + '/' + each_folder + '/'
                                     + each_task)
            tasks += 1
            jpgs += len([s for s in stats if s['jpg']])
            raws += len([s for s in stats if s['raw']])
            finals += len([s for s in stats if s['final']])

        print(each_folder + ': ' + str(tasks) + ' tasks with ' + str(jpgs)
              + ' jpgs, ' + str(raws) + ' raws, ' + str(finals) + ' finals.')


def tasks():
    """
    Reports infos about all tasks.
    """
    actual = task.get_actual()
    # dir02 = os.listdir(get_path(DIR_02))
    dir02 = [f.name for f in os.scandir(get_path(DIR_02)) if f.is_dir()]
    dir02.sort()
    for each_folder in dir02:
        print(' ' + each_folder)
        # tasks = os.listdir(get_path(DIR_02) + '/' + each_folder)
        tasks = [f.name for f in os.scandir(get_path(DIR_02) + '/' + each_folder) if f.is_dir()]

        tasks.sort()
        for each_task in tasks:
            stats = get_short_status(get_path(DIR_02) + '/' + each_folder + '/'
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


def task_summary(path):
    """
    Reports a short summary about a task in sub folder 'path'.
    """
    stats = get_short_status(path)
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

    if final_only:
        stats = get_exif_status_final_only(path)
    else:
        stats = get_exif_status(path)

    # print('show_task() ' + str(stats))
    name_col_len = 1
    # Column length for image name
    for each_stat in stats:
        if len(each_stat['image']) > name_col_len:
            name_col_len = len(each_stat['image'])

    for each_stat in stats:
        # print('show_task() ' + str(each_stat))
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
            title = '-'

        if each_stat['description']:
            description_flag = 'd'
            description = each_stat['description']
        else:
            description_flag = '-'
            description = '-'

        if each_stat['location'] is None:
            location_flag = '-'
        else:
            location_flag = 'g'

        # print('show_task() ' + str(location_flag))

        formatting = '{}{}{}{}{}{} {:<' + str(name_col_len) + '} {} / {}'
        if final_only is False or (final_only is True and final == 'f'):
            print(formatting.format(jpg, raw, final, title_flag, description_flag, location_flag,
                                    each_stat['image'], title, description))
