#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import unittest

import common
import forbidtoken


class TestForbidtoken(unittest.TestCase):
    def test_crlf_with_lf_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_lf.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'crlf')

        # Check result
        self.assertFalse(result, "crlf were detected in test file.")

    def test_crlf_with_crlf_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_crlf.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'crlf')

        # Check result
        self.assertTrue(result, "crlf were not detected in test file.")

    def test_cr_with_lf_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_lf.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'cr')

        # Check result
        self.assertFalse(result, "cr were detected in test file.")

    def test_cr_with_cr_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_cr.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'cr')

        # Check result
        self.assertTrue(result, "cr were not detected in test file.")

    def test_tab_with_lf_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_lf.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'tab')

        # Check result
        self.assertFalse(result, "tab were detected in test file.")

    def test_tab_with_tab_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_tab.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'tab')

        # Check result
        self.assertTrue(result, "tab were not detected in test file.")

    def test_lgpl_with_lf_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_lf.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'lgpl')

        # Check result
        self.assertFalse(result, "lgpl were detected in test file.")

    def test_lgpl_with_lgpl_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_lgpl.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'lgpl')

        # Check result
        self.assertTrue(result, "lgpl were not detected in test file.")

    def test_oslmlog_with_lf_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_lf.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'oslmlog')

        # Check result
        self.assertFalse(result, "oslmlog were detected in test file.")

    def test_oslmlog_with_oslmlog_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_oslm.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'oslmlog')

        # Check result
        self.assertTrue(result, "oslmlog were not detected in test file.")

    def test_digraph_with_lf_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_lf.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'digraphs')

        # Check result
        self.assertFalse(result, "digraphs were detected in test file.")

    def test_digraphs_with_digraphs_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_digraphs.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'digraphs')

        # Check result
        self.assertTrue(result, "digraphs were not detected in test file.")

    def test_digraphs_with_nodigraphs_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_nodigraphs.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'digraphs')

        # Check result
        self.assertFalse(result, "digraphs were detected in test file.")

    def test_doxygen_with_lf_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_lf.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'doxygen')

        # Check result
        self.assertFalse(result, "doxygen were detected in test file.")

    def test_doxygen_with_doxygen_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_doxygen.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'doxygen')

        # Check result
        self.assertTrue(result, "doxygen were not detected in test file.")

    def test_badwords_with_lf_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_lf.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'badwords')

        # Check result
        self.assertFalse(result, "copain were detected in test file.")

    def test_badwords_with_copain_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/forbidtoken_copain.cpp')

        # Apply the hook
        result = forbidtoken.forbidtoken(file, 'badwords')

        # Check result
        self.assertTrue(result, "copain were not detected in test file.")


if __name__ == '__main__':
    unittest.main()
