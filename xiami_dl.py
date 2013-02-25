#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import urllib2
import subprocess
import sys


def get_downloader(name=None):
    if not name:
        name = {
            'win32': 'urllib2'
        }.get(sys.platform, 'wget')

    return {
        'urllib2': urllib2_downloader,
        'wget': wget_downloader
    }.get(name, None)


def urllib2_downloader(url, dest, headers):
    request = urllib2.Request(url)
    for h in headers:
        request.add_header(h, headers[h])
    try:
        response = urllib2.urlopen(request)
        with open(dest, 'wb') as output:
            output.write(response.read())
    except IOError as e:
        print e
    except urllib2.URLError as e:
        print e


def wget_downloader(url, dest, headers):
    wget_opts = ['wget', url, '-O', dest]
    for h in headers:
        wget_opts.append('--header=%s:%s' % (h, headers[h]))
    exit_code = subprocess.call(wget_opts)
    if exit_code != 0:
        raise Exception('wget exited abnormaly')
