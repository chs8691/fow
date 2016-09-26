###############################################################################
# All plump stuff for tasks.
###############################################################################
import plump
import os


def get_actual():
    """
    Returns dictionary with keys 'task' (foldername/taskname),
    'name' (task name), 'folder' (folder name)
    of the actual task or None, if not set.
    """
    item = plump.readConfig()[plump.TASK]
    if item is None or item == 'None':
        return None
    else:
        (folder, name) = item.rsplit('/', 1)
        task = {'task': item, 'name': name, 'folder': folder}
        return task


def get_path(_task):
    """
    Returns String with the absolut path of the task, or None
    if no actual task is set.
    Example:
    get_patch('w/20160101')
        return '/home/chris/fow/02_Progress/w/20160101'
    """
    return plump.get_path(plump.DIR_02 + '/' + _task)


def check_actual():
    """
    Analyse and write error message if actual path is not set or invalid.
    Returns True, if actual task is set and path exists. No print output.
    Returns False and write error message, if task not set or path
    does not exists.
    """
    if get_actual() is None:
        print('No actual task. ' +
            'Use "task --create <task>" to create one.')
        return False

    if not os.path.exists(get_path(get_actual()['task'])):
        print('Actual task points to invalid directory "'
            + get_actual()['task'] +
        '". Please set correct task with task -a <Folder/Task>.')
        return False

    return True