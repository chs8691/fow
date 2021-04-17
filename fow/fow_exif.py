import os
import re
import subprocess

import task
from plump import DIR_FINAL
from plump import list_jpg
from plump import string_get_max_length, images_get_exifs


def check_images(path, criteria):
    """
    Try to find the images to change. Checks criteria and prints a message in error case.
    :param path:
    :param criteria: String with eihter a number or a filename to select an image. Can be "all" to select all images
    in the actual task final dir. An empty string will be interpreted as '1' (first image)
    :return: A list with file names (like os.listdir) or, in error case, None
    """

    all_files = list_jpg(path)
    # print("check_images {}".format(str(all_files)))

    if criteria == "all":
        return all_files

    if len(all_files) == 0:
        print("No images found in {}".format(str(path)))
        return None

    # Convenience for most cases
    if criteria is None:
        criteria = "1"

    # Select by number
    if re.match("^\d*$", criteria):
        nr = int(criteria)
        if nr < 1 or nr > len(all_files):
            print("Image nr doesn't match a file (must between {} and {})".format(str(1), str(len(all_files))))
            return None

        return [all_files[nr - 1]]

    # Criteria can be a file name
    for file in (f for f in all_files if f == criteria):
        return [file]

    # Unexpected criteria
    print("Criteria '{}' invalid. Must be either a number, an existing file name or 'all'".format(str(criteria)))
    return None


def analyse(src_path, files, title, description, author):
    """
    Checks exif for all files in src_path
    :param src_path: Path to the image files
    :param files: List with valid file names
    :param title: String with new title, or None, if tag should not be changed
    :param description: String with new description, or None, if tag should not be changed
    :param author: String for author tag. Can be None

    Returns list with dict() for every image file, for instance:
        return [
          dict(name='image001.jpg',
               title=dict(old=None, new="new title', changed=True, overwrite=True),
               description=dict(old=None, new="new title', changed=True, overwrite=True)
               author=dict(old=None, new="new author', changed=True, overwrite=True)
               )
        ]
        'changed' is True, if tag will be set
        'overwrite' is True, if old value would be overwritten (needs force)
    """
    src_dir = task.get_task_path(task.get_actual()['task']) + '/' + DIR_FINAL
    # files = list_jpg(src_dir)
    exifs = images_get_exifs(src_dir, files, report=False)

    ret = []
    for each in exifs:
        ret.append(dict(name=each['name'], title=_analyze_tag(title, each['title']),
                        description=_analyze_tag(description, each['description']),
                        author=_analyze_tag(author, each['author'])))

    # print('analyse() ret=' + str(ret))

    return ret


def _analyze_tag(new, old):
    # print("_analyze_tag() in={}, {}, {}".format(str(new), str(old), str(force)))
    if new is None:
        changed = False
        overwrite = False
    else:
        changed = new != old
        overwrite = old is not None

    ret = dict(old=old, new=new, changed=changed, overwrite=overwrite)
    # print("_analyze_tag() out={}".format(str(ret)))

    return ret


def show(analysis, src_dir, verbose):
    """
    Prints exif tags.
        :param verbose: If true, empty tags will be reported, too. Otherwise only tags with values will be reported.
    """
    # print(str(analysis))
    # print("Found {} files in {}".format(str(len(analysis)), src_dir))

    max_name_len = string_get_max_length(['title', 'description' 'author'])

    overwrite = False
    for item in analysis:
        print("{}".format(item['name']))
        if item['title']['old'] or verbose:
            _report_tag(item['title'], "title", max_name_len)
        if item['description']['old'] or verbose:
            _report_tag(item['description'], "description", max_name_len)
        if item['author']['old'] or verbose:
            _report_tag(item['author'], "author", max_name_len)

        overwrite = overwrite or item['title']['overwrite'] or item['description']['overwrite'] \
            or item['author']['overwrite']


def test(analysis, src_dir, title_flag, description_flag, author_flag, force, verbose):
    """
    Prints an export test run.
        :param verbose: If true, untouched tags will be reported, too. Otherwise only tags to set will be reported.
    """
    # print(str(analysis))
    # print("Found {} files in {}".format(str(len(analysis)), src_dir))

    max_name_len = string_get_max_length(['title', 'description' 'author'])

    overwrite = False
    for item in analysis:
        print("{}".format(item['name']))
        if title_flag or verbose:
            _report_tag(item['title'], "title", max_name_len)
        if description_flag or verbose:
            _report_tag(item['description'], "description", max_name_len)
        if author_flag or verbose:
            _report_tag(item['author'], "author", max_name_len)

        overwrite = overwrite or item['title']['overwrite'] or item['description']['overwrite'] \
            or item['author']['overwrite']

    if not force and overwrite:
        print("Value(s) would be overwritten, use --force to to this.")


def _set_tag(tag, name, max_name_len):

    # print("tag_analysis={}".format(str(tag)))
    if tag['old'] is None and tag['new'] is None:
        return

    if tag['new'] is None:
        status = ' '
    else:
        if tag['old'] is None:
            status = '+'
        else:
            status = 'o'

    if tag['old'] is not None and tag ['new'] is not None:
        message = "{} -> {}".format(tag['old'], tag['new'])
    elif tag['new'] is not None:
        message = "{}".format(tag['new'])
    elif tag['old'] is not None:
        message = "{}".format(tag['old'])
    else:
        message = ""

    print("  {} {} {}".format(status, name.ljust(max_name_len), message))


def _report_tag(tag, name, max_name_len):

    # print("tag_analysis={}".format(str(tag)))
    # if tag['old'] is None and tag['new'] is None:
    #     return

    if tag['new'] is None:
        status = ' '
    else:
        if tag['old'] is None:
            status = '+'
        else:
            status = 'o'

    if tag['old'] is not None and tag ['new'] is not None:
        message = "{} -> {}".format(tag['old'], tag['new'])
    elif tag['new'] is not None:
        message = "{}".format(tag['new'])
    elif tag['old'] is not None:
        message = "{}".format(tag['old'])
    else:
        message = ""

    print("  {} {} {}".format(status, name.ljust(max_name_len), message))


def _write_tags(image_path, title, description, author):
    """
    Update the gps exifs of the image by the given values (if not None).
    Returns True, if successful, otherwise false
    """

    cmd = 'exiftool'
    
    if title is not None:
        cmd = "{} -title='{}'".format(cmd, title)

    if description is not None:
        cmd = "{} -description='{}'".format(cmd, description)

    if author is not None:
        cmd = "{} -author='{}'".format(cmd, author)

    cmd = "{} {} -overwrite_original".format(cmd, image_path)

    # print('_write_tags() cmd={}'.format(cmd))
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
        print(str(e))
        return False

    return True


def do(analysis, src_dir, title_flag, description_flag, author_flag, verbose):
    """
    Cpmmand exif execution.
    """
    cnt_files_changed = 0
    cnt_tags_set = 0

    # print(str(analysis))
    # print("Found {} files in {}".format(str(len(analysis)), src_dir))

    max_name_len = string_get_max_length(['title', 'description' 'author'])

    for item in analysis:
        print("{}".format(item['name']))
        if _write_tags("{}/{}".format(src_dir, item['name']), item['title']['new'],
                       item['description']['new'], item['author']['new']):
            if title_flag or verbose:
                _report_tag(item['title'], "title", max_name_len)
            if description_flag or verbose:
                _report_tag(item['description'], "description", max_name_len)
            if author_flag or verbose:
                _report_tag(item['author'], "author", max_name_len)
        else:
            print('  Error: Could not write tags!')


def dictlist_get_max_length(analysis, fieldname):
    """
    Returns max string lenght for 'name' in list of dicts.
    """
    names = []
    for item in analysis:
        names.append(item[fieldname])

    return string_get_max_length(names)
