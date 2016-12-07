'''hooks to prevent adding too big binary file

.gitconfig configuration :

[fw4spl-hooks]
    hooks = crlf tab digraphs doxygen

example for 10MB limit :
[filesize-hook]
max_size = 10485760

Only binary files are checked by default. To check every files, use the type option :
[filesize-hook]
type = all

'''

import common

WARNING   = ('Attempt to commit or push too big file(s). '
              'Limit is: %s bytes\n')
FILEWARN  = ('   - %s, %s > %s\n')

def filesize( files ):
    abort = False
    limit = int(common.get_option('filesize-hook.max-size', default=1024**2))
    check_all_files = common.get_option('filesize-hook.type', "binary").strip().lower() == "all"
    too_big_files = []

    for f in files:
        content = f.contents
        check_file = check_all_files or common.binary(f.contents)

        if check_file:
            common.note('Checking ' + str(f.path) + ' size...')

            if f.size > limit:
                too_big_files.append(f)
                common.note('too big')
            else:
                common.note('ok')

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

