from __future__ import absolute_import
from __future__ import unicode_literals

import sys


PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY2:
    import __builtin__

    text_type = __builtin__.unicode
    binary_type = str

    input = __builtin__.raw_input
    range = __builtin__.xrange

    import cookielib
    import HTMLParser
    import urllib
    import urllib2
    import urlparse

    cookiejar = cookielib
    htmlparser = HTMLParser
    parse = urlparse
    parse.unquote = urllib.unquote
    parse.urlencode = urllib.urlencode

    request = urllib2
    URLError = urllib2.URLError

    def iteritems(d):
        return d.iteritems()
else:
    import builtins

    text_type = str
    binary_type = bytes

    input = builtins.input
    range = builtins.range

    import html.parser
    import http.cookiejar
    import urllib.error
    import urllib.parse
    import urllib.request

    cookiejar = http.cookiejar
    htmlparser = html.parser
    parse = urllib.parse
    request = urllib.request
    URLError = urllib.error.URLError

    def iteritems(d):
        return d.items()


def ensure_binary(s, encoding='utf-8', errors='strict'):
    if isinstance(s, text_type):
        return s.encode(encoding, errors)
    elif isinstance(s, binary_type):
        return s
    raise TypeError('not expecting type `%s`' % type(s))


def ensure_text(s, encoding='utf-8', errors='strict'):
    if isinstance(s, binary_type):
        return s.decode(encoding, errors)
    elif isinstance(s, text_type):
        return s
    raise TypeError('not expecting type `%s`' % type(s))
