#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys
import urllib
import urllib2
import json
import httplib
import HTMLParser
from contextlib import closing
from Cookie import SimpleCookie

from xiami_dl import get_downloader
from xiami_util import query_yes_no, sanitize_filename

# ID3 tags support depends on Mutagen
try:
    import mutagen
    import mutagen.mp3
    import mutagen.id3
except:
    mutagen = None
    sys.stderr.write("No mutagen available. ID3 tags won't be written.\n")


VERSION = '0.3.2'

URL_PATTERN_ID = 'http://www.xiami.com/song/playlist/id/%d'
URL_PATTERN_SONG = URL_PATTERN_ID + '/object_name/default/object_id/0/cat/json'
URL_PATTERN_ALBUM = URL_PATTERN_ID + '/type/1/cat/json'
URL_PATTERN_PLAYLIST = URL_PATTERN_ID + '/type/3/cat/json'
URL_PATTERN_VIP = 'http://www.xiami.com/song/gethqsong/sid/%s'

HEADERS = {
    'User-Agent':
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 7.1; Trident/5.0)',

    'Referer': 'http://www.xiami.com/song/play'
}


# Output / Redirected Output
default_encoding = sys.stdout.encoding or sys.getdefaultencoding()
if not default_encoding or default_encoding.lower() == 'ascii':
    default_encoding = 'utf-8'


class Song(object):
    def __init__(self):
        self.title = u'Unknown Song'
        self.song_id = 0
        self.track = 0
        self.album_id = 0
        self.album_tracks = 0
        self.album_name = u'Unknown Album'
        self.artist = u'Unknown Artist'
        self.location = None
        self.lyric_url = None
        self.pic_url = None

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self._location = value
        self.url = decode_location(self._location)


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


# https://gist.github.com/lepture/1014329
def vip_login(email, password):
    println('Login for vip ...')
    _form = {
        'email': email, 'password': password,
        'LoginButton': '登录',
    }
    data = urllib.urlencode(_form)
    headers_login = {'User-Agent': HEADERS['User-Agent']}
    headers_login['Referer'] = 'http://www.xiami.com/web/login'
    headers_login['Content-Type'] = 'application/x-www-form-urlencoded'
    with closing(httplib.HTTPConnection('www.xiami.com')) as conn:
        conn.request('POST', '/web/login', data, headers_login)
        res = conn.getresponse()
        cookie = res.getheader('Set-Cookie')
        member_auth = SimpleCookie(cookie)['member_auth'].value
        _auth = 'member_auth=%s; t_sign_auth=1' % member_auth
        println('Login success')
        return _auth


def get_songs(url):
    return parse_playlist(get_response(url))


def create_song(raw):
    parser = HTMLParser.HTMLParser()

    song = Song()
    song.title = parser.unescape(raw['title'])
    song.artist = parser.unescape(raw['artist'])
    song.album_name = parser.unescape(raw['album_name'])
    song.song_id = raw['song_id']
    song.album_id = raw['album_id']
    song.location = raw['location']
    song.lyric_url = raw['lyric_url']
    song.pic_url = raw['pic']
    return song


def parse_playlist(playlist):
    data = json.loads(playlist)

    if not data['status']:
        return []

    # trackList would be `null` if no tracks
    track_list = data['data']['trackList']
    if not track_list:
        return []

    return map(create_song, track_list)


def vip_location(song_id):
    response = get_response(URL_PATTERN_VIP % song_id)
    return json.loads(response)['location']


def decode_location(location):
    if not location:
        return None

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
    parser.add_argument('--name-template', default='{id} - {title} - {artist}',
                        help='filename template')
    parser.add_argument('--no-lrc-timetag', action='store_true',
                        help='remove timetag in lyric')
    parser.add_argument('-un', '--username', default='',
                        help='Vip account email')
    parser.add_argument('-pw', '--password', default='',
                        help='Vip account password')

    return parser.parse_args()


class XiamiDownloader:
    def __init__(self, args):
        self.downloader = get_downloader(args.tool)
        self.force_mode = args.force
        self.name_template = args.name_template
        self.song_track_db = {}
        self.no_lrc_timetag = args.no_lrc_timetag
        self.directory = args.directory

    def get_song_track(self, song):
        # Cache the track info
        if song.song_id not in self.song_track_db:
            tracks = self.get_album(song.album_id)['data']['trackList']
            for i, track in enumerate(tracks):
                self.song_track_db[track['song_id']] = {
                    'track': i + 1,
                    'track_count': len(tracks)
                }

        if song.song_id in self.song_track_db:
            song_track = self.song_track_db[song.song_id]['track']
            album_tracks = self.song_track_db[song.song_id]['track_count']
        else:
            song_track = 0
            album_tracks = 0

        return song_track, album_tracks

    def format_filename(self, song):
        template = unicode(self.name_template)
        filename = sanitize_filename(template.format(
            id=u'{:02d}'.format(song.track),
            title=song.title,
            artist=song.artist,
        ))
        return u'{}.mp3'.format(filename)

    def format_folder(self, wrap, song):
        return os.path.join(
            wrap.decode(default_encoding),
            sanitize_filename(song.album_name)
        )

    def download(self, url, filename):
        if not self.force_mode and os.path.exists(filename):
            if query_yes_no('File already exists. Skip downloading?') == 'yes':
                return False
        try:
            self.downloader(url, filename, HEADERS)
            return True
        except Exception as e:
            println(u'Error downloading: {}'.format(e))
            return False

    def get_album(self, album_id):
        response = json.loads(get_response(
            'http://www.xiami.com/song/playlist/id/{}/type/1/cat/json'.format(
                album_id
            )
        ))
        return response

    def download_songs(self, songs, with_tagging):
        for i, song in enumerate(songs):
            song.track, song.album_tracks = self.get_song_track(song)

            # generate filename and put file into album folder
            filename = self.format_filename(song)
            folder = self.format_folder(self.directory, song)
            pathname = os.path.join(folder, filename)

            if not os.path.exists(folder):
                os.makedirs(folder)

            println('\n[%d/%d] %s' % (i + 1, len(songs), pathname))
            downloaded = self.download(song.url, pathname)

            # No tagging is needed if download failed or skipped
            if not downloaded:
                continue

            if with_tagging:
                add_id3_tag(pathname, song, self.no_lrc_timetag)


def build_url_list(pattern, l):
    return [pattern % item for group in l for item in group]


# https://github.com/hujunfeng/lrc2txt
def lrc2txt(fp):
    TIME_TAG_RE = '\[\d{2}:\d{2}\.\d{2}\]'
    lyrics = {}
    all_time_tags = []
    lrc = ''
    fp = fp.splitlines()

    counter = 0
    for l in fp:
        line = re.sub(TIME_TAG_RE, '', l)
        time_tags = re.findall(TIME_TAG_RE, l)
        for tag in time_tags:
            lyrics[tag] = line
            all_time_tags.insert(counter, tag)
            counter += 1

    all_time_tags.sort()

    for tag in all_time_tags:
        lrc += lyrics[tag] + '\n'

    return lrc


# Get album image url in a specific size
def get_album_image_url(basic, size=None):
    if size:
        rep = r'\1_%d\2' % size
    else:
        rep = r'\1\2'
    return re.sub(r'^(.+)_\d(\..+)$', rep, basic)


def add_id3_tag(filename, song, no_lrc_timetag):
    println('Tagging...')

    println('Getting album cover...')
    # 4 for a reasonable size, or leave it None for the largest...
    image_url = get_album_image_url(song.pic_url, 4)
    image = get_response(image_url)

    musicfile = mutagen.mp3.MP3(filename)
    try:
        musicfile.add_tags()
    except mutagen.id3.error:
        pass  # an ID3 tag already exists

    # Unsynchronised lyrics/text transcription
    if song.lyric_url:
        println('Getting lyrics...')
        lyric = get_response(song.lyric_url)

        if no_lrc_timetag:
            old_lyric = lyric
            lyric = lrc2txt(lyric)
            if lyric:
                lyric = old_lyric

        musicfile.tags.add(mutagen.id3.USLT(
            encoding=3,
            desc=u'Lyrics',
            text=unicode(lyric, 'utf-8', errors='replace')
        ))

    # Track Number
    musicfile.tags.add(mutagen.id3.TRCK(
        encoding=3,
        text=u'{}/{}'.format(song.track, song.album_tracks)
    ))

    # Track Title
    musicfile.tags.add(mutagen.id3.TIT2(
        encoding=3,
        text=song.title
    ))

    # Album Title
    musicfile.tags.add(mutagen.id3.TALB(
        encoding=3,
        text=song.album_name
    ))

    # Lead Artist/Performer/Soloist/Group
    musicfile.tags.add(mutagen.id3.TPE1(
        encoding=3,
        text=song.artist
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


def main():
    args = parse_arguments()

    xiami = XiamiDownloader(args)

    # Constructs URLs for manifest
    urls = []

    if args.song:
        urls.extend(build_url_list(URL_PATTERN_SONG, args.song))
    if args.album:
        urls.extend(build_url_list(URL_PATTERN_ALBUM, args.album))
    if args.playlist:
        urls.extend(build_url_list(URL_PATTERN_PLAYLIST, args.playlist))

    vip_mode = args.username and args.password
    if vip_mode:
        HEADERS['Cookie'] = vip_login(args.username, args.password)

    # parse playlist for a list of track info
    songs = [
        song
        for playlist_url in urls
        for song in get_songs(playlist_url)
    ]

    if vip_mode:
        for song in songs:
            song.location = vip_location(song.song_id)

    println('%d file(s) to download' % len(songs))

    tagging_enabled = mutagen and (not args.no_tag)
    xiami.download_songs(songs, tagging_enabled)


if __name__ == '__main__':
    main()
