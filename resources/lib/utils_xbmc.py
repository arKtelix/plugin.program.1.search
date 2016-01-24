__author__ = 'Justin'


def uni(string, encoding = 'utf-8'):
    if isinstance(string, basestring):
        if not isinstance(string, unicode):
            string = unicode(string, encoding, 'ignore')
    return string

def ascii(string, encoding = 'ascii'):
    if isinstance(string, unicode):
        string = string.encode('ascii', errors='ignore')
    return string
