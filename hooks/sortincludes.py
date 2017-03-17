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
    if match == None:
        raise Exception('lib path not found')

    # Here we split so we have for instance
    # /home/fbridault/dev/f4s-sandbox/src/f4s/SrcLib/core/fwDataCamp/include/fwMedDataCamp/DicomSeries.hpp
    # split into
    # ['/home/fbridault/dev/f4s-sandbox/src/f4s/SrcLib/core/fwDataCamp/', 'include/fwMedDataCamp/DicomSeries.hpp']
    splitByInc = string.split(path, 'include/')

    # If something has been split, that means we have an include
    if len(splitByInc) > 1:
        libPath = splitByInc
    else:
        libPath = string.split(path, 'src/')

    # Now we take the second last element (we start from the end because 'include' or 'src' may appear multiple times)
    lib = libPath[-2]

    libName = string.split(lib, '/')[-2]
    if (libName == "tu"):
        # If we have a unit test, for instance '/home/fbridault/dev/f4s-sandbox/src/f4s/SrcLib/io/fwCsvIO/test/tu/CsvReaderTest.hpp'
        # We will get 'tu' instead of the library name and thus we have to skip '/test/tu'
        libName = string.split(lib, '/')[-4]

    # We have kept '/home/fbridault/dev/f4s-sandbox/src/f4s/SrcLib/core/fwDataCamp/'
    # We take the second last element split by '/', so in this case 'fwDataCamp'
    return libName


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
                            g_bundles += [rootdir]
                        elif re.match('.*SrcLib', root):
                            g_libs += [rootdir]

    g_libs.sort()
    g_bundles.sort()




def clean_list(includeList):
    newIncludeList = []

    if len(includeList) == 0:
        return newIncludeList

    includeList.sort(key=lambda s: s[1].lower())

    prevModule = includeList[0][0]
    for module, include in includeList:
        if prevModule != module:
            newIncludeList += ['\n']
        newIncludeList += [include]
        prevModule = module

    newIncludeList += ['\n']
    return newIncludeList


def sort_includes(path, enableReformat):
    try:
        cur_lib = find_current_library(path)
    except:
        common.warn('Failed to find current library for file ' + path + ', includes order might be wrong.\n')
        cur_lib = '!!NOTFOUND!!'

    pathname = os.path.dirname(__file__) + "/"

    file = open(pathname + "std_headers.txt", 'r')

    libStd = file.read()
    file.close()

    file = open(path, 'rb')
    content = file.readlines()
    file.close()

    includes = set()
    firstLine = -1
    lastLine = -1

    outOfInclude = False

    for i, line in enumerate(content):
        if (re.match("#include", line)):
            if outOfInclude:
                common.warn(
                    'Failed to parse includes in file ' + path + ', includes sort is skipped. Maybe there is a #ifdef ? This may be handled in a future version.\n')
                return

            if firstLine == -1:
                firstLine = i
            lastLine = i

            includes.add(line)
        elif firstLine > -1 and line != "\n":
            outOfInclude = True

    if firstLine == -1 and lastLine == -1:
        # No include, skip
        return

    includeModules = []

    # Create associated list of modules
    for include in includes:
        includePathMatch = re.match('.*<(.*/.*)>', include)
        module = ""
        if includePathMatch:
            module = includePathMatch.group(1).split('/')[0]
        else:
            includePathMatch = re.match('.*"(.*/.*)"', include)
            if includePathMatch:
                module = includePathMatch.group(1).split('/')[0]
            else:
                module = ""

        includeModules += [module]

    ownHeaderInclude = []
    currentModuleIncludes = []
    libIncludes = []
    bundlesIncludes = []
    otherIncludes = []
    stdIncludes = []

    origPath = re.sub(".hg-new", "", path)
    extension = os.path.splitext(origPath)[1]

    cpp = False
    if extension == ".cpp":
        filename = os.path.basename(origPath)
        matchedHeader = re.sub(extension, ".hpp", filename)
        cpp = True

    for include, module in zip(includes, includeModules):

        if cpp and re.search('".*' + matchedHeader + '.*"', include):
            ownHeaderInclude += [(module, include)]
        elif module == cur_lib or re.search('".*"', include):
            currentModuleIncludes += [(module, include)]
        elif module in g_libs:
            libIncludes += [(module, include)]
        elif module in g_bundles:
            bundlesIncludes += [(module, include)]
        else:
            includePathMatch = re.match('.*<(.*)>', include)
            if includePathMatch and includePathMatch.group(1) in libStd:
                stdIncludes += [(module, include)]
            else:
                otherIncludes += [(module, include)]

    newIncludes = clean_list(ownHeaderInclude) + clean_list(currentModuleIncludes) + clean_list(
        libIncludes) + clean_list(bundlesIncludes) + clean_list(otherIncludes) + clean_list(stdIncludes)

    newContent = []
    for i, line in enumerate(content):
        if i == firstLine:
            newContent += newIncludes[:-1]
        elif i < firstLine or i > lastLine:
            newContent += [line]

    if content != newContent:
        if enableReformat:
            open(path, 'wb').writelines(newContent)
            return FormatReturn.Modified
        else:
            common.error('Include headers are not correctly sorted in file : ' + path + '.')
            return FormatReturn.Error

    return FormatReturn.NotModified
