#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../hooks'))

import common
import re
import check_commit
import argparse

# FIXME: For now, we duplicate the regex of check_commit.py because some commits are not always properly formatted
# The only difference for now is the subject starting with a capital (which is forbidden normally)
TITLE_PATTERN_REGEX = r'(?P<type>' + '|'.join(check_commit.CONST.TYPES) + ')\((?P<scope>\S+)\):(?P<subject> [A-z].*)'

def gitlog(rev, rev2, options=''):
    command = 'git log --first-parent ' + options + ' ' + rev + '..' + rev2
    result = common.execute_command(command)

    if result.status == 0:
        return result.out

    raise Exception('Error executing "%s"', command )


def gen_log(rev, rev2):
    difflog = gitlog(rev, rev2, '--pretty=format:%P')
    parent = difflog.split(' ')[1]

    difflog = gitlog(rev, parent)

    commits = re.split(r'commit [a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9][a-f0-9]', difflog)

    changelog = dict()

    for commit in commits:

        found_commit = False
        commit_description = ""
        commit_type = ""
        commit_scope = ""
        commit_subject = ""

        regex_indent = re.compile('^    ')
        regex_see_mr = re.compile('^See merge request.*')
        regex_merge_branch = re.compile('^Merge branch.*')
        regex_close_bug = re.compile('^[Cc]loses?.*#.*')
        regex_howto = re.compile('^## How to test.*')
        regex_fix_symbols = re.compile('(::[A-z:]*) ')

        was_previous_line_empty = False
        for line in commit.splitlines():

            if found_commit:

                # Strip some text...
                description_line = re.sub(regex_indent, '', line)
                empty_line =  len(description_line) == 0
                description_line = re.sub(regex_see_mr, '', description_line)
                description_line = re.sub(regex_close_bug, '', description_line)
                description_line = re.sub(regex_merge_branch, '', description_line)
                description_line = re.sub(regex_fix_symbols, r'`\1`', description_line)

                if re.match(regex_howto, description_line):
                    # Simply stops there if someone forgot the usual gitlab description part
                    break
                if len(description_line):
                    commit_description += description_line + '\n'
                    was_previous_line_empty = False
                elif empty_line:
                    if not was_previous_line_empty:
                        commit_description += '\n'
                        was_previous_line_empty = True
                else:
                    was_previous_line_empty = True

            else:
                title_pattern = re.compile(TITLE_PATTERN_REGEX)
                title_match = title_pattern.search(line)

                if title_match:
                    commit_scope = title_match.group('scope')
                    if commit_scope == 'master':
                        continue

                    commit_type = title_match.group('type')
                    commit_subject = title_match.group('subject').strip(' ')
                    # Ensure the scope has a proper line ending
                    commit_subject = commit_subject.strip('\n')

                    if commit_subject[-1] != '.':
                        commit_subject += '.'

                    # Force upper case on the first letter
                    commit_subject = commit_subject[0].upper() + commit_subject[1:]

                    commit_subject = '*' + commit_subject + '*'
                    commit_subject += '\n'

                    if commit_type == 'merge':
                        commit_type = 'feat'
                    found_commit = True

        if found_commit:

            if not changelog.has_key(commit_type):
                changelog[commit_type] = []

            changelog[commit_type].append([commit_scope, commit_subject, commit_description])

    try:
        repo_name = open(".fw4spl", 'r').read()
    except:
        repo_name = open(".fw4spl-deps", 'r').read()
    repo_name = repo_name.strip('\n')

    formatted_changelog = '# ' + repo_name + ' ' + rev2 + '\n\n'

    for commit_type, entries in changelog.iteritems():

        if commit_type in ['feat']:
            formatted_changelog += '## New features:\n\n'
        elif commit_type in ['fix']:
            formatted_changelog += '## Bug fixes:\n\n'
        elif commit_type in ['docs']:
            formatted_changelog += '## Documentation:\n\n'
        elif commit_type in ['refactor']:
            formatted_changelog += '## Refactor:\n\n'
        elif commit_type in ['perf']:
            formatted_changelog += '## Performances:\n\n'
        else:
            continue

        for entry in entries:
            formatted_changelog += "### " + entry[0] + '\n\n'
            if not re.match(r' ?Into', entry[1]):
                formatted_changelog += entry[1]
            formatted_changelog += entry[2]

    print formatted_changelog


parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Generate a changelog for a FW4SPL repository.',
)

parser.add_argument('path',
                    nargs='*',
                    help='Git path, can be a commit or two commits.')

args = parser.parse_args()

try:
    rev1 = args.path[0]
    rev2 = args.path[1]
except:
    parser.print_usage()
    exit(1)

gen_log(rev1, rev2)
