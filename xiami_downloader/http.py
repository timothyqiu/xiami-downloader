from __future__ import absolute_import
from __future__ import unicode_literals

from xiami_downloader._compat import ensure_binary, iteritems, parse, request


def build_request(method, url, headers, form=None):
    req = request.Request(url)
    req.method = method

    headers = headers.copy()

    if form:
        # urlencode in PY2 has no `encode` argument
        form = {
            key: ensure_binary(value)
            for key, value in iteritems(form)
        }
        headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
        })
        req.data = ensure_binary(parse.urlencode(form))

    for name, value in iteritems(headers):
        req.add_header(name, value)

    return req
