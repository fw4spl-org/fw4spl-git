#!/usr/bin/python2
# -*- coding: utf-8 -*-

'''hooks to prevent adding too big binary file

.gitconfig configuration :

[fw4spl-hooks]
    hooks = crlf tab digraphs doxygen

example for 10MB limit :
[filesize-hook]
    max-size = 10485760

All files are checked by default. To check only binary files, use the type option :
[filesize-hook]
    type = binary
'''

import common

WARNING   = ('Attempt to commit or push too big file(s). '
              'Limit is: %s bytes')
FILEWARN  = ('   - %s, %s > %s')

def filesize( files ):
    abort = False
    limit = int(common.get_option('filesize-hook.max-size', default=1024**2))
    check_all_files = common.get_option('filesize-hook.type', "all").strip().lower() != "binary"
    too_big_files = []

    common.note('Checking files size...')

    count = 0
    for f in files:
        check_file = check_all_files or common.binary(f.contents)

        if check_file:
            common.trace('Checking ' + str(f.path) + ' size...')

            count = count + 1
            if f.size > limit:
                too_big_files.append(f)

    common.note('%d file(s) checked.' % count)

    if too_big_files:
        common.error(WARNING % limit)
        for f in too_big_files:
            common.error(FILEWARN % (
                f.path,
                f.size,
                limit
                ))
        abort = True
    return abort

hooks = {
        'filesize':filesize,
        }

