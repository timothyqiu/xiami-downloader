from __future__ import absolute_import
from __future__ import unicode_literals

import subprocess
import sys

from xiami_downloader._compat import request


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
    req = request.Request(url)
    for h in headers:
        req.add_header(h, headers[h])
    response = request.urlopen(req)
    length = int(response.headers['Content-Length'])
    downloaded = 0.0
    with open(dest, 'wb') as output:
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            downloaded += len(chunk)
            output.write(chunk)
            percent = float(downloaded) / length * 100
            sys.stdout.write('\r{:5.1f}%'.format(percent))
            sys.stdout.flush()
        sys.stdout.write('\n')


def wget_downloader(url, dest, headers):
    wget_opts = ['wget', url, '-O', dest]
    for h in headers:
        wget_opts.append('--header=%s:%s' % (h, headers[h]))
    subprocess.check_call(wget_opts)
