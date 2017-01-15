#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import collections
import os, re
import subprocess
import fnmatch

g_trace = False

class FormatReturn:
    NotModified = 0
    Modified = 1
    Error = 2
    def __init__(self):
        self.value = 0

    def add(self, value):
        self.value = max(self.value, value)

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
    print('* [Sheldon] ' + msg )
    
def trace(msg):
    if g_trace:
        print('* [Sheldon] ' + msg )

def error(msg):
    print('*** [ERROR] ' + msg + ' ***')
    
def warn(msg):
    print('* [Warning] ' + msg + ' *')

def binary(s):
    """return true if a string is binary data"""
    return bool(s and '\0' in s)

ExecutionResult = collections.namedtuple(
    'ExecutionResult',
    'status, out',
)

def get_repo_root():
    return execute_command('git rev-parse --show-toplevel').out.strip()

def is_LGPL_repo():

    repoRoot = get_repo_root()
    try:
        f = open(os.path.join(repoRoot, "LICENSE/COPYING.LESSER"))
        f.close()
        return True
    except:
        return False

def execute_command(proc):

    try:
        out = subprocess.check_output(proc.split(), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        return ExecutionResult(1, "")
    except OSError:
        return ExecutionResult(1, "")
    return ExecutionResult(0, out)

def current_commit():
    if execute_command('git rev-parse --verify HEAD').status:
        return '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
    else:
        return 'HEAD'

def get_option(option, default, type=""):

    try:
        out = subprocess.check_output(('git config ' + type + ' ' + option).split()).strip()
        return out
    except subprocess.CalledProcessError:
        return default

def _contents(sha):
    return execute_command('git show ' + sha).out

def _diff_index(rev):
    return execute_command('git diff-index --cached -z --diff-filter=AM ' + rev).out

def _diff(rev, rev2):
    return execute_command('git diff --raw -z --diff-filter=AM ' + rev + ' ' + rev2).out

def _size(sha):
    cmd_out = execute_command('git cat-file -s ' + sha).out
    return int(cmd_out)

def files_in_rev(rev, rev2 = ''):
    # see: git help diff-index
    # "RAW OUTPUT FORMAT" section
    diff_row_regex = re.compile(
        r'''
        :
        (?P<old_mode>[^ ]+)
        [ ]
        (?P<new_mode>[^ ]+)
        [ ]
        (?P<old_sha1>[^ ]+)...
        [ ]
        (?P<new_sha1>[^ ]+)...
        [ ]
        (?P<status>[^\0]+)
        \0
        (?P<path>[^\0]+)
        \0
        ''',
        re.X
    )
    for match in diff_row_regex.finditer(_diff(rev, rev2)):
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

def files_staged_for_commit(rev):
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
    for match in diff_index_row_regex.finditer(_diff_index(rev)):
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
