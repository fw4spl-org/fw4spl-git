#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Make sure you do not commit TAB, CRLF, ... in matching pattern files.

.gitconfig configuration :

[fw4spl-hooks]
    hooks = crlf tab digraphs doxygen

[forbidtoken-hooks]
    crlf= *.cpp *.hpp *.xml
    lgpl= *.cpp *.hpp *.xml
    tab= *.cpp *.xml *.py

To do the same check on a server to prevent CRLF/CR from being
pushed or pulled:

Default file pattern is '*'. To specify patterns to check :

"""

import re
from functools import partial

import common

BAD_WORDS_LIST = [
    'copain',
    'zizi',
    'bite',
    'couille',
    'fuck',
    'toto',
    'tutu',
    'titi',
]

CRLF = lambda x: '\r\n' in x
CR = lambda x: '\r' in x
TAB = lambda x: '\t' in x
LGPL = lambda x: 'Lesser General Public License' in x
BSD = lambda x: 'under the terms of the BSD Licence' in x
SLM_LOG = lambda x: bool(
    ('O''SLM_LOG' in x) and not (re.search('#define O''SLM_LOG', x) and x.count('O''SLM_LOG') == 1)
)
DIGRAPH = lambda x: "<:" in x or ":>" in x
DOXYGEN = lambda x: '* @class' in x or '* @date' in x or '* @namespace' in x
BADWORDS = lambda x: any( re.search(r'\b'+bad+r'\b', x, re.IGNORECASE) for bad in BAD_WORDS_LIST )

tr = {
    'crlf': (CRLF, 'CRLF line endings', '*.cpp *.hpp *.hxx *.cxx *.c *.h *.xml *.txt *.cmake *.py'),
    'cr': (CR, 'CR line endings', '*.cpp *.hpp *.hxx *.cxx *.c *.h *.xml *.txt *.cmake *.py'),
    'tab': (TAB, 'TAB', '*.cpp *.hpp *.hxx *.cxx *.c *.h *.xml *.txt *.cmake *.py'),
    'lgpl': (LGPL, 'LGPL Header', '*.cpp *.hpp *.hxx *.cxx *.c *.h *.xml *.txt *.cmake'),
    'bsd': (BSD, 'BSD Header', '*.cpp *.hpp *.hxx *.cxx *.c *.h *.xml *.txt *.cmake'),
    'oslmlog': (SLM_LOG, 'O''SLM_LOG', '*.cpp *.hpp *.hxx *.cxx *.c *.h'),
    'digraphs': (DIGRAPH, 'Forbiden digraphs: <'':, :''>', '*.cpp *.hpp *.hxx *.cxx *.c *.h'),
    'doxygen': (DOXYGEN, '@class @date @namespace doxygen tag(s)', '*.cpp *.hpp *.hxx *.cxx *.c *.h'),
    'badwords': (BADWORDS, 'Forbidden word in our code', '*.cpp *.hpp *.hxx *.cxx *.c *.h'),
}

WARNING = ('Attempt to commit or push text file(s) containing "%s"')
FILEWARN = ('   - %s:%s')


def forbidtoken(files, config_name):
    include_patterns = common.get_option('forbidtoken-hook.' + config_name, default=tr[config_name][2]).split()

    common.note('Checking for "' + config_name + '" tokens on ' + ', '.join(include_patterns) + ' files')
    abort = False
    token = tr[config_name][0]
    line_iter = lambda x: enumerate(re.finditer(".*\n", x, re.MULTILINE), 1)
    line_match = lambda test, x: (n for n, m in line_iter(x) if test(m.group()))

    count = 0
    for f in files:
        if not any(f.fnmatch(p) for p in include_patterns):
            continue
        common.trace('Checking ' + str(f.path) + '...')
        content = f.contents
        if not common.binary(content) and token(content):
            if not abort:
                common.error(WARNING % (tr[config_name][1]))
            for n in line_match(token, content):
                common.error(FILEWARN % (f.path, n))
            abort = True
        count += 1

    if abort:
        common.error('Hook "' + config_name + '" failed.')

    common.note('%d file(s) checked.' % count)

    return abort


hooks = dict(
    [(name, partial(forbidtoken, config_name=name)) for name in tr]
)
