# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from xiami_downloader import http
from xiami_downloader._compat import (
    cookiejar,
    parse,
    range,
    request,
)


USER_AGENT = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 7.1; Trident/5.0)'


def decrypt_location(location):
    """Decrypts the `location` field in Xiami responses to URL."""
    if not location:
        return None

    rows, url = int(location[:1]), location[1:]

    urllen = len(url)
    cols_base = urllen // rows  # basic column count
    rows_ex = urllen % rows     # count of rows that have 1 more column

    matrix = []
    for r in range(rows):
        length = cols_base + 1 if r < rows_ex else cols_base
        matrix.append(url[:length])
        url = url[length:]

    url = ''
    for i in range(urllen):
        url += matrix[i % rows][i // rows]

    return parse.unquote(url).replace('^', '0')


def login(email, password):
    """Gets the user cookie at Xiami.com"""
    logging.info('Start to login to Xiami.com')

    headers = {
        'User-Agent': http.USER_AGENT,
        'Referer': 'http://www.xiami.com/web/login',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    form = {
        'email': email,
        'password': password,
        'LoginButton': '登录',
    }
    req = http.build_request('POST', 'http://www.xiami.com/web/login',
                             headers=headers, form=form)

    jar = cookiejar.CookieJar()
    opener = request.build_opener(request.HTTPCookieProcessor(jar))

    try:
        opener.open(req)
    except Exception as e:
        logging.warn('Login failed: %s', e)
        return None

    member_auth = next((c.value for c in jar if c.name == 'member_auth'), None)
    if not member_auth:
        logging.warn('Login failed: `member_auth` not in cookies')
        return None

    logging.info('Login success')
    return 'member_auth={}; t_sign_auth=1'.format(member_auth)
