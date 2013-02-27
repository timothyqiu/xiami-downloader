#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import getopt
import os
import re
import sys
import urllib
import urllib2
import xml.etree.ElementTree as ET

from xiami_dl import get_downloader


URL_PATTERN_ID = 'http://www.xiami.com/song/playlist/id/%d'
URL_PATTERN_SONG = '%s/object_name/default/object_id/0' % URL_PATTERN_ID
URL_PATTERN_ALBUM = '%s/type/1' % URL_PATTERN_ID
URL_PATTERN_PLAYLIST = '%s/type/3' % URL_PATTERN_ID

HEADERS = {
    'User-Agent':
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 7.1; Trident/5.0)',

    'Referer': 'http://www.xiami.com/song/play'
}


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
        print e

    return ''


def get_playlist_from_url(url):
    return parse_playlist(get_response(url))


def parse_playlist(playlist):
    try:
        xml = ET.fromstring(playlist)
    except:
        return []

    return [
        {
            'title': track.find('{http://xspf.org/ns/0/}title').text,
            'location': track.find('{http://xspf.org/ns/0/}location').text
        }
        for track in xml.iter('{http://xspf.org/ns/0/}track')
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


def usage():
    message = [
        'Usage: %s [options]' % (sys.argv[0]),
        '    -a <album id>: Adds all songs in an album to download list.',
        '    -p <playlist id>: Adds all songs in a playlist to download list.',
        '    -s <song id>: Adds a song to download list.',
        '    -f : Force mode. Overwrite existing files without prompt.',
        '    -t urllib2|wget: Change the download tool.',
        '    -h : Shows usage.'
    ]
    print '\n'.join(message)


# Refer: http://code.activestate.com/recipes/577058/
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes": "yes", "y": "yes", "ye": "yes",
             "no": "no", "n": "no"}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return default
        elif choice in valid.keys():
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


class XiamiDownloader:
    def __init__(self):
        self.force_mode = False
        self.downloader = get_downloader()

    def download(self, url, filename):
        if not self.force_mode and os.path.exists(filename):
            if query_yes_no('File already exists. Skip downloading?') == 'yes':
                return
        self.downloader(url, filename, HEADERS)


if __name__ == '__main__':
    print 'Xiami Music Preview Downloader v0.1.5'

    playlists = []

    xiami = XiamiDownloader()

    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'ha:p:s:t:f')
    except getopt.GetoptError as e:
        print e
        sys.exit(1)

    for key, value in optlist:
        if key == '-a':
            playlists.append(URL_PATTERN_ALBUM % int(value))
        elif key == '-p':
            playlists.append(URL_PATTERN_PLAYLIST % int(value))
        elif key == '-s':
            playlists.append(URL_PATTERN_SONG % int(value))
        elif key == '-t':
            xiami.downloader = get_downloader(value)
        elif key == '-f':
            xiami.force_mode = True

    if not xiami.downloader:
        print 'No such downloader. Check your -t option.'

    if ('-h' in optlist) or (not playlists) or (not xiami.downloader):
        usage()
        sys.exit(1)

    tracks = []

    # parse playlist xml for a list of track info
    for playlist_url in playlists:
        for url in get_playlist_from_url(playlist_url):
            tracks.append(url)

    print '%d file(s) to download' % len(tracks)

    for i in xrange(len(tracks)):
        track = tracks[i]
        track['url'] = decode_location(track['location'])

    for i in xrange(len(tracks)):
        track = tracks[i]
        filename = '%s.mp3' % sanitize_filename(track['title'])
        url = track['url']
        print '\n[%d/%d] %s' % (i + 1, len(tracks), filename)
        xiami.download(url, filename)
