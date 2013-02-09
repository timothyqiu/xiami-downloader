#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import getopt
import sys
import urllib
import urllib2
import xml.etree.ElementTree as ET

URL_PATTERN_ID = 'http://www.xiami.com/song/playlist/id/%d'
URL_PATTERN_SONG = '%s/object_name/default/object_id/0' % URL_PATTERN_ID
URL_PATTERN_ALBUM = '%s/type/1' % URL_PATTERN_ID
URL_PATTERN_PLAYLIST = '%s/type/3' % URL_PATTERN_ID
USER_AGENT = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 7.1; Trident/5.0)'


def get_playlist_from_url(url):
    request = urllib2.Request(url)
    request.add_header('User-Agent', USER_AGENT);  # Xiami now blocks python UA
    data = urllib2.urlopen(request).read()
    return parse_playlist(data)


def parse_playlist(playlist):
    xml = ET.fromstring(playlist)
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


def download(url, dest):
    urllib.urlretrieve(url, dest)


def usage():
    message = [
        'Usage: %s [options]' % (sys.argv[0]),
        '    -a <album id>: Adds all songs in an album to download list.',
        '    -p <playlist id>: Adds all songs in a playlist to download list.',
        '    -s <song id>: Adds a song to download list.',
        '    -h : Shows usage.'
    ]
    print '\n'.join(message)


if __name__ == '__main__':
    print 'Xiami Music Preview Downloader v0.1.1'

    playlists = []

    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'ha:p:s:')
    except getopt.GetoptError as e:
        print e
        usage()
        sys.exit(1)

    for key, value in optlist:
        if key == '-a':
            playlists.append(URL_PATTERN_ALBUM % int(value))
        elif key == '-p':
            playlists.append(URL_PATTERN_PLAYLIST % int(value))
        elif key == '-s':
            playlists.append(URL_PATTERN_SONG % int(value))

    if ('-h' in optlist) or (not playlists):
        usage()
        sys.exit(1)

    tracks = []

    for playlist_url in playlists:
        for url in get_playlist_from_url(playlist_url):
            tracks.append(url)

    print '%d file(s) to download' % len(tracks)
    for i in xrange(len(tracks)):
        print '%s' % tracks[i]['title']

    for i in xrange(len(tracks)):
        track = tracks[i]
        filename = '%s.mp3' % track['title']
        url = decode_location(track['location'])
        print '[%02d/%02d] Downloading %s...' % (i, len(tracks), filename)
        download(url, filename)
