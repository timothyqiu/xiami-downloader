import urllib2
import subprocess
import sys


__all__ = ['get_downloader']


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
    response = urllib2.urlopen(request)
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
    exit_code = subprocess.call(wget_opts)
    if exit_code != 0:
        raise Exception('wget exited abnormaly')
