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

import os
import re
from fnmatch import fnmatch

import common
import sortincludes
from common import FormatReturn

SEPARATOR = '%s\n' % ('-' * 79)
FILEWARN = lambda x: ('  - %s') % os.path.relpath(x, common.get_repo_root())
UNCRUSTIFY_PATH = 'uncrustify'
BACKUP_LIST_FILE = 'backupList'

LICENSE = '/\* \*\*\*\*\* BEGIN LICENSE BLOCK \*\*\*\*\*\n\
 \* FW4SPL - Copyright \(C\) IRCAD, (.*).\n\
 \* Distributed under the terms of the GNU Lesser General Public License \(LGPL\) as\n\
 \* published by the Free Software Foundation.\n\
 \* \*\*\*\*\*\* END LICENSE BLOCK \*\*\*\*\*\* \*/'


# ------------------------------------------------------------------------------

def codingstyle(files, enable_reformat, check_lgpl, check_commits_date):
    source_patterns = common.get_option('codingstyle-hook.source-patterns', default='*.cpp *.cxx *.c').split()
    header_patterns = common.get_option('codingstyle-hook.header-patterns', default='*.hpp *.hxx *.h').split()
    misc_patterns = common.get_option('codingstyle-hook.misc-patterns', default='*.cmake *.txt *.xml *.json').split()

    code_patterns = source_patterns + header_patterns
    include_patterns = code_patterns + misc_patterns

    sort_includes = common.get_option('codingstyle-hook.sort-includes', default="true", type='--bool') == "true"

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

    if common.execute_command(UNCRUSTIFY_PATH + ' -v -q').status != 0:
        common.error('Failed to launch uncrustify.\n')
        return []

    checked = set()

    reformatted_list = []
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
            file_path = os.path.join(repoRoot, f.path)
            if os.path.isfile(file_path):
                res = format_file(file_path, enable_reformat, code_patterns, header_patterns, misc_patterns, check_lgpl,
                                  sort_includes, f.status, check_commits_date)
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


# ------------------------------------------------------------------------------

# Reformat file according to minimal coding-style rules
# Return True if anything as been modified along with a unified diff
def format_file(source_file, enable_reformat, code_patterns, header_patterns, misc_patterns, check_lgpl, sort_includes,
                status, check_commits_date):
    # Invoke uncrustify for source code files
    if any(fnmatch(source_file, p) for p in code_patterns):

        common.trace('Launching uncrustify on : ' + source_file)
        config_file = os.path.join(os.path.dirname(__file__), 'uncrustify.cfg')

        ret = FormatReturn()

        # Fix license year
        if check_lgpl is True:
            ret.add(fix_license_year(source_file, enable_reformat, status, check_commits_date))

        # Sort headers
        if sort_includes is True:
            ret.add(sortincludes.sort_includes(source_file, enable_reformat))

        if any(fnmatch(source_file, p) for p in header_patterns):
            ret.add(fix_header_guard(source_file, enable_reformat))

        # Uncrustify
        command = UNCRUSTIFY_PATH + ' -c ' + config_file + ' -q %s ' + source_file

        if enable_reformat is True:
            # Check first
            uncrustify = common.execute_command(command % '--check')

            if uncrustify.status != 0:
                uncrustify = common.execute_command(command % '--replace --no-backup --if-changed')
                if uncrustify.status != 0:
                    common.error('Uncrustify failure on file: ' + source_file)
                    common.error(uncrustify.out)
                    return FormatReturn.Error
                ret.add(FormatReturn.Modified)
        else:
            uncrustify = common.execute_command(command % '--check')

            if uncrustify.status != 0:
                common.error('Uncrustify failure on file: ' + source_file)
                return FormatReturn.Error

        return ret.value

    # Replace only YEAR, TAB, CRLF and CR for miscellaneous files
    elif any(fnmatch(source_file, p) for p in misc_patterns):

        common.trace('Parsing: ' + source_file + ' to replace CR, CRLF and TABs')

        str_old_file = open(source_file, 'rb').read()

        str_new_file = re.sub('\t', '    ', str_old_file)
        tmp_str = re.sub('\r\n', '\n', str_new_file)
        str_new_file = re.sub('\r', '\n', tmp_str)

        if str_old_file == str_new_file:
            return FormatReturn.NotModified

        # Something has been changed, write the new file
        open(source_file, 'wb').write(str_new_file)
        return FormatReturn.Modified


# ------------------------------------------------------------------------------

# Check licence header
def fix_license_year(path, enable_reformat, status, check_commits_date):
    with open(path, 'r') as source_file:
        content = source_file.read()

    common.trace('Checking for LGPL license in: ' + path)

    YEAR = common.get_file_datetime(path, check_commits_date).year

    # Look for the license pattern
    licence_number = len(re.findall(LICENSE, content, re.MULTILINE))
    if licence_number > 1:

        common.error("There should be just one licence header per file in :" + FILEWARN(path) + ".")
        return FormatReturn.Error

    elif licence_number < 1:

        if enable_reformat:

            lic = LICENSE
            lic = lic.replace("(.*)", "%s-%s" % (YEAR, YEAR))
            lic = lic.replace("\\", "")

            with open(path, 'wb') as source_file:

                source_file.write(lic + "\n\n")
                source_file.write(content)

            common.note('LGPL license header fixed in : ' + FILEWARN(path) + '.')
            return FormatReturn.Modified

        else:

            common.error("There should be at least one licence header per file in :" + FILEWARN(path) + ".")
            return FormatReturn.Error

    # Here, it has only one occurrences that must be checked

    # Check license
    LICENSE_YEAR = r"(.*)FW4SPL - Copyright \(C\) IRCAD, ([0-9]+)."
    LICENSE_YEAR_RANGE = r"(.*)FW4SPL - Copyright \(C\) IRCAD, ([0-9]+)-([0-9]+)."

    # Check date
    if re.search(LICENSE_YEAR_RANGE, content):

        LICENSE_YEAR_REPLACE = r"\1FW4SPL - Copyright (C) IRCAD, \2-" + str(YEAR) + "."
        str_new_file = re.sub(LICENSE_YEAR_RANGE, LICENSE_YEAR_REPLACE, content)

    else:

        match = re.search(LICENSE_YEAR, content)

        if match:

            if status == 'A' or match.group(2) == str(YEAR):

                LICENSE_YEAR_REPLACE = r"\1FW4SPL - Copyright (C) IRCAD, " + str(YEAR) + "."
                str_new_file = re.sub(LICENSE_YEAR, LICENSE_YEAR_REPLACE, content)

            else:

                LICENSE_YEAR_REPLACE = r"\1FW4SPL - Copyright (C) IRCAD, \2-" + str(YEAR) + "."
                str_new_file = re.sub(LICENSE_YEAR, LICENSE_YEAR_REPLACE, content)
        else:

            common.error('Licence year format in : ' + FILEWARN(path) + ' is not correct.')
            return FormatReturn.Error

    if str_new_file != content:

        if enable_reformat:

            common.note('Licence year fixed in : ' + FILEWARN(path))
            with open(path, 'wb') as source_file:
                source_file.write(str_new_file)
            return FormatReturn.Modified

        else:

            common.error('Licence year in : ' + FILEWARN(path) + ' is not up-to-date.')
            return FormatReturn.Error

    return FormatReturn.NotModified


# ------------------------------------------------------------------------------

# Check the header guard consistency
def fix_header_guard(path, enable_reformat):
    ret = FormatReturn()

    with open(path, 'r') as source_file:
        content = source_file.read()

    # Regex for '#pragma once'
    single_comment = "(\/\/([^(\n|\r)]|\(|\))*)"
    multi_comment = "(\/\*([^\*\/]|\*[^\/]|\/)*\*\/)"
    useless_char = "\t| |\r"
    pragma_once = "#pragma(" + useless_char + ")+once"
    all_before_pragma = ".*" + pragma_once + "(" + useless_char + ")*\n"

    # Remove old style
    path_upper = path.upper()
    path_upper = path_upper.replace("\\", "/")
    substrings = path_upper.split('/');
    find = False;
    res = "__";
    for i in range(0, len(substrings)):
        if substrings[i] == "INCLUDE":
            find = True;
        elif substrings[i] == "TEST":
            res += substrings[i - 1].upper() + "_UT_";
        elif find:
            res += substrings[i].upper() + "_";
    expected_guard = res.split('.');
    if len(re.findall("HXX", expected_guard[1], re.DOTALL)) != 0 :
        expected_guard[0] += "_HXX__";
    else :
        expected_guard[0] += "_HPP__";

    expected_guard = expected_guard[0]

    # Remove all about expected guard
    while len(re.findall("#(ifndef|define|endif)((" + useless_char + ")|(/\*)|(\/\/))*" + expected_guard + "[^\n]*",
                         content, re.DOTALL)) != 0:

        match2 = re.search("#(ifndef|define|endif)((" + useless_char + ")|(/\*)|(\/\/))*" + expected_guard + "[^\n]*",
                           content, re.DOTALL)
        if enable_reformat:

            content = content.replace(match2.group(0), "")
            common.note("Old style of header guard fixed : " + match2.group(0) + "in file : " + FILEWARN(path) + ".")
            with open(path, 'wb') as source_file:
                source_file.write(content)
            ret.add(FormatReturn.Modified)

        else:

            common.error("Old style of header guard found : " + match2.group(0) + "in file : " + FILEWARN(path) + ".")
            ret.add(FormatReturn.Error)
            return ret.value

    # Number of occurrences of '#pragma once'
    pragma_number = len(re.findall(pragma_once, content, re.MULTILINE))
    if pragma_number > 1:

        common.error("There should be just one '#pragma once' per file in :" + FILEWARN(path) + ".")
        ret.add(FormatReturn.Error)
        return ret.value

    elif pragma_number < 1:

        # Add 'pragma once'
        if enable_reformat:

            match = re.search("(" + single_comment + "|" + multi_comment + "|" + useless_char + "|\n)*", content,
                              re.MULTILINE)

            with open(path, 'wb') as source_file:
                source_file.write(match.group(0))
                source_file.write("#pragma once\n\n")
                source_file.write(content.replace(match.group(0), ""))

            common.note("'#pragma once' fixed in :" + FILEWARN(path))

            ret.add(FormatReturn.Modified)
            return ret.value

        else:

            common.error("There should be at least one '#pragma once' per file in :" + FILEWARN(path) + ".")
            ret.add(FormatReturn.Error)
            return ret.value

    # Here, it has only one occurrences that must be checked

    # Get all string before first '#pragma once'
    out = re.search(all_before_pragma, content, re.DOTALL).group(0)

    # Remove '#pragma once'
    match2 = re.search(pragma_once, out, re.DOTALL)
    out = out.replace(match2.group(0), "")

    # Remove multi line comments
    while len(re.findall(multi_comment, out, re.DOTALL)) != 0:
        match2 = re.search(multi_comment, out, re.DOTALL)
        out = out.replace(match2.group(0), "")

    # Remove single line comments
    while len(re.findall(single_comment, out, re.DOTALL)) != 0:
        match2 = re.search(single_comment, out, re.DOTALL)
        out = out.replace(match2.group(0), "")

    # If it's not empty, they are an error
    if len(re.findall("[^\n]", out, re.DOTALL)) != 0:
        common.error(
            ("Unexpected : '%s' befor #pragma once in :" % re.search("^.+$", out, re.MULTILINE).group(0)) + FILEWARN(
                path) + ".")
        ret.add(FormatReturn.Error)
        return ret.value

    # Check space number between '#pragma' and 'once'
    if len(re.findall("#pragma once", content, re.DOTALL)) == 0:

        if enable_reformat:
            # Get all string before first '#pragma once'
            out = re.search(all_before_pragma, content, re.DOTALL).group(0)

            # Remove '#pragma once'
            match2 = re.search(pragma_once, out, re.DOTALL)
            out2 = out.replace(match2.group(0), "")

            with open(path, 'wb') as source_file:

                source_file.write(out2)
                source_file.write("#pragma once\n")
                source_file.write(content.replace(out, ""))

            ret.add(FormatReturn.Modified)
            return ret.value

        else:

            common.error("Needed : '#pragma once', actual : '" + re.search(pragma_once, content, re.DOTALL).group(
                0) + "' in file :" + FILEWARN(path) + ".")
            ret.add(FormatReturn.Error)
            return ret.value

    ret.add(FormatReturn.NotModified)
    return ret.value
