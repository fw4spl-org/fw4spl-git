#!/usr/bin/python2
# -*- coding: utf-8 -*-

"""
Cppcheck your code.

.gitconfig configuration :

[fw4spl-hooks]
    hooks = cppcheck

[cppcheck]
    source-patterns = *.cpp *.cxx *.c
    header-patterns = *.hpp *.hxx *.h
    cppcheck-path="C:/Program Files/Cppcheck/cppcheck.exe"
"""

import os
import re
import subprocess
import common

from fnmatch import fnmatch

SEPARATOR       = '%s\n' % ('-'*79)
CPPCHECK_PATH   = 'cppcheck'

#------------------------------------------------------------------------------

# Can we run cppcheck ?
def check_cppcheck_install():
    p = subprocess.Popen([CPPCHECK_PATH, '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.communicate()

    return p.wait() != 0

#------------------------------------------------------------------------------

# Return True if cppcheck find errors in specified file
def check_file(file):
    
    common.note( 'Checking with ' + CPPCHECK_PATH + ' file: ' + file )
    
    # Invoke cppcheck for source code files
    p = subprocess.Popen([CPPCHECK_PATH, \
                          '--suppress=missingInclude', \
                          '--suppress=noExplicitConstructor', \
                          '--suppress=unmatchedSuppression', \
                          '--suppress=unusedFunction', \
                          '--enable=all', '--quiet', \
                          '--template={file}@!@{line}@!@{severity}@!@{message}', \
                          file], \
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = p.communicate()
    
    
    if err != None:
        print( err )
        
    if out != None:
        print( out )

    if p.wait() != 0:
        common.error( 'Cppcheck failure on file: ' + file )
        common.error( 'Aborting' )
        return True

    if out:
        common.error( 'Cppcheck failure on file: ' + file )
        for line in out.splitlines():
            words = re.findall('(.+)@!@(.+)@!@(.+)@!@(.+)', line)
            if(words):
                num_line = words[0][1]
                severity = words[0][2]
                message  = words[0][3]
                common.error( '[%s] line %s: %s' % (severity, num_line, message) )
                common.error( SEPARATOR )
        return True

    return False

#------------------------------------------------------------------------------

def cppcheck(files):
    abort = False
    source_patterns = common.get_option('cppcheck-hook.source-patterns', default='*.cpp *.cxx *.c').split()
    header_patterns = common.get_option('cppcheck-hook.header-patterns', default='*.hpp *.hxx *.h').split()

    code_patterns = source_patterns + header_patterns

    global CPPCHECK_PATH
    
    if common.g_cppcheck_path_arg != None and len( common.g_cppcheck_path_arg ) > 0:
        CPPCHECK_PATH = common.g_cppcheck_path_arg
    else:
        CPPCHECK_PATH = common.get_option('cppcheck-hook.cppcheck-path', default=CPPCHECK_PATH, type='--path').strip()
    
    if check_cppcheck_install():
        common.error('Failed to launch cppcheck.=')
        return True

    repoRoot = common.get_repo_root()
    for f in files:
        if any(fnmatch(f.path.lower(), p) for p in code_patterns):

            if not common.binary(f.contents):
                file = os.path.join(repoRoot, f.path)
                abort = check_file(file) or abort

    return abort

hooks = {
        'cppcheck':cppcheck,
        }
