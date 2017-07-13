import pickle
import sys

from plump import get_fow_root, DIR_FOW

# configuration file for this fw installation, read once with readFowConfig()
fow_config = None


def create_pickle(settings):
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


def read_item(key):
    """
    Returns the value of the given key from the fow pickle. If key not found or pickle not found, None will be returned.
    """
    settings = read_pickle()
    if settings is None:
        return None
    try:
        return settings[key]
    except:
        return None


def read_pickle():
    """
    Returns a dictionary from setting.pickle.
    Returns None, if setting not found
    Example:
        return dict(task='w/kw05', export.pc='/media/diskstation/photo/w')
    """
    try:
        with open(get_fow_root() + '/' + DIR_FOW + '/setting.pickle',
                  'rb') as data:
            settings = pickle.load(data)
    except IOError:
        print('setting.pickle not found but will be created with next writing.')
        return None

    return settings


def set_item(key, value):
    """
    Updates or creates the specific value in the config pickle.
    Returns True, if item could be updated, otherwise False.
    """
    settings = read_pickle()
    settings[key] = value

    return create_pickle(settings)


def read_installation_item(_key):
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
            return ''
            # print(str(fow_config))

    try:
        return fow_config[_key]
    except:
        return ''


def get_help_file_dir():
    """
    Returns the string path to the help files. In this directory, there has
    to be a file for every command.
    """
    # return 'helpFiles'
    # return 'man'
    # return '/usr/share/man/man1'

    # print('HELP_FILE_DIR=' + readFowConfig('HELP_FILE_DIR'))
    return read_installation_item('HELP_FILE_DIR')