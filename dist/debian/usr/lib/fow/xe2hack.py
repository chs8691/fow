import subprocess

from plump import DIR_RAW, list_raw, image_get_model


def analyse(path, from_model, to_model):
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
        # print(file_path + '=' + str(image_get_model(file_path)))
        file_name = each
        model = image_get_model(file_path)
        if model == from_model:
            ret.append(dict(subdir=subdir, file_name=file_name))

    return dict(path=path, from_model=from_model, to_model=to_model,
                files=ret)


def test(analysis):
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


def do(analysis):
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
        # print('xe2hack_do(): cmd={0}'.format(cmd))
        try:
            subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                shell=True,
                universal_newlines=True)
        # except subprocess.CalledProcessError as err:
        except subprocess.CalledProcessError:
            # print(str(err))
            return None

        print('{0} {1}'.format(each['subdir'], each['file_name']))

    print('{0} file(s) changed.'.format(len(analysis['files'])))