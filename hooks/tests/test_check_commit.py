#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

import check_commit
import common


class TestCheckCommit(unittest.TestCase):
    def test_check_commit_with_valid_title(self):
        # Be verbose by default
        common.g_trace = True

        # Apply the hook
        result = check_commit.check_commit_messages(
            ["ffffffff:devil@ircad.fr:fix(reactor): prevent uncontrolled nuclear fusion. See #666"])

        result += check_commit.check_commit_messages(
            ["ffffffff:devil@ircad.fr:chore(*): apply latest sheldon"])

        result += check_commit.check_commit_messages(
            ["ffffffff:devil@ircad.fr:refactor(plugin_config.cmake): generate at build instead at configure"])

        # Check result
        self.assertFalse(any(result), "A valid commit has been detected as invalid.")

    def test_check_commit_with_invalid_title(self):
        # Be verbose by default
        common.g_trace = True

        # Apply the hook
        result = check_commit.check_commit_messages(
            ["ffffffff:devil@ircad.fr:It's the party at the village"])

        # Check result
        self.assertTrue(any(result), "An invalid commit has not been detected as invalid")

    def test_check_commit_with_valid_author(self):
        # Be verbose by default
        common.g_trace = True

        # Apply the hook
        result = check_commit.check_commit_messages(
            ["ffffffff:god@ircad.fr:fix(reactor): prevent uncontrolled nuclear fusion. See #666"])

        # Check result
        self.assertFalse(any(result), "A valid commit has been detected as invalid.")

    def test_check_commit_with_invalid_author(self):
        # Be verbose by default
        common.g_trace = True

        # Apply the hook
        result = check_commit.check_commit_messages(
            ["ffffffff:anonymous@nowhere.com:fix(reactor): Prevent uncontrolled nuclear fusion. See #666"])

        # Check result
        self.assertTrue(any(result), "An invalid commit has not been detected as invalid")


if __name__ == '__main__':
    unittest.main()
