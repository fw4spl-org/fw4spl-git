'''hooks to prevent adding too big binary file

.gitconfig configuration :

[fw4spl-hooks]
    hooks = crlf tab digraphs doxygen

example for 10MB limit :
[filesize-hook]
max_size = 10485760

All files are checked by default. To check only binray files, use the type option :
[filesize-hook]
type = binary

'''

import common

WARNING   = ('Attempt to commit or push too big file(s). '
              'Limit is: %s bytes')
FILEWARN  = ('   - %s, %s > %s')

def filesize( files ):
    abort = False
    limit = int(common.get_option('filesize-hook.max-size', default=2048**2))
    check_all_files = common.get_option('filesize-hook.type', "all").strip().lower() != "binary"
    too_big_files = []

    for f in files:
        content = f.contents
        check_file = check_all_files or common.binary(f.contents)

        if check_file:
            common.note('Checking ' + str(f.path) + ' size...')

            if f.size > limit:
                too_big_files.append(f)

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

