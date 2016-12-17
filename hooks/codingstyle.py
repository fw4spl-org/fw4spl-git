"""
Make sure you respect the minimal coding rules and gently reformat files for you.

.gitconfig configuration :

[fw4spl-hooks]
    hooks = codingstyle

Available options are :
source-patterns : file patterns to process as source code files - default to *.cpp *.cxx *.c
header-patterns : file patterns to process as header files - default to *.hpp *.hxx *.h
misc-patterns : file patterns to process as non-source code files (build, configuration, etc...)
                Reformatting is limited to TABs and EOL - default to *.options *.cmake *.txt *.xml
uncrustify-path : path to the uncrustify program - default to uncrustify

[coding-style]
source-patterns = *.cpp *.cxx *.c
header-patterns = *.hpp *.hxx *.h
misc-patterns = *.options *.cmake *.txt *.xml *.json
uncrustify-path=C:\Program files\uncrustify\uncrustify.exe

"""

import os, sys
import re
import datetime
import subprocess
import hashlib
import difflib
import shutil
import string
import common

import sortincludes

from common import FormatReturn
from fnmatch import fnmatch
from functools import partial

YEAR            = datetime.date.today().year
SEPARATOR       = '%s\n' % ('-'*79)
FILEWARN        = lambda x : ('  - %s') % os.path.relpath(x, repoRoot)
UNCRUSTIFY_PATH = 'uncrustify'
BACKUP_LIST_FILE= 'backupList'

LICENSE = '/\* \*\*\*\*\* BEGIN LICENSE BLOCK \*\*\*\*\*\n\
 \* FW4SPL - Copyright \(C\) IRCAD, (.*).\n\
 \* Distributed under the terms of the GNU Lesser General Public License \(LGPL\) as\n\
 \* published by the Free Software Foundation.\n\
 \* \*\*\*\*\*\* END LICENSE BLOCK \*\*\*\*\*\* \*/'


#------------------------------------------------------------------------------

def fix_license_year(file, enableReformat):
    strOldFile = open(file, 'rb').read()

    common.trace( 'Checking for LGPL license in: ' + file )

    # Look for the license pattern
    match = re.search(LICENSE, strOldFile, re.MULTILINE)
    if match == None:
        common.error( 'LGPL license header missing in : ' + file + '.' )
        return FormatReturn.Error

    LICENSE_YEAR = r"(.*)FW4SPL - Copyright \(C\) IRCAD, ([0-9]+)-([0-9]+)."
    LICENSE_YEAR_REPLACE =  r"\1FW4SPL - Copyright (C) IRCAD, \2-"+str(YEAR)+"."

    strNewFile = re.sub(LICENSE_YEAR, LICENSE_YEAR_REPLACE, strOldFile)

    if strNewFile != strOldFile:
        if enableReformat:
            common.note( 'Licence year fixed in : ' + file )
            open(file, 'wb').write(strNewFile)
            return FormatReturn.Modified
            return FormatReturn.NotModified
        else:
            common.error( 'Licence year in : ' + file + ' is not up-to-date.' )
            return FormatReturn.Error

    return FormatReturn.NotModified

#------------------------------------------------------------------------------

# Reformat file according to minimal coding-style rules
# Return True if anything as been modified along with a unified diff
def format_file(file, enableReformat, code_patterns, header_patterns, misc_patterns, checkLGPL, sortIncludes):

    diff = ''

    # Invoke uncrustify for source code files
    if any(fnmatch(file, p) for p in code_patterns):

        common.trace( 'Launching uncrustify on : ' + file )
        configFileName = os.path.join(os.path.dirname( __file__ ), 'uncrustify.cfg')

        ret = FormatReturn()

        command = UNCRUSTIFY_PATH + ' -c ' + configFileName +  ' -q %s ' + file

        if(enableReformat):
            # Check first
            uncrustify = common.execute_command(command % '--check' )

            if uncrustify.status:
                uncrustify = common.execute_command(command % '--replace --no-backup')
                if uncrustify.status:
                    common.error( 'Uncrustify failure on file: '+ file )
                    return FormatReturn.Error
                ret.add( FormatReturn.Modified )
        else:
            uncrustify = common.execute_command(command % '--check')

            if uncrustify.status:
                common.error( 'Uncrustify failure on file: '+ file )
                return FormatReturn.Error

        # Fix license year
        if checkLGPL:
            ret.add( fix_license_year(file, enableReformat) )

        # Sort headers
        if sortIncludes:
            ret.add( sortincludes.sort_includes(file, enableReformat) )

        if any(fnmatch(file, p) for p in header_patterns):
            ret.add( fix_header_guard(file, enableReformat) )

        return ret.value

    # Replace only YEAR, TAB, CRLF and CR for miscellaneous files
    elif any(fnmatch(file, p) for p in misc_patterns):

        common.trace( 'Parsing: ' + file + ' to replace CR, CRLF and TABs' )

        strOldFile = open(file, 'rb').read()

        strNewFile = re.sub('\t', '    ', strOldFile)
        str = re.sub('\r\n', '\n', strNewFile)
        strNewFile = re.sub('\r', '\n', str)

        if strOldFile == strNewFile:
            return FormatReturn.NotModified

        # Something has been changed, write the new file
        newFile = open(file, 'wb').write(strNewFile)
        return FormatReturn.Modified

#------------------------------------------------------------------------------

# Check the header guard consistency
def fix_header_guard(path, enableReformat):

    ret = FormatReturn()

    file = open(path, 'r')
    content = file.read()
    file.close()

    # Assume the first ifndef is the first header guard
    match = re.search('#ifndef +(_*(?:[0-9A-Z]+_*)*)$', content, re.MULTILINE)
    if match == None:
        common.error("Can't find header guard, maybe check the naming convention ?")
        common.error(FILEWARN(path))
        return FormatReturn.Error

    guard = match.group(1)

    # Now check that the guard name follows the file name
    fileupper = path.upper()

    match = re.search('(?:(?:INCLUDE\/)|(?:SRC\/)).*', fileupper)
    if match == None:
        common.error("warning: can't find 'src' or 'include' in the file path." )
        common.error("         Header guard naming check skipped." )
        common.error(FILEWARN(path))

    else:

        # look if this is a unit test
        testMatch = re.search('([^\/]*)(?:\/TEST\/TU\/INCLUDE)(.*)', fileupper)

        if testMatch:
            expectedGuard = '__' + testMatch.group(1) + '_' + 'UT' + re.sub('/|\.', '_',  testMatch.group(2)) + '__'
        else:

            # find the last interesting part of the path (we can have SRC or INCLUDE multiple times)
            splitBySrc = string.split(fileupper, 'SRC/')[-1]
            splitByInc = string.split(fileupper, 'INCLUDE/')[-1]
            if len(splitBySrc) < len(splitByInc):
                fileupper = splitBySrc
            else:
                fileupper = splitByInc
            expectedGuard = '__' + re.sub('/|\.', '_',  fileupper) + '__'

        if guard != expectedGuard:
            common.note(FILEWARN(path))

            strNewFile = re.sub(r"([^_])" + guard, r"\1" + expectedGuard, content)

            if strNewFile != content:
                if enableReformat:
                    open(path, 'wb').write(strNewFile)
                    content = strNewFile
                    common.note("The header guard does not follow our naming convention." )
                    common.note("    Replacing " + guard + " by " + expectedGuard + " ." )
                    ret.add(FormatReturn.Modified)
                else:
                    common.error("The header guard does not follow our naming convention." )
                    return FormatReturn.Error


        match = re.search('#define +' + expectedGuard, content, re.MULTILINE)
        if match == None:
            common.error("Can't find #define header guard matching : " + expectedGuard)
            common.error(FILEWARN(path))
            return FormatReturn.Error

        match = re.search('#endif */[/\*] *' + expectedGuard + '(?:.*\*/)?', content, re.MULTILINE)
        if match == None:
            common.error("Can't find #endif with a comment matching the header guard  : " + expectedGuard + "\n")
            common.error(FILEWARN(path))
            return FormatReturn.Error
    
    return ret.value

#------------------------------------------------------------------------------

def codingstyle( files, enableReformat ):

    source_patterns = common.get_option('codingstyle-hook.source-patterns', default=['*.cpp','*.cxx','*.c'])
    header_patterns = common.get_option('codingstyle-hook.header-patterns', default=['*.hpp','*.hxx','*.h'])
    misc_patterns = common.get_option('codingstyle-hook.misc-patterns', default=['*.options','*.cmake','*.txt', '*.xml'])

    code_patterns = source_patterns + header_patterns
    include_patterns = code_patterns + misc_patterns

    checkLGPL = common.is_LGPL_repo()
    sortIncludes = common.get_option('codingstyle-hook.sort-includes', default="true", type='--bool') == "true"
    global UNCRUSTIFY_PATH
    UNCRUSTIFY_PATH = common.get_option('codingstyle-hook.uncrustify-path', default=UNCRUSTIFY_PATH, type='--path').strip()

    if common.execute_command(UNCRUSTIFY_PATH + ' -v -q').status:
        common.error('Failed to launch uncrustify.\n')
        return []

    checked  = set()

    reformatedList = []
    global repoRoot
    repoRoot = common.get_repo_root()

    sortincludes.find_libraries_and_bundles(repoRoot)

    ret = False
    count = 0
    countReformat = 0
    for f in files:
        if f in checked or not any(f.fnmatch(p) for p in include_patterns):
            continue

        content = f.contents
        if not common.binary(content):

            # Do this last because contents of the file will be modified by uncrustify
            # Thus the variable content will no longer reflect the real content of the file
            file = os.path.join(repoRoot, f.path)
            res = format_file(file, enableReformat, code_patterns, header_patterns, misc_patterns, checkLGPL, sortIncludes)
            count = count + 1
            if res == FormatReturn.Modified:
                reformatedList.append(f.path)
                countReformat = countReformat + 1
            elif res == FormatReturn.Error:
                # Error in reformatting
                ret = True

        checked.add(f)

    common.note('%d file(s) checked, %d file(s) reformatted.' % (count, countReformat) )

    return ret, reformatedList


