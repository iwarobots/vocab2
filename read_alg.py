#!/usr/bin/env python
# -*- coding: utf-8 -*-


import requests


def validate_url(url):
    http = 'http://'
    https = 'https://'
    if not (http == url[:7] or https == url[:8]):
        url = '%s%s' % (http, url)
    return url

def read(url):
    # future: we need an async
    url = validate_url(url)
    resp = requests.get(url)
    html = resp.text
    return html