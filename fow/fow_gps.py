import os

import re

import sys
import webbrowser
from shutil import copy

from plump import DIR_FOW, get_fow_root, list_video, list_jpg, images_get_exifs, image_get_exifs, image_write_gps, progress_prepare


class Map(object):
    def __init__(self):
        self._points = []

    def add_point(self, coordinates):
        """
        Adds new marker
        :param coordinates: array with lan, lon, title, label
        :return:
        """
        self._points.append(coordinates)

    def count(self):
        """
        Returns the nr. of points
        :return: Positive integer
        """
        return len(self._points)

    def __str__(self):
        center_lat = sum(( x[0] for x in self._points)) / len(self._points)
        center_lon = sum(( x[1] for x in self._points)) / len(self._points)

        markers_code = "\n".join(["""
                lonLat = new OpenLayers.LonLat( {lon} ,{lat} )
                      .transform(
                        new OpenLayers.Projection("EPSG:4326"), // transform from WGS 1984
                        map.getProjectionObject() // to Spherical Mercator Projection
                      );
            
                markers.addMarker(new OpenLayers.Marker(lonLat));
            """.format(lat=x[0], lon=x[1], name=x[2], title=x[3], description=x[4], label=x[5]) for x in self._points
            ])

        return """
            <html>
            <body>
              <div id="mapdiv"></div>
              <script src="http://www.openlayers.org/api/OpenLayers.js"></script>
              <script>
                map = new OpenLayers.Map("mapdiv");
                map.addLayer(new OpenLayers.Layer.OSM());
            
                var zoom=14;
                var markers = new OpenLayers.Layer.Markers( "Markers" );
                var lonLat;
                {markersCode}
                map.addLayer(markers);
                
                var lonLatCenter = new OpenLayers.LonLat( {centerLon} ,{centerLat} )
                      .transform(
                        new OpenLayers.Projection("EPSG:4326"), // transform from WGS 1984
                        map.getProjectionObject() // to Spherical Mercator Projection
                      );
                map.setCenter (lonLatCenter, zoom);
              </script>
            </body></html>
        """.format(centerLat=center_lat, centerLon=center_lon,
                   markersCode=markers_code)


def map(image_path):
    """
    Show map with pins for all jpg images in the given path
    :param image_path: String with path
    :return: -
    """
    labels = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    labelIndex = 0

    map = Map()
    images = list_jpg(image_path)
    exifs = images_get_exifs(image_path, images, report=True)

    # Sorted list by date, so the labels will be sorted
    names = list()
    for each in exifs:
        names.append((each['createdate'], each))
    for e in sorted(names, key=lambda item: item[0]):
        if not e[1]['gps'] is None and not e[1]['gps']['lon'] is None:
            map.add_point((float(e[1]['gps']['lat']), float(e[1]['gps']['lon']), e[1]['name'],
                           e[1]['title'], e[1]['description'], labels[labelIndex % len(labels)]))
            labelIndex += 1;

    if map.count() < 1:
        print('All {} images without geo locations'.format(str(len(images))))
        return

    file_path = get_fow_root() + DIR_FOW + "/map.html"
    with open(file_path, "w") as out:
        print(map, file=out)
        webbrowser.open(file_path)


def analyse(track_path, image_path, write_path):
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
    ret = dict(track_path=track_path, image_path=image_path, files=[], existing_track_files=[])

    images = list_video(image_path)
    images.extend(list_jpg(image_path))

    # Load all gps files
    gpx_files = os.listdir(track_path)

    patterns = []
    # for each in images:
    #     ret['files'].append(dict(image_name=each))

    exifs = images_get_exifs(image_path, images, True)
    existing_track_files = []
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

            # Find existing track files, that would be overwritten
            if write_path is not None:
                for dest in os.listdir(write_path):
                    for src in (t for t in track_files if t == dest):
                        existing_track_files.append(src)
                        # print("analyse() exists={}".format(src))

            ret['files'].append(dict(image_name=each['name'], image_gps=each['gps'], tracks=track_files))

    ret['existing_track_files'] = list(frozenset(existing_track_files))

    # print("analyse() ret={}".format(ret))
    return ret


def test(analysis, verbose, write_path):
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
    :param write_path: Path to the copy directory for the found ttrack file
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

    if write_path is None:
        print(('{} images, {} with potentially track files, {} without track files. ' +
               '{} with existing gps information (would be overwritten)')
              .format(len(analysis['files']), cntWithTracks, cntWithoutTracks, cntOverwrite))
    else:
        print(('{} images, {} with potentially track files, {} without track files. ' +
               '{} with existing gps information (would be overwritten)')
              .format(len(analysis['files']), cntWithTracks, cntWithoutTracks, cntOverwrite))
        if len(analysis['existing_track_files']) > 0:
            if verbose:
                print('Track files will be copied to {} and would potentially overwrite up to {} files:'
                      .format(write_path, len(analysis['existing_track_files'])))
                for each in analysis['existing_track_files']:
                    print(each)
            else:
                print('Track files will be copied to {} and would potentially overwrite up to {} files.'
                      .format(write_path, len(analysis['existing_track_files'])))
        else:
            print('Track files will be copied to {}'.format(write_path))


def do(analysis, force, verbose, write_path):
    """
    Cpmmand gps execution.
    """
    cnt_set = 0
    cnt_overwritten = 0
    cnt_nothing_done = 0

    print('Path to images: {}'.format(analysis['image_path']))
    print('Path to tracks: {}'.format(analysis['track_path']))
    if write_path is not None:
        print('Path to write track file copies: {}'.format(write_path))

    name_col_len = 1
    # Column length for image name
    for each in analysis['files']:
        if len(each['image_name']) > name_col_len:
            name_col_len = len(each['image_name'])

    if not verbose:
        # print('Processing images', end='')
        index = 0
        progress = progress_prepare(len(analysis['files']), 'Processing', analysis['image_path'])

    # --write: Do this in a separate step
    copy_list = []

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

        if action != ' ' and write_path is not None:
            copy_list.append(gpx_name)

    if not verbose:
        # print('Done.')
        sys.stdout.write('\n')

    # --write: Now copy found track files to destination
    cnt_write_err = 0
    cnt_write = 0
    cnt_overwritten = 0
    for each in frozenset(copy_list):
        if each in analysis['existing_track_files']:
            verb = "Done (overwritten)."
        else:
            verb = "Done."
        try:
            copy(os.path.join(analysis['track_path'], each), write_path)
            if verbose:
                print("Copy {} {}".format(each, verb))
            cnt_write += 1
            if each in analysis['existing_track_files']:
                cnt_overwritten += 1
        except IOError as e:
            print("Copy {} failed: {}".format(each, e))
            cnt_write_err += 1

    if write_path is None:
        print('{} images processed, {} gps data set (where {} existing gps data were changed).'
              .format(len(analysis['files']), cnt_set, cnt_overwritten))
    else:
        print(('{} images processed, {} gps data set (where {} existing gps data were changed). '
               'Copied {} track file(s), {} overwritten, {} failed.')
              .format(len(analysis['files']), cnt_set, cnt_overwritten, cnt_write, cnt_overwritten, cnt_write_err))

