import re
import html
import hashlib
import os
import urllib
from functools import partial
from . import config


def clear_screen():
    os.system('cls' if config.OS == 'Windows' else 'clear')


def emoji_dealer(l):
    # regex = re.compile('^(.*?)(?:<span class="emoji emoji([0-9a-fA-F]+)"></span>(.*?))+$')
    for m in l:  # because m is dict so can be used like this
        m['NickName'] = escape_emoji(m['NickName'])
    return l


def escape_emoji(s):
    s = re.split('<span class="emoji |"></span>', s)
    for i in range(len(s)):
        if s[i].startswith("emoji"):
            try:
                s[i] = chr(int(s[i][5:], 16))
            except:
                pass
    s = ''.join(s)
    s = s.replace('<br/>', '\n')
    s = html.unescape(s)
    return s


def check_file(fileDir):
    try:
        with open(fileDir):
            pass
        return True
    except:
        return False


def md5sum(filename):
    with open(filename, mode='rb') as f:
        d = hashlib.md5()
        for buf in iter(partial(f.read, 128), b''):
            d.update(buf)
    return d.hexdigest()


def urlencode_withoutplus(query):
    if hasattr(query, 'items'):
        query = query.items()
    l = []
    for k, v in query:
        k = urllib.parse.quote(str(k), safe="!#$%&'()*+,/:;=?@~")
        v = urllib.parse.quote(str(v), safe="!#$%&'()*+,/:;=?@~")
        l.append(k + '=' + v)
    return '&'.join(l)
