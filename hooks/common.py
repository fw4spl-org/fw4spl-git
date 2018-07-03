#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import collections
# From command line arguments
import datetime
import fnmatch
import os
import re
import subprocess

g_trace = False
g_cppcheck_path_arg = None
g_uncrustify_path_arg = None


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
    print(('* [Sheldon] ' + msg))


def trace(msg):
    if g_trace:
        print(('* [Sheldon] ' + msg))


def error(msg):
    print(('*** [ERROR] ' + msg + ' ***'))


def warn(msg):
    print(('* [Warning] ' + msg + ' *'))


def binary(s):
    """return true if a string is binary data"""
    return b'\0' in s


ExecutionResult = collections.namedtuple(
    'ExecutionResult',
    'status, out',
)


def get_repo_root():
    result = execute_command('git rev-parse --show-toplevel')

    if result.status == 0:
        return result.out.strip().decode()

    warn(result.out.decode())
    return ""


def is_LGPL_repo():
    repo_root = get_repo_root()
    try:
        f = open(os.path.join(repo_root, "LICENSE/COPYING.LESSER"))
        f.close()
        return True
    except:
        return False


def _get_git_commit_datetime(path):
    # Get the git modification date of the file
    result = execute_command('git log -1 --format=%ad --date=format:%Y-%m-%dT%H:%M:%S ' + path)

    if result.status != 0:
        warn(result.out.decode())
        return None

    try:
        # Parse the string back to a datetime object
        return datetime.datetime.strptime(result.out.decode().strip(), '%Y-%m-%dT%H:%M:%S')
    except Exception as e:
        warn(e.message)
        return None


def get_file_datetime(path, check_commits_date):
    try:
        creation_time = datetime.datetime.fromtimestamp(os.path.getctime(path))
        modification_time = datetime.datetime.fromtimestamp(os.path.getmtime(path))
    except Exception as e:
        warn(e.message)

        creation_time = None
        modification_time = None

    if check_commits_date:
        git_datetime = _get_git_commit_datetime(path)

        # Use git modification time if it is valid and creation_time == modification_time
        if git_datetime is not None:
            return git_datetime

    # Use the modification time, if any
    if modification_time is not None:
        return modification_time

    # Otherwise use the system time
    return datetime.datetime.today()


def execute_command(proc):
    try:
        out = subprocess.check_output(proc.split(), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        return ExecutionResult(1, e.output)
    except OSError as e:
        return ExecutionResult(1, e.message)

    return ExecutionResult(0, out)


def current_commit():
    if execute_command('git rev-parse --verify HEAD').status != 0:
        return '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
    else:
        return 'HEAD'


def get_option(option, default, type=""):
    try:
        out = subprocess.check_output(('git config ' + type + ' ' + option).split()).strip()
        return out.decode()
    except subprocess.CalledProcessError:
        return default


def _contents(sha):
    result = execute_command('git show ' + sha)

    if result.status == 0:
        return result.out.decode()

    warn(result.out.decode())
    return ""


def _diff_index(rev):
    result = execute_command('git diff-index --cached -z --diff-filter=AM ' + rev)

    if result.status == 0:
        return result.out.decode()

    warn(result.out.decode())
    return ""


def _diff(rev, rev2):
    result = execute_command('git diff --raw -z --diff-filter=AM ' + rev + ' ' + rev2)

    if result.status == 0:
        return result.out.decode()

    warn(result.out.decode())
    return ""


def _size(sha):
    result = execute_command('git cat-file -s ' + sha)
    if result.status == 0:
        try:
            return int(result.out)
        except ValueError:
            return 0

    warn(result.out.decode())
    return 0


def files_in_rev(rev, rev2=''):
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

        if status is None or status == 'D':
            continue

        # Try to guest if the file has been deleted in a later commit
        file_status = status_of_file(get_repo_root() + '/' + path)

        if file_status is None or file_status == 'D':
            continue

        content = _contents(sha)

        if content is None or len(content) <= 0:
            continue

        size = _size(sha)

        if size is None or size <= 0:
            continue

        yield FileAtIndex(
            content,
            size,
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
    diff_idx = _diff_index(rev)
    for match in diff_index_row_regex.finditer(diff_idx):
        mode, sha, status, path = match.group(
            'new_mode', 'new_sha1', 'status', 'path'
        )

        # Try to guest if the file has been deleted in a later commit
        file_status = status_of_file(get_repo_root() + '/' + path)

        if status is not None and status != 'D' and file_status is not None and file_status != 'D':
            yield FileAtIndex(
                _contents(sha),
                _size(sha),
                mode,
                sha,
                status,
                path
            )


def status_of_file(path):
    # By default status is set to 'A' like it is a new file.
    # if the git status is '??' or empty, we guess also that the file is a new file.
    status = 'A'
    gitstatus = execute_command('git status --porcelain ' + path)

    if gitstatus.status != 0:
        warn("File : " + path + " is not in a git repository, sheldon will consider it like a new file")
    else:
        out = gitstatus.out.split()

        # if out is not empty and not equal to '??' so we have modified a tracked file.
        if out and out[0] != '??':
            status = out[0]

    return status


def file_on_disk(path):
    status = status_of_file(path)

    if status is not None and status != 'D':
        with open(path, 'rb') as content_file:
            content = content_file.read()

        stat = os.stat(path)
        size = stat.st_size

        yield FileAtIndex(
            content,
            size,
            '',
            '',
            status,
            path
        )


def directory_on_disk(path):
    for root, dirs, files in os.walk(path):
        for name in files:
            file_path = os.path.join(root, name)
            yield next(file_on_disk(file_path))
