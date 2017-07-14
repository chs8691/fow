###############################################################################
# All plump stuff for tasks.
###############################################################################
import os
import config
from plump import list_raw, list_jpg, filename_get_name, get_path, TASK, DIR_02


def get_actual():
    """
    Returns dictionary with keys 'task' (foldername/taskname),
    'name' (task name), 'folder' (folder name), 'path' (absolute path)
    of the actual task or None, if not set.
    """
    try:
        settings = config.read_pickle()
        item = settings[TASK]

        if item is None or item == 'None':
            return None
        else:
            (folder, name) = item.rsplit('/', 1)
            path = get_task_path('{}'.format(item))
            task = {'task': item, 'name': name, 'folder': folder, 'path': path}
            return task
    except:
        print("get_actual() {}".format(str('Exception occurred')))
        return None


def get_task_path(_task):
    """
    Returns String with the absolute path of the task, or None
    if no actual task is set.
    Example:
    get_patch('w/20160101')
        return '/home/chris/fow/02_Progress/w/20160101'
    """
    return get_path(DIR_02 + '/' + _task)


def check_actual():
    """
    Analyse and write error message if actual path is not set or invalid.
    Returns True, if actual task is set and path exists. No print output.
    Returns False and write error message, if task not set or path
    does not exists.
    """
    if get_actual() is None:
        print('No actual task. Use "task --create <task>" to create one.')
        return False

    if not os.path.exists(get_task_path(get_actual()['task'])):
        print('Actual task points to invalid directory "'
            + get_actual()['task'] +
        '". Please set correct task with task -a <Folder/Task>.')
        return False

    return True


def move_corresponding_raws(jpg_dir, src_dir, dest_dir, dry_run):
    """
    Moves all corresponding raws from source directory to destination directory.
    jpg_dir is the /jpg directory with corresponding jpg files.
    src_dir is the /row directory with raws to move.
    dest_dir is the target directory.
    """
    # print('jpg=' + jpg_dir)
    # print('src=' + src_dir)
    # print('dst=' + dest_dir)

    jpgs = list_jpg(jpg_dir)
    # print(str(jpgs))

    raws = list_raw(src_dir)
    # print(str(raws))
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
    task 0 and, on the other hand, the task -1 will be set to last task.

    Example:
        return dict=(
        a_task=dict(subdir='family',task='holidays',active=true),
        p_task=dict(subdir='family',task='birthday',active=False),
        n_task=dict(subdir='weekly',task='20160101',active=False))

    """
    tasks = []

    dir02 = os.listdir(get_path(DIR_02))
    dir02.sort()
    active = get_actual()

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

            # print('get_next_task() ' + str(tasks))

            # Just one or none task
    if len(tasks) == 0:
        return None
    elif len(tasks) == 1:
        return dict(a_task=tasks[0], n_task=None, p_task=None)

        # Find active item
    max_i = len(tasks) - 1

    active_i = -1
    for i in range(0, max_i + 1):
        # print('i={0}'.format(i))
        if tasks[i]['active']:
            active_i = i
            break
    # print('active_i={0}, offset={1}'.format(active_i, offset))

    i_active = active_i + offset
    i1 = i_active - 1
    i2 = i_active + 1
    # if(backwards):
    # i_active = active_i - 1
    # i1 = active_i - 2
    # i2 = active_i
    # else:
    # i_active = active_i + 1
    # i1 = active_i
    # i2 = active_i + 2
    # print('get_next_task() p={0} a={1} n={2}'.format(i1, i_active, i2))

    # Handle out of ranges
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

    # print('get_next_task() p={0} a={1} n={2}'.format(i1, i_active, i2))
    return dict(a_task=tasks[i_active], p_task=tasks[i1],
                n_task=tasks[i2])