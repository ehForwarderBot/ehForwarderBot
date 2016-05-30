import re, html

import os
from . import config

def clear_screen():
    os.system('cls' if config.OS == 'Windows' else 'clear')
def emoji_dealer(l):
    #regex = re.compile('^(.*?)(?:<span class="emoji emoji([0-9a-fA-F]+)"></span>(.*?))+$')
    for m in l: # because m is dict so can be used like this
        m['NickName'] = escape_emoji(m['NickName'])
    return l

def escape_emoji(s):
    s = re.split('<span class="emoji emoji|"></span>', s)
    for i in range(len(s)):
        try:
            s[i] = chr(int(s[i], 16))
        except:
            pass
    s = ''.join(s)
    s = s.replace('<br/>', '\n')
    s = html.unescape(s)
    return s

def check_file(fileDir):
    try:
        with open(fileDir): pass
        return True
    except:
        return False
