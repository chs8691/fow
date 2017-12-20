import os

import re

import sys

from plump import list_raw, list_video, list_jpg, images_get_exifs, image_get_exifs, image_write_gps, progress_prepare


def analyse(track_path, image_path):
    """
    Analyses for gps command for all image files in the given image_path. Tracks will be searched in track_path. Both
    directories should exist and should be accessible; but they can be empty. Subdirectories are not supported, neither
    for tracks, nor for images.
    Returns a list with a dict for every image file. List can be empty.
    Supported image file types are: jpg, raw and videos; it will be always search for every image type. Other files
    will be untouched (XMP, tiff).
    Supported track files are: gpx, tcx.
    Example with explanations:
    dict=(track_path=track_path, image_path=image_path, files=
        [dict=(
            image_name='img001.raf',            # name of the image file
            image_gps= dict=(lat=123, lon=234)  # actual image file location, can be None
            tracks=['2017-03-05.gpx', ...],     # list with names of the track file, can be None
            dict=(...), ...
        ]
    """
    ret = dict(track_path=track_path, image_path=image_path, files=[])

    images = list_video(image_path)
    images.extend(list_jpg(image_path))

    # Load all gps files
    gpx_files = os.listdir(track_path)

    patterns = []
    # for each in images:
    #     ret['files'].append(dict(image_name=each))

    exifs = images_get_exifs(image_path, images)
    # print("anlyse() exifs={}".format(str(exifs)))
    for each in exifs:
        # print("analyse() {} {}".format(str(each['name']), str(each['createdate'])))
        if not each['createdate'] is None:
            (date, time) = each['createdate'].split(" ", 1)
            (y,m,d) = date.split(':')
            # print("analyse() {}-{}-{}".format(str(y), str(m), str(d)))
            # patterns.append(".*{0}.?{1}.?{2}.*\.gpx".format(y, m, d))
            pattern = re.compile(".*{0}.?{1}.?{2}.*\.(tcx|gpx)".format(y, m, d))
            # print("analyse() {0} track_files={1}".format(each['name'], str(track_files)))
            track_files = [f for f in gpx_files if not pattern.match(f) is None]
            ret['files'].append(dict(image_name=each['name'], image_gps=each['gps'], tracks=track_files))

    # print("analyse() ret={}".format(ret))
    return ret


def test(analysis, verbose):
    """
    Dry run of rename command.
    verbose - boolean
    Example for analysis:
    dict=(track_path=track_path, image_path=image_path, files=
        [dict=(
            image_name='img001.raf',            # name of the image file
            image_gps= dict=(lat=123, lon=234)  # actual image file location, can be None
            tracks=['2017-03-05.gpx', ...],     # list with names of the track file, can be None
            dict=(...), ...
        ]
    """
    cntWithTracks = 0
    cntWithoutTracks = 0
    cntOverwrite = 0

    print('Path to images: {}'.format(analysis['image_path']))
    print('Path to tracks: {}'.format(analysis['track_path']))

    name_col_len = 1
    # Column length for image name
    for each in analysis['files']:
        if len(each['image_name']) > name_col_len:
            name_col_len = len(each['image_name'])

    for each in analysis['files']:
        if each['image_gps'] is None:
            has_gps = ' '
        else:
            has_gps = 'g'
        if len(each['tracks']) == 0:
            cntWithoutTracks += 1
        else:
            cntWithTracks += 1

        if len(each['tracks']) > 0:
            if not each['image_gps'] is None:
                cntOverwrite += 1
                status = 'o'
            else:
                status = '+'
        else:
            status = ' '

        formatting = '{} {:<' + str(name_col_len) + '} {} {}'
        if verbose:
            print(formatting.format(status, each['image_name'], has_gps, str(each['tracks'])))

    print(('{} images, {} with potentially track files, {} without track files. ' +
           '{} with existing gps information (would be overwritten).')
          .format(len(analysis['files']), cntWithTracks, cntWithoutTracks, cntOverwrite))


def do(analysis, force, verbose):
    """
    Cpmmand gps execution.
    """
    cnt_set = 0
    cnt_overwritten = 0
    cnt_nothing_done = 0

    print('Path to images: {}'.format(analysis['image_path']))
    print('Path to tracks: {}'.format(analysis['track_path']))

    name_col_len = 1
    # Column length for image name
    for each in analysis['files']:
        if len(each['image_name']) > name_col_len:
            name_col_len = len(each['image_name'])

    if not verbose:
        # print('Processing images', end='')
        index = 0
        progress = progress_prepare(len(analysis['files']), 'Processing', analysis['image_path'])

    for each in analysis['files']:
        if not verbose:
            # print('.', end='')
            index += 1
            sys.stdout.write(progress['back'] + progress['formatting'].format(str(index)))
            sys.stdout.flush()
        action = ' '
        gpx_name = ''
        if each['image_gps'] is None:
            has_gps = ' '
        else:
            has_gps = 'g'
        if not force:
            cnt_nothing_done += 1
            continue

        gps_new = None
        for each_track in each['tracks']:
            image_write_gps(
                '{}/{}'.format(analysis['image_path'], each['image_name']),
                '{}/{}'.format(analysis['track_path'], each_track))
            gps_new = image_get_exifs(analysis['image_path'], each['image_name'])['gps']

            # Exit criteria: gps set
            if gps_new is not None:
                if gps_new == each['image_gps']:
                    # Same gps, try again
                    continue
                has_gps = 'g'
                gpx_name = each_track
                if each['image_gps'] is None:
                    action = '+'
                else:
                    action = '*'
                    cnt_overwritten += 1
                break

        if action == ' ':
            cnt_nothing_done += 1
        else:
            cnt_set += 1

        if verbose:
            # +g img001.jpg 20160321.gpx
            formatting = '{}{} {:<' + str(name_col_len) + '} {}'
            print(formatting.format(action, has_gps, each['image_name'], gpx_name))

    if not verbose:
        # print('Done.')
        sys.stdout.write('\n')

    print('{} images processed, {} gps data set (where {} existing gps data were changed)'
          .format(len(analysis['files']), cnt_set, cnt_overwritten))

