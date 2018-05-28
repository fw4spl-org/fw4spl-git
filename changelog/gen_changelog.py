
import os,sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../hooks'))

import common
import re
import check_commit


def gitlog(rev, rev2, options=''):
    result = common.execute_command('git log --first-parent ' + options + ' ' + rev + '..' + rev2)

    if result.status == 0:
        return result.out

    warn(result.out)
    return ""

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

        for line in commit.splitlines():

            if found_commit:
                commit_description += line + '\n'

            else:
                title_pattern = re.compile(check_commit.TITLE_PATTERN_REGEX)
                title_match = title_pattern.search(line)

                if title_match:
                    commit_type = title_match.group('type')
                    commit_scope = title_match.group('scope')
                    commit_subject = title_match.group('subject').strip(' ')

                    if commit_type == 'merge':
                        commit_type = 'feat'
                    found_commit = True

        if found_commit:

            if not changelog.has_key(commit_type):
                changelog[commit_type] = []

            changelog[commit_type].append([commit_scope, commit_subject, commit_description])

    formatted_changelog = 'Changelog between FW4SPL ' + rev + ' and ' + rev2 + '\n'
    formatted_changelog += '******************************************\n\n'

    for commit_type, entries in changelog.iteritems():

        if commit_type in ['feat']:
            formatted_changelog += 'New features:\n=============\n\n'

        if commit_type in ['fix']:
            formatted_changelog += 'Bug fixes:\n==========\n\n'

        for entry in entries:
            formatted_changelog += entry[0] + '\n------------\n'
            formatted_changelog += entry[1] + '\n'
            formatted_changelog += entry[2] + '\n'

    print formatted_changelog

gen_log('15.0.0', '16.0.0')