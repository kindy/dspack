
import sys
import re
from cStringIO import StringIO
from struct import Struct, pack, unpack
 
F4 = 0xFFFF
F8 = 0xFFFFFFFF
MAX_LEN = 0xFFFFFFFFFFFFFFFF >> 1
BIG_LEN = 0xFFFFFFFF >> 1
BIG_LEN_PAD = 1 << 63

len_struct = Struct('!I')
big_len_struct = Struct('!Q')

class FieldSchemaError(TypeError):
    pass

class TooLongError(ValueError):
    pass

def wlen(n):
    if n <= BIG_LEN:
        return len_struct.pack(n)

    if n > MAX_LEN:
        raise TooLongError()

    return big_len_struct.pack(BIG_LEN_PAD + n)

def rlen(s, offset=0):
    n = len_struct.unpack(s[offset:offset + 4])[0]
    if (n >> 31) < 1:
        return 4, n

    return 8, big_len_struct.unpack(s[offset:offset + 8])[0] - BIG_LEN_PAD

assert wlen(12345) == '\x00\x0009', 'wlen not ok'
assert wlen(0xFFFFFFFF12345) == '\x80\x0f\xff\xff\xff\xf1#E', 'wlen for big not ok'
assert rlen(wlen(12345)) == (4, 12345), 'rlen not ok'
assert rlen(wlen(0xFFFFFFFF12345)) == (8, 0xFFFFFFFF12345), 'rlen for big not ok'


class Field(object):

    def __init__(self, typ, fixed=True, len_=None, id_=None, note=None):
        self.typ = typ
        self.fixed = fixed
        self.len = len_
        self.is_list = False
        self.id = id_
        self.note = note

    def __str__(self):
        return '%s: %s' % (self.id, self.typ)

class ListField(object):

    def __init__(self, typ, fixed=True, len_=None, id_=None, note=None):
        self.is_list = True
        self.typ = typ
        self.fixed = fixed
        self.len = len_
        self.id = id_
        self.note = note

    def __str__(self):
        return '%s: %s[]' % (self.id, self.typ.typ)


class Pack(object):

    def __init__(self, fmt):
        self.fmt = fmt
        self.parse_fmt(fmt)
        self._buf = StringIO()

    def parse_fmt(self, fmt):
        '''
            ._fmts ()
                fixed:
                fmt: 'D2H23J'
                count: (1, 2, 23)
            ._fields ()
            ._field_ids = ()

        fixed-len string    - raw data
        dyn string          - <data-len>raw data
        fixed-len list
            fixed-len string- raw data
            dyn string      - <list-data-len><data-len>raw data<data-len>raw data...
        dyn list
            fixed-len string- <list-len>raw data
            dyn string      - <list-data-len><data-len>raw data<data-len>raw data...

        dynamic string || dynamic list || (fixed list with dynamic string)
        '''
        fmt = fmt.lstrip()
        flag = fmt[0]
        if flag in '@=<>!':
            fmt = fmt[1:]
        else:
            flag = '!'

        self.flag = flag

        _fmts = []
        _fmt = None

        re_field = r'''
            (?P<list>(?P<llen>\d+|~)?:)?
            (?P<len>\d+|~)?(?P<typ>[a-zA-Z])
            (?:
                \(
                    (?P<id>[a-zA-Z_][a-zA-Z_0-9]*)
                    (?P<note>[^\)]*)
                \)
            )?'''
        field_n = 0
        _fields = []
        for m in re.finditer(re_field, fmt, re.X):
            field_n += 1
            list_, llen, len_, typ, id_, note = m.groups()
            fixed = True

            if len_:
                if typ not in 'spS':
                    raise FieldSchemaError('typ: %s have no length' % typ)

                if len_ == '~':
                    fixed = False
                else:
                    len_ = int(len_)
                    if len_ < 1:
                        raise FieldSchemaError('length of typ: %s should >= 1' % typ)

            if not id_:
                id_ = 'f%d' % field_n

            if note:
                note = note.lstrip() or None

            _field = Field(typ, fixed=fixed, len_=len_, id_=id_, note=note)

            if list_:
                if not llen or llen == '~':
                    fixed = False
                else:
                    fixed = True
                    llen = int(llen)
                    if llen < 1:
                        raise FieldSchemaError('length of list: %s should >= 1' % typ)

                _field = ListField(typ=_field, fixed=fixed, len_=len_,
                        id_=id_, note=note)

            _fields.append(_field)

        for x in _fields:
            print x


    def help(self):
        pass

    def clear(self):
        pass

    def addRow(self, *rows, **row):
        if row:
            self.addKWRow(row)

    def addRows(self, rows):
        x

    def getData(self):
        pass


def dumps(fmt, rows):
    p = Pack(fmt)
    p.addRows(rows)

    return p.getData()


def _test():
    _fmt = '''
    ! H(day) B(device) B(feed) 3S(country) I(category)
    ~:Q(app_ids) ~:H(changes App's rank change)
    '''
    p = Pack(_fmt)

    '''
    print repr(dumps(, [
        [123, 2, 2, 'CN', 123654,
            [123, 231, 1213], [1, 2, 0]
        ],
        [123, 2, 2, 'CN', 123654,
            [123, 231, 1213], [1, 2, 0]
        ],
    ]))
    '''

_test()

'''
    rank_struct = Struct('B3sIBBH')
    null_change = -32767
 
    for f in glob.glob('20130801-143441-*'):
        data = loads(zlibd(open(f, 'rb').read()))
 
        day = 123
        c = 'CN '
        cat = 12345
 
        # print 'ing: ', f
 
        for dev_feed, ranks in data.items():
            len_ = len(ranks)
            buf.write(rank_struct.pack(day, c, cat, 2, 2, len_))
            app_ids = []
            changes = []
            for app_id, change in ranks:
                app_ids.append(app_id)
                changes.append(change if change is not None else null_change)
 
            buf.write(pack('%dQ' % len_, *app_ids))
            buf.write(pack('%dh' % len_, *changes))
 
    print buf.getvalue()
    buf.close()
 
convert()
'''
