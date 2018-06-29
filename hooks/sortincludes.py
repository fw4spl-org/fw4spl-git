#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import re
import string

import common
from common import FormatReturn

g_libs = []
g_bundles = []


def find_current_library(path):
    # Just assert first for 'src' or 'include'
    match = re.search('(?:(?:include\/)|(?:src\/)).*', path)
    if match is None:
        raise Exception('lib path not found')

    # Here we split so we have for instance
    # /home/fbridault/dev/f4s-sandbox/src/f4s/SrcLib/core/fwDataCamp/include/fwMedDataCamp/DicomSeries.hpp
    # split into
    # ['/home/fbridault/dev/f4s-sandbox/src/f4s/SrcLib/core/fwDataCamp/', 'include/fwMedDataCamp/DicomSeries.hpp']
    split_by_inc = string.split(path, 'include/')

    # If something has been split, that means we have an include
    if len(split_by_inc) > 1:
        lib_path = split_by_inc
    else:
        lib_path = string.split(path, 'src/')

    # Now we take the second last element (we start from the end because 'include' or 'src' may appear multiple times)
    lib = lib_path[-2]

    lib_name = string.split(lib, '/')[-2]
    if lib_name == "tu":
        # If we have a unit test, for instance '/home/fbridault/dev/f4s-sandbox/src/f4s/SrcLib/io/fwCsvIO/test/tu/CsvReaderTest.hpp'
        # We will get 'tu' instead of the library name and thus we have to skip '/test/tu'
        lib_name = string.split(lib, '/')[-4]

    # We have kept '/home/fbridault/dev/f4s-sandbox/src/f4s/SrcLib/core/fwDataCamp/'
    # We take the second last element split by '/', so in this case 'fwDataCamp'
    return lib_name


def find_libraries_and_bundles(fw4spl_projects):
    global g_libs
    global g_bundles

    g_libs = []
    g_bundles = []

    for project_dir in fw4spl_projects:
        if not os.path.isdir(project_dir):
            common.warn("%s isn't a valid directory." % project_dir)
            continue
        for root, dirs, files in os.walk(project_dir):
            rootdir = os.path.split(root)[1]
            # Do not inspect hidden folders
            if not rootdir.startswith("."):
                for file in files:
                    if file == "CMakeLists.txt":
                        if re.match('.*Bundles', root):
                            g_bundles += [rootdir.encode()]
                        elif re.match('.*SrcLib', root):
                            g_libs += [rootdir.encode()]

    g_libs.sort()
    g_bundles.sort()


def clean_list(includes):
    new_include_list = []

    if len(includes) == 0:
        return new_include_list

    includes.sort(key=lambda s: s[1].lower())

    prev_module = includes[0][0]
    for module, include in includes:
        if prev_module != module:
            new_include_list += [b'\n']
        new_include_list += [include]
        prev_module = module

    new_include_list += [b'\n']
    return new_include_list


def sort_includes(path, enable_reformat):
    try:
        cur_lib = find_current_library(path)
    except:
        common.warn('Failed to find current library for file ' + path + ', includes order might be wrong.\n')
        cur_lib = '!!NOTFOUND!!'

    pathname = os.path.dirname(__file__) + "/"

    file = open(pathname + "std_headers.txt", 'rb')
    lib_std = file.read()
    file.close()

    file = open(path, 'rb')
    content = file.readlines()
    file.close()

    includes = set()
    first_line = -1
    last_line = -1

    out_of_include = False

    for i, line in enumerate(content):
        if re.match(b"#include", line):
            if out_of_include:
                common.warn(
                    'Failed to parse includes in file ' + path + ', includes sort is skipped. Maybe there is a #ifdef ? This may be handled in a future version.\n')
                return FormatReturn.NotModified

            if first_line == -1:
                first_line = i
            last_line = i

            includes.add(line)
        elif first_line > -1 and line != b"\n":
            out_of_include = True

    if first_line == -1 and last_line == -1:
        # No include, skip
        return FormatReturn.NotModified

    include_modules = []

    # Create associated list of modules
    for include in includes:
        include_path_match = re.match(b'.*<(.*/.*)>', include)
        module = ""
        if include_path_match:
            module = include_path_match.group(1).split(b'/')[0]
        else:
            include_path_match = re.match(b'.*"(.*/.*)"', include)
            if include_path_match:
                module = include_path_match.group(1).split(b'/')[0]
            else:
                module = b""

        include_modules += [module]

    own_header_include = []
    current_module_includes = []
    lib_includes = []
    bundles_includes = []
    other_includes = []
    std_includes = []

    orig_path = re.sub(".hg-new", "", path)
    extension = os.path.splitext(orig_path)[1]

    cpp = False
    if extension == ".cpp":
        filename = os.path.basename(orig_path)
        matched_header = re.sub(extension, ".hpp", filename)
        cpp = True

    for include, module in zip(includes, include_modules):

        if cpp and re.search(b'".*' + matched_header.encode() + b'.*"', include):
            own_header_include += [(module, include)]
        elif module == cur_lib or re.search(b'".*"', include):
            current_module_includes += [(module, include)]
        elif module in g_libs:
            lib_includes += [(module, include)]
        elif module in g_bundles:
            bundles_includes += [(module, include)]
        else:
            include_path_match = re.match(b'.*<(.*)>', include)
            if include_path_match and include_path_match.group(1) in lib_std:
                std_includes += [(module, include)]
            else:
                other_includes += [(module, include)]

    new_includes = clean_list(own_header_include) + clean_list(current_module_includes) + clean_list(
        lib_includes) + clean_list(bundles_includes) + clean_list(other_includes) + clean_list(std_includes)

    new_content = []
    for i, line in enumerate(content):
        if i == first_line:
            new_content += new_includes[:-1]
        elif i < first_line or i > last_line:
            new_content += [line]

    if content != new_content:
        if enable_reformat:
            open(path, 'wb').writelines(new_content)
            return FormatReturn.Modified
        else:
            common.error('Include headers are not correctly sorted in file : ' + path + '.')
            return FormatReturn.Error

    return FormatReturn.NotModified
