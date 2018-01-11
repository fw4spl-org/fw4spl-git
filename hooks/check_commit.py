#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import re

import common


class _Const(object):
    @apply
    def TYPES():
        def fset(self, value):
            raise TypeError

        def fget(self):
            return ['feat', 'fix', 'perf', 'revert', 'docs', 'chore', 'style', 'refactor', 'test', 'merge']

        return property(**locals())


CONST = _Const()


# return all unpushed commit message
def unpushed_commit_message():
    command_result = common.execute_command('git log --branches --not --remotes --pretty=format:%h:%aE:%s')

    if command_result.status != 0:
        return []
    else:
        return command_result.out.split('\n')


def commit_in_path(old_path=None, new_path=None):
    git_command = 'git log --first-parent --pretty=format:%h:%aE:%s'

    if old_path is not None and len(old_path) > 0:
        git_command += ' ' + old_path

        if new_path is not None and len(new_path) > 0:
            git_command += '..' + new_path

    command_result = common.execute_command(git_command)

    if command_result.status != 0:
        return []
    else:
        return command_result.out.split('\n')


# check the title conformance against commitizen/angularjs/... rules
def __check_commit_title(commit_hash, commit_title):
    # Test the title against regex
    title_pattern = re.compile(r'(?P<type>' + '|'.join(CONST.TYPES) + ')\((?P<scope>\w+)\):(?P<subject>.*)')
    title_match = title_pattern.match(commit_title)

    # Convert into a boolean
    title_have_not_matched = title_match is None

    if title_have_not_matched is True:
        common.error(
            "Commit '"
            + commit_hash
            + "' with title '"
            + commit_title
            + "' does not follow Sheldon rules: '<type>(<scope>): <subject>'.")
    else:
        common.note(
            "Commit '"
            + commit_hash
            + "' with title '"
            + commit_title
            + "' follows Sheldon rules.")

    return title_have_not_matched


# check that the author is not anonymous
def __check_commit_author(commit_hash, commit_author):
    # Test the title against regex
    author_pattern = re.compile(r'\.*anonymous\.*')
    author_match = author_pattern.match(commit_author.lower())

    # Convert into a boolean
    author_have_matched = author_match is not None

    if author_have_matched is True:
        common.error(
            "Commit '"
            + commit_hash
            + "' has anonymous author.")

    return author_have_matched


def check_commit_messages(commit_messages):
    results = [False]

    for commit_message in commit_messages:
        # Split commit message according to "--pretty=format:%h:%aE:%s"
        split_message = commit_message.split(':', 2)

        if len(split_message) == 3:
            # Extract the type
            commit_hash = split_message[0]
            commit_author = split_message[1]
            commit_title = split_message[2]

            results.append(__check_commit_title(commit_hash, commit_title))
            results.append(__check_commit_author(commit_hash, commit_author))

    return results
