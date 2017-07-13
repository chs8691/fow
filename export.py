import os
import shutil
import sys
import task
from plump import list_jpg, string_get_max_length
from plump import DIR_FINAL
from plump import time_readable


def analyse(_task, _dest):
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
    src_dir = task.get_task_path(task.get_actual()['task']) + '/' + DIR_FINAL
    files = list_jpg(src_dir)
    # for file in files:
    # print('export_analyse() file=' + str(file) + ' '
    # + time_readable(os.path.getatime(src_dir + '/' + file)))

    ret = []
    for file in files:
        exists = os.path.exists(_dest + '/' + file)
        if exists:
            dst_time = os.path.getatime(_dest + '/' + file)
        else:
            dst_time = None

        ret.append(dict(
            name=file,
            exists=exists,
            src_time=os.path.getatime(src_dir + '/' + file),
            dst_time=dst_time
        ))

    # print('export_analyse() ret=' + str(ret))

    return ret


def test(analysis, src_dir, dest):
    """
    Prints an export test run.
    """
    # print(str(analysis))
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


def copy(analysis, src_dir, dest):
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


def dictlist_get_max_length(analysis, fieldname):
    """
    Returns max string lenght for 'name' in list of dicts.
    """
    names = []
    for item in analysis:
        names.append(item[fieldname])

    return string_get_max_length(names)