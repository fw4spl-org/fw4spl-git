#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import collections
import os, re
import subprocess
import fnmatch

class FileAtIndex(object):

    def __init__(self, contents, size, mode, sha1, status, path):
        self.contents = contents
        self.size = size
        self.mode = mode
        self.sha1 = sha1
        self.status = status
        self.path = path

    def fnmatch(self, pattern):
        basename = os.path.basename(self.path)
        return fnmatch.fnmatch(basename, pattern)

def note(msg):
    print('*** [Pre-commit hook] ' + msg + ' ***')

def error(msg):
    print('*** [Pre-commit hook: ERROR] ' + msg + ' ***')

def binary(s):
    """return true if a string is binary data"""
    return bool(s and '\0' in s)

ExecutionResult = collections.namedtuple(
    'ExecutionResult',
    'status, out',
)

def execute_command(proc):

    try:
        out = subprocess.check_output(proc.split())
    except subprocess.CalledProcessError:
        return ExecutionResult(1, "")
    return ExecutionResult(0, out)

def _current_commitish():
    if execute_command('git rev-parse --verify HEAD').status:
        return '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
    else:
        return 'HEAD'

def get_option(option, default="", type=""):

    try:
        out = subprocess.check_output(('git config ' + type + option).split())
        return out
    except subprocess.CalledProcessError:
        if default:
            return default
        else:
            error("Option '" + option + "' not found and no default value was provided.")
            error("Commit aborted !!!")
            exit(1)

def _contents(sha):
    return execute_command('git show ' + sha).out

def _diff_index():
    return execute_command('git diff-index --cached -z --diff-filter=AM ' + _current_commitish()).out

def _size(sha):
    cmd_out = execute_command('git cat-file -s ' + sha).out
    return int(cmd_out)

def files_staged_for_commit():
    # see: git help diff-index
    # "RAW OUTPUT FORMAT" section
    diff_index_row_regex = re.compile(
        r'''
        :
        (?P<old_mode>[^ ]+)
        [ ]
        (?P<new_mode>[^ ]+)
        [ ]
        (?P<old_sha1>[^ ]+)
        [ ]
        (?P<new_sha1>[^ ]+)
        [ ]
        (?P<status>[^\0]+)
        \0
        (?P<path>[^\0]+)
        \0
        ''',
        re.X
    )
    for match in diff_index_row_regex.finditer(_diff_index()):
        mode, sha, status, path = match.group(
            'new_mode', 'new_sha1', 'status', 'path'
        )
        yield FileAtIndex(
            _contents(sha),
            _size(sha),
            mode,
            sha,
            status,
            path
        )
