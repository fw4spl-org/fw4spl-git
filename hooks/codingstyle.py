#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Make sure you respect the minimal coding rules and gently reformat files for you.

.gitconfig configuration :

[fw4spl-hooks]
    hooks = codingstyle

[codingstyle-hook]
    source-patterns = *.cpp *.cxx *.c
    header-patterns = *.hpp *.hxx *.h
    misc-patterns = *.cmake *.txt *.xml *.json
    uncrustify-path=C:\Program files\uncrustify\uncrustify.exe
    additional-projects = "D:/Dev/src/fw4spl-ar;D:/Dev/src/fw4spl-ext"

Available options are :
source-patterns : file patterns to process as source code files - default to *.cpp *.cxx *.c
header-patterns : file patterns to process as header files - default to *.hpp *.hxx *.h
misc-patterns : file patterns to process as non-source code files (build, configuration, etc...)
                Reformatting is limited to TABs and EOL - default to *.options *.cmake *.txt *.xml
uncrustify-path : path to the uncrustify program - default to uncrustify
additional-projects : additional fw4spl repositories paths used to sort includes (separated with a ;).
                      default parent folder of the current repository.

"""

import datetime
import os
import re
import string
from fnmatch import fnmatch

import common
import sortincludes
from common import FormatReturn

YEAR = datetime.date.today().year
SEPARATOR = '%s\n' % ('-' * 79)
FILEWARN = lambda x: ('  - %s') % os.path.relpath(x, repoRoot)
UNCRUSTIFY_PATH = 'uncrustify'
BACKUP_LIST_FILE = 'backupList'

LICENSE = '/\* \*\*\*\*\* BEGIN LICENSE BLOCK \*\*\*\*\*\n\
 \* FW4SPL - Copyright \(C\) IRCAD, (.*).\n\
 \* Distributed under the terms of the GNU Lesser General Public License \(LGPL\) as\n\
 \* published by the Free Software Foundation.\n\
 \* \*\*\*\*\*\* END LICENSE BLOCK \*\*\*\*\*\* \*/'


# ------------------------------------------------------------------------------

def fix_license_year(file, enable_reformat, status):
    str_old_file = open(file, 'rb').read()

    common.trace('Checking for LGPL license in: ' + file)

    # Look for the license pattern
    match = re.search(LICENSE, str_old_file, re.MULTILINE)
    if match is None:
        common.error('LGPL license header missing in : ' + file + '.')
        return FormatReturn.Error

    LICENSE_YEAR = r"(.*)FW4SPL - Copyright \(C\) IRCAD, ([0-9]+)."
    LICENSE_YEAR_RANGE = r"(.*)FW4SPL - Copyright \(C\) IRCAD, ([0-9]+)-([0-9]+)."

    if re.search(LICENSE_YEAR_RANGE, str_old_file):
        LICENSE_YEAR_REPLACE = r"\1FW4SPL - Copyright (C) IRCAD, \2-" + str(YEAR) + "."
        str_new_file = re.sub(LICENSE_YEAR_RANGE, LICENSE_YEAR_REPLACE, str_old_file)
    else:
        match = re.search(LICENSE_YEAR, str_old_file)
        if match:
            if status == 'A' or match.group(2) == str(YEAR):
                LICENSE_YEAR_REPLACE = r"\1FW4SPL - Copyright (C) IRCAD, " + str(YEAR) + "."
                str_new_file = re.sub(LICENSE_YEAR, LICENSE_YEAR_REPLACE, str_old_file)
            else:
                LICENSE_YEAR_REPLACE = r"\1FW4SPL - Copyright (C) IRCAD, \2-" + str(YEAR) + "."
                str_new_file = re.sub(LICENSE_YEAR, LICENSE_YEAR_REPLACE, str_old_file)
        else:
            common.error('Licence year format in : ' + file + ' is not correct.')
            return FormatReturn.Error

    if str_new_file != str_old_file:
        if enable_reformat:
            common.note('Licence year fixed in : ' + file)
            open(file, 'wb').write(str_new_file)
            return FormatReturn.Modified
        else:
            common.error('Licence year in : ' + file + ' is not up-to-date.')
            return FormatReturn.Error

    return FormatReturn.NotModified


# ------------------------------------------------------------------------------

# Reformat file according to minimal coding-style rules
# Return True if anything as been modified along with a unified diff
def format_file(file, enable_reformat, code_patterns, header_patterns, misc_patterns, check_lgpl, sort_includes,
                status):
    # Invoke uncrustify for source code files
    if any(fnmatch(file, p) for p in code_patterns):

        common.trace('Launching uncrustify on : ' + file)
        configFileName = os.path.join(os.path.dirname(__file__), 'uncrustify.cfg')

        ret = FormatReturn()

        command = UNCRUSTIFY_PATH + ' -c ' + configFileName + ' -q %s ' + file

        if enable_reformat is True:
            # Check first
            uncrustify = common.execute_command(command % '--check')

            if uncrustify.status:
                uncrustify = common.execute_command(command % '--replace --no-backup')
                if uncrustify.status:
                    common.error('Uncrustify failure on file: ' + file)
                    return FormatReturn.Error
                ret.add(FormatReturn.Modified)
        else:
            uncrustify = common.execute_command(command % '--check')

            if uncrustify.status:
                common.error('Uncrustify failure on file: ' + file)
                return FormatReturn.Error

        # Fix license year
        if check_lgpl is True:
            ret.add(fix_license_year(file, enable_reformat, status))

        # Sort headers
        if sort_includes is True:
            ret.add(sortincludes.sort_includes(file, enable_reformat))

        if any(fnmatch(file, p) for p in header_patterns):
            ret.add(fix_header_guard(file, enable_reformat))

        return ret.value

    # Replace only YEAR, TAB, CRLF and CR for miscellaneous files
    elif any(fnmatch(file, p) for p in misc_patterns):

        common.trace('Parsing: ' + file + ' to replace CR, CRLF and TABs')

        str_old_file = open(file, 'rb').read()

        str_new_file = re.sub('\t', '    ', str_old_file)
        tmp_str = re.sub('\r\n', '\n', str_new_file)
        str_new_file = re.sub('\r', '\n', tmp_str)

        if str_old_file == str_new_file:
            return FormatReturn.NotModified

        # Something has been changed, write the new file
        open(file, 'wb').write(str_new_file)
        return FormatReturn.Modified


# ------------------------------------------------------------------------------

# Check the header guard consistency
def fix_header_guard(path, enableReformat):
    ret = FormatReturn()

    file = open(path, 'r')
    content = file.read()
    file.close()

    # Assume the first ifndef is the first header guard
    match = re.search('#ifndef +(_*(?:[0-9A-Z]+_*)*)$', content, re.MULTILINE)
    if match is None:
        common.error("Can't find header guard, maybe check the naming convention ?")
        common.error(FILEWARN(path))
        return FormatReturn.Error

    guard = match.group(1)

    # Now check that the guard name follows the file name
    file_upper = path.upper()

    match = re.search('(?:(?:INCLUDE\/)|(?:SRC\/)).*', file_upper)
    if match is None:
        common.error("warning: can't find 'src' or 'include' in the file path.")
        common.error("         Header guard naming check skipped.")
        common.error(FILEWARN(path))

    else:

        # look if this is a unit test
        test_match = re.search('([^\/]*)(?:\/TEST\/TU\/INCLUDE)(.*)', file_upper)

        if test_match:
            expected_guard = '__' + test_match.group(1) + '_' + 'UT' + re.sub('/|\.', '_', test_match.group(2)) + '__'
        else:

            # find the last interesting part of the path (we can have SRC or INCLUDE multiple times)
            split_by_src = string.split(file_upper, 'SRC/')[-1]
            split_by_inc = string.split(file_upper, 'INCLUDE/')[-1]
            if len(split_by_src) < len(split_by_inc):
                file_upper = split_by_src
            else:
                file_upper = split_by_inc
            expected_guard = '__' + re.sub('/|\.', '_', file_upper) + '__'

        if guard != expected_guard:
            common.note(FILEWARN(path))

            str_new_file = re.sub(r"([^_])" + guard, r"\1" + expected_guard, content)

            if str_new_file != content:
                if enableReformat:
                    open(path, 'wb').write(str_new_file)
                    content = str_new_file
                    common.note("The header guard does not follow our naming convention.")
                    common.note("    Replacing " + guard + " by " + expected_guard + " .")
                    ret.add(FormatReturn.Modified)
                else:
                    common.error("The header guard does not follow our naming convention.")
                    return FormatReturn.Error

        match = re.search('#define +' + expected_guard, content, re.MULTILINE)
        if match is None:
            common.error("Can't find #define header guard matching : " + expected_guard)
            common.error(FILEWARN(path))
            return FormatReturn.Error

        match = re.search('#endif */[/\*] *' + expected_guard + '(?:.*\*/)?', content, re.MULTILINE)
        if match is None:
            common.error("Can't find #endif with a comment matching the header guard  : " + expected_guard + "\n")
            common.error(FILEWARN(path))
            return FormatReturn.Error

    return ret.value


# ------------------------------------------------------------------------------

def codingstyle(files, enable_reformat, check_lgpl, deep_scan=True):
    source_patterns = common.get_option('codingstyle-hook.source-patterns', default='*.cpp *.cxx *.c').split()
    header_patterns = common.get_option('codingstyle-hook.header-patterns', default='*.hpp *.hxx *.h').split()
    misc_patterns = common.get_option('codingstyle-hook.misc-patterns', default='*.cmake *.txt *.xml *.json').split()

    code_patterns = source_patterns + header_patterns
    include_patterns = code_patterns + misc_patterns

    sortIncludes = common.get_option('codingstyle-hook.sort-includes', default="true", type='--bool') == "true"
    global repoRoot
    repoRoot = common.get_repo_root()

    if repoRoot is None:
        common.warn("Cannot find 'fw4spl' repository structure")
        parent_repo = ""
    else:
        parent_repo = os.path.abspath(os.path.join(repoRoot, os.pardir))

    fw4spl_configured_projects = common.get_option('codingstyle-hook.additional-projects', default=None)
    fw4spl_projects = []

    if fw4spl_configured_projects is None:
        # no additional-projects specified in config file. Default is parent repository folder
        fw4spl_projects.append(parent_repo)
    else:
        fw4spl_projects = fw4spl_configured_projects.split(";")
        # adds current repository folder to the additional-projects specified in config file.
        fw4spl_projects.append(repoRoot)
        # normalize pathname
        fw4spl_projects = map(os.path.normpath, fw4spl_projects)
        # remove duplicates
        fw4spl_projects = list(set(fw4spl_projects))

    global UNCRUSTIFY_PATH

    if common.g_uncrustify_path_arg is not None and len(common.g_uncrustify_path_arg) > 0:
        UNCRUSTIFY_PATH = common.g_uncrustify_path_arg
    else:
        UNCRUSTIFY_PATH = common.get_option('codingstyle-hook.uncrustify-path', default=UNCRUSTIFY_PATH,
                                            type='--path').strip()

    common.note('Using uncrustify: ' + UNCRUSTIFY_PATH)

    if common.execute_command(UNCRUSTIFY_PATH + ' -v -q').status:
        common.error('Failed to launch uncrustify.\n')
        return []

    checked = set()

    reformatedList = []
    sortincludes.find_libraries_and_bundles(fw4spl_projects)

    ret = False
    count = 0
    reformat_count = 0
    for f in files:
        if f in checked or not any(f.fnmatch(p) for p in include_patterns):
            continue

        content = f.contents
        if not common.binary(content):

            # Do this last because contents of the file will be modified by uncrustify
            # Thus the variable content will no longer reflect the real content of the file
            file = os.path.join(repository_root, f.path)
            res = format_file(file, enable_reformat, code_patterns, header_patterns, misc_patterns, check_lgpl,
                              sort_includes, f.status)
            count += 1
            if res == FormatReturn.Modified:
                reformatted_list.append(f.path)
                reformat_count += 1
            elif res == FormatReturn.Error:
                # Error in reformatting
                ret = True

        checked.add(f)

    common.note('%d file(s) checked, %d file(s) reformatted.' % (count, reformat_count))

    return ret, reformatted_list
