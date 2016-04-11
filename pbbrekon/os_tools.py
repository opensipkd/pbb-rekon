from datetime import datetime
from urllib import unquote_plus
from urlparse import urlparse
from time import sleep
from types import (
    StringType,
    UnicodeType,
    IntType,
    LongType,
    )
import re
import sys
import os
import pytz
import locale
#locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')


##########
# String #
##########
def clean(s):
    r = ''
    for ch in s:
        ascii = ord(ch)
        if ascii > 126 or ascii < 32:
            ch = ' '
        r += ch
    return r

def to_str(s):
    s = s or ''
    s = type(s) in [StringType, UnicodeType] and s or str(s)
    return clean(s)

def left(s, width):
    s = to_str(s)
    return s.ljust(width)[:width]

def right(s, width):
    s = to_str(s)
    return s.zfill(width)[:width]


     
##################
# Data Structure #
##################
class FixLength(object):
    def __init__(self, struct):
        self.set_struct(struct)

    def set_struct(self, struct):
        self.struct = struct
        self.fields = {}
        new_struct = []
        for s in struct:
            name = s[0]
            size = s[1:] and s[1] or 1
            typ = s[2:] and s[2] or 'A' # N: numeric, A: alphanumeric
            self.fields[name] = {'value': None, 'type': typ, 'size': size}
            new_struct.append((name, size, typ))
        self.struct = new_struct

    def set(self, name, value):
        self.fields[name]['value'] = value

    def get(self, name):
        return self.fields[name]['value']

    def __setitem__(self, name, value):
        self.set(name, value)

    def __getitem__(self, name):
        return self.get(name)

    def get_raw(self):
        s = ''
        for name, size, typ in self.struct:        
            v = self.fields[name]['value']
            pad_func = typ == 'N' and right or left
            if typ == 'N':
                v = v or 0
                try:
                    i = int(v)
                except:
                    print name, size, typ, v
                    sys.exit()
                if v == i:
                    v = i
            else:
                v = v or ''
            s += pad_func(v, size)
        return s

    def set_raw(self, raw):
        awal = 0
        for t in self.struct:
            name = t[0]
            size = t[1:] and t[1] or 1
            akhir = awal + size
            value = raw[awal:akhir]
            if not value:
                return
            self.set(name, value)
            awal += size
        return True

    def from_dict(self, d):
        for name in d:
            value = d[name]
            self.set(name, value)
        