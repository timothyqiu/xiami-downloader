#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys
import urllib
import urllib2
import xml.etree.ElementTree as ET

from xiami_dl import get_downloader
from xiami_util import query_yes_no

# ID3 tags support depends on Mutagen
try:
    import mutagen
    import mutagen.mp3
    import mutagen.id3
except:
    mutagen = None
    sys.stderr.write("No mutagen available. ID3 tags won't be written.\n")


VERSION = '0.2.1'

URL_PATTERN_ID = 'http://www.xiami.com/song/playlist/id/%d'
URL_PATTERN_SONG = '%s/object_name/default/object_id/0' % URL_PATTERN_ID
URL_PATTERN_ALBUM = '%s/type/1' % URL_PATTERN_ID
URL_PATTERN_PLAYLIST = '%s/type/3' % URL_PATTERN_ID

HEADERS = {
    'User-Agent':
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 7.1; Trident/5.0)',

    'Referer': 'http://www.xiami.com/song/play'
}


# Output / Redirected Output
default_encoding = sys.stdout.encoding or sys.getdefaultencoding()
if not default_encoding or default_encoding.lower() == 'ascii':
    default_encoding = 'utf-8'


def println(text):
    if type(text) == unicode:
        text = text.encode(default_encoding, errors='replace')
    sys.stdout.write(str(text) + '\n')


def get_response(url):
    """ Get HTTP response as text

    If sent without the headers, there may be a 503/403 error.
    """
    request = urllib2.Request(url)
    for header in HEADERS:
        request.add_header(header, HEADERS[header])

    try:
        response = urllib2.urlopen(request)
        return response.read()
    except urllib2.URLError as e:
        println(e)
        return ''


def get_playlist_from_url(url):
    tracks = parse_playlist(get_response(url))
    tracks = [
        {
            key: unicode(track[key])
            for key in track
            if track[key]
        }
        for track in tracks
    ]
    return tracks


def parse_playlist(playlist):
    try:
        # Removes the XML namespace
        playlist = re.sub(r'xmlns=\".*?\"', '', playlist)
        xml = ET.fromstring(playlist)
    except:
        return []

    return [
        {
            key: track.find(key).text
            for key in [
                'title', 'location', 'lyric', 'pic', 'artist', 'album_name'
            ]
        }
        for track in xml.iter('track')
    ]


def decode_location(location):
    url = location[1:]
    urllen = len(url)
    rows = int(location[0:1])

    cols_base = urllen / rows  # basic column count
    rows_ex = urllen % rows    # count of rows that have 1 more column

    matrix = []
    for r in xrange(rows):
        length = cols_base + 1 if r < rows_ex else cols_base
        matrix.append(url[:length])
        url = url[length:]

    url = ''
    for i in xrange(urllen):
        url += matrix[i % rows][i / rows]

    return urllib.unquote(url).replace('^', '0')


def sanitize_filename(filename):
    return re.sub(r'[\\/:*?<>|]', '_', filename)


def parse_arguments():

    note = 'The following SONG, ALBUM, and PLAYLIST are IDs which can be' \
           'obtained from the URL of corresponding web page.'

    parser = argparse.ArgumentParser(description=note)

    parser.add_argument('-v', '--version', action='version', version=VERSION)
    parser.add_argument('-f', '--force', action='store_true',
                        help='overwrite existing files without prompt')
    parser.add_argument('-t', '--tool', choices=['wget', 'urllib2'],
                        help='change the download tool')
    parser.add_argument('-s', '--song', action='append',
                        help='adds songs for download',
                        type=int, nargs='+')
    parser.add_argument('-a', '--album', action='append',
                        help='adds all songs in the albums for download',
                        type=int, nargs='+')
    parser.add_argument('-p', '--playlist', action='append',
                        help='adds all songs in the playlists for download',
                        type=int, nargs='+')
    parser.add_argument('--no-tag', action='store_true',
                        help='skip adding ID3 tag')
    parser.add_argument('--directory', default='',
                        help='save downloads to the directory')

    return parser.parse_args()


class XiamiDownloader:
    def __init__(self):
        self.force_mode = False

    def format_track(self, trackinfo, current, total):
        trackinfo['id'] = '%s/%s' % (current + 1, total)
        trackinfo['num'] = str(current + 1).zfill(2)
        return trackinfo

    def format_filename(self, trackinfo):
        return sanitize_filename(
            '%s - %s - %s.mp3' % (
                trackinfo['num'], trackinfo['title'], trackinfo['artist']
            )
        )

    def format_folder(self, wrap, trackinfo):
        return os.path.join(
            os.getcwd(),
            wrap.decode(default_encoding),
            sanitize_filename(trackinfo['album_name'])
        )

    def format_output(self, folder, filename):
        return os.path.join(folder, filename)

    def download(self, url, filename):
        if not self.force_mode and os.path.exists(filename):
            if query_yes_no('File already exists. Skip downloading?') == 'yes':
                return False
        self.downloader(url, filename, HEADERS)
        return True


def build_url_list(pattern, l):
    return [pattern % item for group in l for item in group]


# Get album image url in a specific size
def get_album_image_url(basic, size=None):
    if size:
        rep = r'\1_%d\2' % size
    else:
        rep = r'\1\2'
    return re.sub(r'^(.+)_\d(\..+)$', rep, basic)


def add_id3_tag(filename, track):
    println('Tagging...')

    println('Getting album cover...')
    # 4 for a reasonable size, or leave it None for the largest...
    image = get_response(get_album_image_url(track['pic'], 4))

    musicfile = mutagen.mp3.MP3(filename)
    try:
        musicfile.add_tags()
    except mutagen.id3.error:
        pass  # an ID3 tag already exists

    # Unsynchronised lyrics/text transcription
    if 'lyric' in track:
        println('Getting lyrics...')
        lyric = get_response(track['lyric'])

        musicfile.tags.add(mutagen.id3.USLT(
            encoding=3,
            desc=u'Lyrics',
            text=unicode(lyric, 'utf-8', errors='replace')
        ))

    # Track Number
    musicfile.tags.add(mutagen.id3.TRCK(
        encoding=3,
        text=track['id']
    ))

    # Track Title
    musicfile.tags.add(mutagen.id3.TIT2(
        encoding=3,
        text=track['title']
    ))

    # Album Title
    musicfile.tags.add(mutagen.id3.TALB(
        encoding=3,
        text=track['album_name']
    ))

    # Lead Artist/Performer/Soloist/Group
    musicfile.tags.add(mutagen.id3.TPE1(
        encoding=3,
        text=track['artist']
    ))

    # Attached Picture
    if image:
        musicfile.tags.add(mutagen.id3.APIC(
            encoding=3,         # utf-8
            mime='image/jpeg',
            type=3,             # album front cover
            desc=u'Cover',
            data=image
        ))

    println(musicfile.pprint())

    # Note:
    # mutagen only write id3v2 with v2.4 spec,
    # which win-os does not support;
    # save(v1=2) will write id3v1,
    # but that requires encoding=0 (latin-1),
    # which breaks utf-8, so no good solution for win-os.
    musicfile.save()


if __name__ == '__main__':

    args = parse_arguments()

    xiami = XiamiDownloader()
    xiami.downloader = get_downloader(args.tool)
    xiami.force_mode = args.force

    urls = []

    if args.song:
        urls.extend(build_url_list(URL_PATTERN_SONG, args.song))
    if args.album:
        urls.extend(build_url_list(URL_PATTERN_ALBUM, args.album))
    if args.playlist:
        urls.extend(build_url_list(URL_PATTERN_PLAYLIST, args.playlist))

    # parse playlist xml for a list of track info
    tracks = []
    for playlist_url in urls:
        for url in get_playlist_from_url(playlist_url):
            tracks.append(url)

    println('%d file(s) to download' % len(tracks))

    for track in tracks:
        track['url'] = decode_location(track['location'])

    for i, track in enumerate(tracks):
        track = xiami.format_track(track, i, len(tracks))

        # generate filename and put file into album folder
        filename = xiami.format_filename(track)
        folder = xiami.format_folder(args.directory, track)

        output_file = xiami.format_output(folder, filename)

        if not os.path.exists(folder):
            os.makedirs(folder)

        println('\n[%d/%d] %s' % (i + 1, len(tracks), output_file))
        downloaded = xiami.download(track['url'], output_file)

        if mutagen and downloaded and (not args.no_tag):
            add_id3_tag(output_file, track)
