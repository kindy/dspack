<a name="start"/>
# DataSetPack Specification

DataSetPack is an data set serialization specification like binary-packed csv.
It can be used as data storage or transfer format.

Core Concept in DataSetPack are **schema** and **row**, a little like in a SQL system.

Schema define items in row, each item has type and length info.
and, schema info can be embed in data, so the data can be unpack it-self.

This document describes the DataSetPack schema and data formats.

## Table of contents

* [DataSetPack specification](#start)
  * [Schema](#schema)
      * [Type](#schema-type)
      * [Length](#schema-length)
  * [Formats](#formats)
      * [Overview](#formats-overview)
      * [Meta Info](#formats-meta)
      * [Row Info](#formats-row)
      * [Field Info](#formats-field)
  * [Serialization: data to format conversion](#serialization)
  * [Deserialization: format to data conversion](#deserialization)

<a name="schema"/>
## Schema

| Character | Byte order             | Size     | Alignment |
| @	        | native                 | native   | native    |
| =         | native                 | standard | none      |
| <         | little-endian          | standard | none      |
| >         | big-endian             | standard | none      |
| !         | network (= big-endian) | standard | none      |


```
schema ::= flag { field }
flag   ::= `!´ | `@´ | `=´ | `<´ | `>´
field  ::= (list | single) [ @desc ]
list   ::= { (Int | `~´) } `:´ single
single ::= { (Int | `~´) } strtyp | notstrtyp
strtyp ::= `s´ | `p´
notstrtyp ::= (Char - strtyp)
desc   ::= `(´ Indent [ ` ´ { All - `)´ } ] `)´
```

Notes:

* spacing is always ignore unless in desc.

### Example

```
! H(day) B(device) B(feed) 3s(country) I(category)
  2~:Q(app_ids) 2~:H(changes App's rank change)
```

number before string tell that how long this string is.
if a `~` follow by the number, it means the length of string is dynamic.
the mean of number change to bytes to save or read the following string.

number has same means for list.

field `2~:Q(app_ids)` means `app_ids` is a list of big int, with max length of `pow(2, 2 * 8)`(`65535`).

we can save multiple `dict` in one row:

`:~s(meta_keys) :~s(meta_vals Used with meta_keys)`


string:

```
s   - 1 byte string
~s  - dynamic length string, read length begin 1 byte.
2~s - dynamic length string, read length begin 2 byte.
12s - 12 bytes string.
```

list:

```
B    - one unsigned char
:B   - list of unsigned char with dynamic length, read length begin 1 byte.
~:B  - same as :B .
10:B - a list with 10 unsigned char.
2~:B - list of unsigned char with dynamic length, read length begin 2 byte.
```

Note: `B` in list can be replace by string.

```
Format(ssize)   C Type              Python type         Notes
x  1            pad byte            no value             
c  1            char                string of length 1   
b  1            signed char         integer             (3)
B  1            unsigned char       integer             (3)
?  1            _Bool               bool                (1)
h  2            short               integer             (3)
H  2            unsigned short      integer             (3)
i  4            int                 integer             (3)
I  4            unsigned int        integer             (3)
l  4            long                integer             (3)
L  4            unsigned long       integer             (3)
q  8            long long           integer             (2), (3)
Q  8            unsigned long long  integer             (2), (3)
f  4            float               float               (4)
d  8            double              float               (4)
s               char[]              string               
p               char[]              string               
S               char[]              string              (*) auto trim tail '\0'
P               void *              integer             (5), (3)
```

Notes:

* For the `f` and `d` conversion codes, the packed representation uses the IEEE 754 binary32 (for `f`) or binary64 (for `d`) format,
  regardless of the floating-point format used by the platform.



``` python
from dspack import DsPack

p = DsPack.new('''
    ! H(day) B(device) B(feed) 3S(country) I(category)
      2~:Q(app_ids) 2~:H(changes App's rank change)
''')

p.addRow([234, 1, 2, 'CN', 12345, [12345, 23456], [2, 1]])
# or more clear:
p.addRow(day=234, device=1, feed=2, country='CN', category=12345, app_ids=[12345, 23456], changes=[2, 1])
```


## storage format

```
data     ::= meta_length meta { row_data }
row_data ::= row_length row
```

when some time read `row_length` as `0` but `src` not reach `eof`, parser will restart again(looking for `meta_length`).

at begin, read meta head length from first 2 bytes, if all bits is 1, read 2 more bytes.
when got meta head length, read meta info.

in meta info:

* version info
* schema info
* description
* dict-style meta


`row` struct depends on `schema`.
at default, parser will unpack first part of fixed length fileds.
you can ask parser unpack all fields when read `row` data.

``` python
from dspack import DsPack

data = ...
p = DsPack.load(data)

for row in p.iter():
    print row

for day, device, feed, country, category, app_ids, changes in p.iter():
    print app_ids

```

___

    DataSetPack specification
    Kindy Lin © 2013

