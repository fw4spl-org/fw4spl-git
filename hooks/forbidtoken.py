"""
Make sure you do not commit TAB, CRLF, ... in matching pattern files.

.gitconfig configuration :

[fw4spl-hooks]
    hooks = crlf tab digraphs doxygen

To do the same check on a server to prevent CRLF/CR from being
pushed or pulled:

Default file pattern is '*'. To specify patterns to check :

[forbidtoken-hooks]
crlf= *.cpp *.hpp *.xml
lgpl= *.cpp *.hpp *.xml
tab= *.cpp *.xml *.py
"""

import re

from functools import partial

import common

CRLF    = lambda x : '\r\n' in x
CR      = lambda x : '\r' in x
TAB     = lambda x : '\t' in x
LGPL    = lambda x : 'Lesser General Public License' in x
BSD     = lambda x : 'under the terms of the BSD Licence' in x
SLM_LOG = lambda x : bool(
        ('O''SLM_LOG' in x) and not (re.search('#define O''SLM_LOG', x) and x.count('O''SLM_LOG') == 1)
        )
DIGRAPH = lambda x : "<:" in x or ":>" in x
DOXYGEN = lambda x : '* @class' in x or '* @date' in x or '* @namespace' in x
COPAIN = lambda x : 'copain' in x

tr = {
               'crlf' : (CRLF    , 'CRLF line endings'   ),
                 'cr' : (CR      , 'CR line endings'     ),
                'tab' : (TAB     , 'TAB'                 ),
               'lgpl' : (LGPL    , 'LGPL Header'         ),
                'bsd' : (BSD     , 'BSD Header'          ),
            'oslmlog' : (SLM_LOG , 'O''SLM_LOG'          ),
           'digraphs' : (DIGRAPH , 'Forbiden digraphs: <'':, :''>'),
            'doxygen' : (DOXYGEN , '@class or @date doxygen tag(s)' ),
             'copain' : (COPAIN  , 'copain' ),
     }


WARNING   = ('Attempt to commit or push text file(s) containing "%s"')
FILEWARN  = ('   - %s:%s')

def forbidtoken( files, config_name ):
    include_patterns = common.get_option('forbidtoken-hooks.' + config_name, default='*').split()

    common.note('Checking for "' + config_name + '" tokens on ' + ', '.join(include_patterns) + ' files')
    abort   = False
    token   = tr[config_name][0]
    line_iter = lambda x:enumerate( re.finditer(".*\n", x, re.MULTILINE), 1 )
    line_match = lambda test, x:(n for n,m in line_iter(x) if test(m.group()))

    for f in files:
        if not any(f.fnmatch(p) for p in include_patterns):
            continue
        content = f.contents
        if not common.binary(f.contents) and token(content):
            if not abort:
                common.error(WARNING % (tr[config_name][1]))
            for n in line_match(token, content):
                common.error(FILEWARN % (f.path, n))
            abort = True

    if abort:
        print('\n')
        common.error('Hook "' + config_name + '" failed.\n')

    return abort

hooks = dict(
        [ (name, partial(forbidtoken, config_name = name)) for name in tr ]
        )

