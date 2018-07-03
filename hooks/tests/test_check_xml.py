#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import unittest

import check_xml
import common


class TestCheckXml(unittest.TestCase):
    def test_check_xml_with_valid_xml_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/check_xml_valid.xml')

        # Apply the hook
        result = check_xml.check_xml(file)

        # Check result
        self.assertFalse(result, "Valid xml detected as invalid.")

    def test_check_xml_with_invalid_xml_file(self):
        # Be verbose by default
        common.g_trace = True

        # Load the test file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file = common.file_on_disk(dir_path + '/data/check_xml_invalid.xml')

        # Apply the hook
        result = check_xml.check_xml(file)

        # Check result
        self.assertTrue(result, "Invalid xml detected as valid.")


if __name__ == '__main__':
    unittest.main()
