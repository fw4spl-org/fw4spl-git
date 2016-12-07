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
LGPL-check : check is the LGPL header is correct and mention the current year (since it has been modified)
show-diff : if something has been reformatted, display a diff of all the modifications at the end - default to yes
autoclean : automatically remove backup files when a commit succeeds - default to yes
uncrustify-path : path to the uncrustify program - default to uncrustify

[coding-style]
source-patterns = *.cpp *.cxx *.c
header-patterns = *.hpp *.hxx *.h
misc-patterns = *.options *.cmake *.txt *.xml *.json
LGPL-check=yes
show-diff=yes
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

from fnmatch import fnmatch
from functools import partial

YEAR            = datetime.date.today().year
SEPARATOR       = '%s\n' % ('-'*79)
WARNING_LIC     = ('Attempt to commit or push code file(s) where LGPL is missing')
WARNING_YEAR    = ('Attempt to commit or push code file(s) where year "%s" is missing in the LGPL')
FILEWARN        = lambda x : ('  - %s') % os.path.relpath(x, repoRoot)
UNCRUSTIFY_PATH = 'uncrustify'
BACKUP_LIST_FILE= 'backupList'

NEWFILE         = lambda x : x + '.hg-new'
OLDFILE         = lambda x : x + '.hg-old'

LICENSE = '/\* \*\*\*\*\* BEGIN LICENSE BLOCK \*\*\*\*\*\n\
 \* FW4SPL - Copyright \(C\) IRCAD, (.*).\n\
 \* Distributed under the terms of the GNU Lesser General Public License \(LGPL\) as\n\
 \* published by the Free Software Foundation.\n\
 \* \*\*\*\*\*\* END LICENSE BLOCK \*\*\*\*\*\* \*/'

#------------------------------------------------------------------------------

# Check the LGPL block with the correct year
def check_license(content, file):

    common.note( 'Parsing: ' + file + ' to check LGPL block' )

    # Look for the license pattern
    match = re.search(LICENSE, content, re.MULTILINE)
    if match == None:
        common.error(WARNING_LIC)
        common.error(FILEWARN(file))
        return True

    # Look if the current year is mentioned
    dateStr = match.group(1)
    matches = re.findall('20\d+', dateStr)

    if str(YEAR) not in matches:
        common.error(WARNING_YEAR)
        common.error(FILEWARN(file))
        return True

    return False

#------------------------------------------------------------------------------

def fix_license_year(file):
    strOldFile = open(file, 'rb').read()

    common.note( 'Parsing: ' + file + ' to replace license year' )

    LICENSE_YEAR = r"(.*)FW4SPL - Copyright \(C\) IRCAD, ([0-9]+)-([0-9]+)."
    LICENSE_YEAR_REPLACE =  r"\1FW4SPL - Copyright (C) IRCAD, \2-"+str(YEAR)+"."

    strNewFile = re.sub(LICENSE_YEAR, LICENSE_YEAR_REPLACE, strOldFile)

    if strNewFile != strOldFile:
        open(file, 'wb').write(strNewFile)

#------------------------------------------------------------------------------

# Reformat file according to minimal coding-style rules
# Return True if anything as been modified along with a unified diff
def format_file(file, showDiff, code_patterns, header_patterns, misc_patterns, checkLGPL, sortIncludes):

    diff = ''

    # Invoke uncrustify for source code files
    if any(fnmatch(file, p) for p in code_patterns):

        configFileName = os.path.dirname( __file__ ) + '/uncrustify.cfg'
        newFile = NEWFILE(file)

        p = subprocess.Popen([UNCRUSTIFY_PATH, '-f' + file, '-c' + configFileName, '-o' + newFile, '-q'], \
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.communicate()

        if p.wait() != 0:
            common.error( '\nUncrustify failure\n File: '+ file +'\naborting\n' )
            return 2, diff

        # Fix license year
        if checkLGPL:
            fix_license_year(newFile)

        # Sort headers
        if sortIncludes:
            sortincludes.sort_includes(newFile)

        if any(fnmatch(file, p) for p in header_patterns):
            if fix_header_guard(newFile, file, ui):
                return 2, diff


        strNewFile = open(newFile, 'r').readlines()
        strOldFile = open(file, 'r').readlines()

        # Autoremove new file if there is no change
        if strNewFile == strOldFile:
            os.remove(newFile)

            return 0, diff

        # Generate the diff if needed
        if showDiff:
            genDiff = difflib.unified_diff(strOldFile, strNewFile, fromfile=file, tofile=newFile, n=3)

            for line in genDiff:
                diff += line

    # Replaces YEAR, TAB, CRLF and CR for miscellaneous files
    elif any(fnmatch(file, p) for p in misc_patterns):

        common.note( 'Parsing: ' + file + ' to replace CR, CRLF and TABs' )

        strOldFile = open(file, 'rb').read()

        strNewFile = re.sub('\t', '    ', strOldFile)
        str = re.sub('\r\n', '\n', strNewFile)
        strNewFile = re.sub('\r', '\n', str)

        if strOldFile == strNewFile:
            return 0, diff

        # Something has been changed, write the new file
        newFile = open(NEWFILE( file ), 'wb').write(strNewFile)

        # Generate the diff if needed
        if showDiff:
            strOldFile = strOldFile.splitlines(True)
            strNewFile = strNewFile.splitlines(True)
            genDiff = difflib.unified_diff(strOldFile, strNewFile, fromfile=file, tofile=NEWFILE( file ), n=3)

            for line in genDiff:
                diff += line

    return 1, diff

#------------------------------------------------------------------------------

# Check the header guard consistency
def fix_header_guard(path, originalPath, ui):

    common.note( 'Parsing: ' + path + ' to check and fix header guard' )

    file = open(path, 'r')
    content = file.read()
    file.close()

    # Assume the first ifndef is the first header guard
    match = re.search('#ifndef +(_*(?:[0-9A-Z]+_*)*)$', content, re.MULTILINE)
    if match == None:
        common.error("Can't find header guard, maybe check the naming convention ?")
        common.error(FILEWARN(originalPath))
        return True

    guard = match.group(1)

    # Now check that the guard name follows the file name
    fileupper = originalPath.upper()

    match = re.search('(?:(?:INCLUDE\/)|(?:SRC\/)).*', fileupper)
    if match == None:
        common.error("warning: can't find 'src' or 'include' in the file path." )
        common.error("         Header guard naming check skipped." )
        common.error(FILEWARN(originalPath))

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
            common.note(FILEWARN(originalPath))
            common.note("The header guard does not follow our naming convention." )
            common.note("    Replacing " + guard + " by " + expectedGuard + " ." )

            strNewFile = re.sub(r"([^_])" + guard, r"\1" + expectedGuard, content)

            if strNewFile != content:
                open(path, 'wb').write(strNewFile)
                content = strNewFile

        match = re.search('#define +' + expectedGuard, content, re.MULTILINE)
        if match == None:
            common.error("Can't find #define header guard matching : " + expectedGuard)
            common.error(FILEWARN(originalPath))
            return True

        match = re.search('#endif */[/\*] *' + expectedGuard + '(?:.*\*/)?', content, re.MULTILINE)
        if match == None:
            common.error("Can't find #endif with a comment matching the header guard  : " + expectedGuard + "\n")
            common.error(FILEWARN(originalPath))
            return True

    return False

#------------------------------------------------------------------------------

# Check the header guard consistency
def check_header_guard(content, file, ui):

    common.note( 'Parsing: ' + file + ' to check header guard' )

    # Assume the first ifndef is the first header guard
    match = re.search('#ifndef +(__(?:[0-9A-Z]+_)*[0-9A-Z]+__)$', content, re.MULTILINE)
    if match == None:
        common.error("Can't find header guard, maybe check the naming convention ?")
        common.error(FILEWARN(file))
        return True

    guard = match.group(1)

    # Now check that the guard name follows the file name
    fileupper = file.upper()

    match = re.search('(?:(?:INCLUDE\/)|(?:SRC\/)).*', fileupper)
    if match == None:
        common.error("warning: can't find 'src' or 'include' in the file path." )
        common.error("         Header guard naming check skipped." )
        common.error(FILEWARN(file))

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
            common.error("The header guard does not follow our naming convention.\n" )
            common.error(FILEWARN(file))
            common.error("    " + guard + " found, " + expectedGuard + " expected.\n" )
            return True

    match = re.search('#define +' + guard, content, re.MULTILINE)
    if match == None:
        common.error("Can't find #define header guard matching : " + guard + "\n")
        common.error(FILEWARN(file))
        return True

    match = re.search('#endif */[/\*] *' + guard + '(?:.*\*/)?', content, re.MULTILINE)
    if match == None:
        common.error("Can't find #endif with a comment matching the header guard  : " + guard + "\n")
        common.error(FILEWARN(file))
        return True

    return False

#------------------------------------------------------------------------------

def codingstyle( files ):

    source_patterns = common.get_option('codingstyle-hook.source-patterns', default=['*.cpp','*.cxx','*.c'])
    header_patterns = common.get_option('codingstyle-hook.header-patterns', default=['*.hpp','*.hxx','*.h'])
    misc_patterns = common.get_option('codingstyle-hook.misc-patterns', default=['*.options','*.cmake','*.txt', '*.xml'])

    code_patterns = source_patterns + header_patterns
    include_patterns = code_patterns + misc_patterns

    checkLGPL = common.get_option('codingstyle-hook.LGPL-check', default=True, type='--bool') == "true"
    sortIncludes = common.get_option('codingstyle-hook.sort-includes', default=False, type='--bool') == "true"
    showDiff = common.get_option('codingstyle-hook.show-diff', default=False, type='--bool') == "true"
    autoclean = common.get_option('codingstyle-hook.autoclean', default=True, type='--bool') == "true"
    global UNCRUSTIFY_PATH
    UNCRUSTIFY_PATH = common.get_option('codingstyle-hook.uncrustify-path', default=[UNCRUSTIFY_PATH], type='--path').strip()

    print checkLGPL
    if common.execute_command(UNCRUSTIFY_PATH + ' -v -q').status:
        common.error('Failed to launch uncrustify.\n')
        return True

    abort    = False
    reformat = False
    checked  = set()
    diff     = ''


    reformatedList = []
    global repoRoot
    repoRoot = common.execute_command('git rev-parse --show-toplevel').out.strip()

    #sortincludes.find_libraries_and_bundles(repoRoot)

    for f in files:
        if f in checked or not any(f.fnmatch(p) for p in include_patterns):
            continue

        content = f.contents
        if not common.binary(content):

            # Do this last because contents of the file will be modified by uncrustify
            # Thus the variable content will no longer reflect the real content of the file
            file = os.path.join(repoRoot, f.path)
            res, fileDiff = format_file(file, showDiff, code_patterns, header_patterns, misc_patterns, checkLGPL, sortIncludes)
            if res == 1:
                reformatedList.append(f.path)
                reformat = True
                diff += fileDiff
            elif res == 2:

                # Error in reformatting
                return True

        checked.add(f)

    if reformat:
        #if showDiff:
        #    ui.edit(diff, 'user')

        text = "\nSome files don't respect the coding style:\n"

        for f in reformatedList:
            text += FILEWARN(f)
        text += '\nThe commit will be aborted.\nDo you wish to apply modifications automatically (Yn)?\n' \
                '\n  - If yes, you will need to redo the commit (backups will be created).' \
                '\n  - If no, nothing will be changed but you will need to fix the files manually.\n$$ &yes $$ &no'
        answer = 1#ui.promptchoice(text, default=0)
        if answer == 1:
            # remove all *.new files and abort
            print
            common.error( 'Commit aborted, no format modification made has been made.' )
            print

            for f in reformatedList:
                file = os.path.join(repoRoot, f)
                os.remove( NEWFILE( file ) )
            return True

        common.error( 'Commit aborted, files have been reformatted. Commit again to apply modifications in the changeset.' )

        # apply modifications and make backups
        if autoclean:
            backupPath = os.path.join(repoRoot, '.hg', BACKUP_LIST_FILE)
            fBackupList = open(backupPath, 'a+')

        for f in reformatedList:
            file = os.path.join(repoRoot, f)
            shutil.copy2( file, OLDFILE( file ) )
            # Use copyfile because we wan't to preserve time attributes, otherwise hg will still consider the
            # files to be modified after the commit
            shutil.copy2( NEWFILE( file ), file )
            os.remove( NEWFILE( file ) )

            if autoclean:
                fBackupList.writelines(OLDFILE( file ) + '\n')

        if autoclean:
            fBackupList.close()

        return True

    checked  = set()

    for f in files:
        if f in checked:
            continue

        if any(f.fnmatch(p) for p in code_patterns):
            # We can't use content = csctx[f].data() because the content of the file may have been
            # modified by coding-style hook. This function returns the unmodified content
            path = os.path.join(repoRoot, f.path)
            file = open(path, 'r')
            content = file.read()
            file.close()

            if not common.binary(content):

                if checkLGPL:
                    abort = abort or check_license(content, path)

                if any(f.fnmatch(p) for p in header_patterns):
                    abort = check_header_guard(content, path) or abort

        checked.add(f)

    if abort:
        return True

    if autoclean:
        backupPath = os.path.join(repoRoot, '.hg', BACKUP_LIST_FILE)
        if os.path.exists(backupPath):
            backupList = open(backupPath, 'r').readlines()

            common.note('\n')
            for f in backupList:
                backupFile = f.path.split()
                if backupFile:
                    if os.path.exists( backupFile[0] ):
                        common.note('Delete backup file ' + f)
                        os.remove( backupFile[0] )
            os.remove( backupPath )

    return False

hooks = {
        'codingstyle':codingstyle,
        }
