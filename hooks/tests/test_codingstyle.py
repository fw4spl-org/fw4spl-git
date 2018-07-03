#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import filecmp
import os
import shutil
import unittest

import codingstyle
import common


class TestCodingstyle(unittest.TestCase):
    @classmethod
    def __are_directory_identical(cls, dircmp):
        if len(dircmp.diff_files) > 0 or len(dircmp.funny_files) > 0:
            return False
        else:
            for sub_dircmp in list(dircmp.subdirs.values()):
                sub_return = cls.__are_directory_identical(sub_dircmp)
                if not sub_return:
                    return False
        return True

    @classmethod
    def __execute_codingstyle(cls, test, enableReformat, *args, **kwargs):
        # Be verbose by default
        common.g_trace = True

        # Be sure to use a fixed year
        codingstyle.YEAR = 2999

        # Construct the base path
        dir_path = os.path.dirname(os.path.realpath(__file__))
        test_data_path = dir_path + '/' + test

        if enableReformat:
            # Save the test data
            test_data_path_copy = test_data_path + str(os.getpid())
            shutil.copytree(test_data_path, test_data_path_copy)

            try:
                # Find the files to check
                files = common.directory_on_disk(test_data_path_copy)

                # Apply the hook
                result, reformatted = codingstyle.codingstyle(files, True, True, False)

            except:
                shutil.rmtree(test_data_path_copy)
                raise

            # Compare the result with a verbatim
            verbatim = kwargs.get('verbatim', None)

            if verbatim is not None:
                verbatim_data_path = dir_path + '/' + verbatim
                dircmp = filecmp.dircmp(verbatim_data_path, test_data_path_copy)
                if not cls.__are_directory_identical(dircmp):
                    result = True

            # Cleanup
            shutil.rmtree(test_data_path_copy)
        else:
            # Find the files to check
            files = common.directory_on_disk(test_data_path)

            # Apply the hook on source directly
            result, reformatted = codingstyle.codingstyle(files, False, True, False)

        return result, reformatted

    def test_codingstyle_formatted(self):
        result, reformatted = self.__execute_codingstyle('data/Codingstyle/Formatted', False)

        # Check result
        self.assertFalse(result, "Codingstyle function should return no error.")
        self.assertFalse(len(reformatted) > 0, "No file should have been reformatted.")

    def test_codingstyle_lgpl_check(self):
        result, reformatted = self.__execute_codingstyle('data/Codingstyle/Lgpl', False)

        # Check result
        self.assertTrue(result, "Codingstyle function should return True as one file at least contains one error.")
        self.assertFalse(len(reformatted) > 0, "No file should have been fixed.")

    def test_codingstyle_lgpl_reformat(self):
        result, reformatted = self.__execute_codingstyle('data/Codingstyle/Lgpl', True)

        # Check result
        self.assertFalse(result, "Codingstyle function should return no error.")
        self.assertTrue(len(reformatted) > 0, "Some files should have been fixed.")

    def test_codingstyle_sort_includes_check(self):
        result, reformatted = self.__execute_codingstyle('data/Codingstyle/Sort_includes', False)

        # Check result
        self.assertTrue(result, "Codingstyle function should return True as one file at least contains one error.")
        self.assertFalse(len(reformatted) > 0, "No file should have been fixed.")

    def test_codingstyle_sort_includes_reformat(self):
        result, reformatted = self.__execute_codingstyle('data/Codingstyle/Sort_includes', True)

        # Check result
        self.assertFalse(result, "Codingstyle function should return no error.")
        self.assertTrue(len(reformatted) > 0, "Some files should have been fixed.")

    def test_codingstyle_header_guards_typo_check(self):
        result, reformatted = self.__execute_codingstyle('data/Codingstyle/Header_guards_typo', False)

        # Check result
        self.assertTrue(result, "Codingstyle function should return True as one file at least contains one error.")
        self.assertFalse(len(reformatted) > 0, "No file should have been fixed.")

    def test_codingstyle_header_guards_typo_reformat(self):
        result, reformatted = self.__execute_codingstyle('data/Codingstyle/Header_guards_typo', True)

        # Check result
        self.assertFalse(result, "Codingstyle function should return no error.")
        self.assertTrue(len(reformatted) > 0, "Some files should have been fixed.")

    def test_codingstyle_header_guards_forgotten_check(self):
        result, reformatted = self.__execute_codingstyle('data/Codingstyle/Header_guards_forgotten', False)

        # Check result
        self.assertTrue(result, "Codingstyle function should return True as one file at least contains one error.")
        self.assertFalse(len(reformatted) > 0, "No file should have been fixed.")

    def test_codingstyle_uncrusitfy_formatted_check(self):
        result, reformatted = self.__execute_codingstyle('data/Codingstyle/Uncrustify_formatted', False)

        # Check result
        self.assertFalse(result, "Codingstyle function should return True as no file contains error.")
        self.assertFalse(len(reformatted) > 0, "No file should have been fixed.")

    def test_codingstyle_uncrusitfy_unformatted_check(self):
        result, reformatted = self.__execute_codingstyle('data/Codingstyle/Uncrustify_unformatted', False)

        # Check result
        self.assertTrue(result, "Codingstyle function should return False as one file at least contains one error.")
        self.assertFalse(len(reformatted) > 0, "No file should have been fixed.")

    def test_codingstyle_uncrustify_unformatted_reformat(self):
        result, reformatted = self.__execute_codingstyle('data/Codingstyle/Uncrustify_unformatted',
                                                         True,
                                                         verbatim='data/Codingstyle/Uncrustify_formatted')

        # Check result
        self.assertFalse(result, "Codingstyle function should return no error.")
        self.assertTrue(len(reformatted) > 0, "Some files should have been fixed.")


if __name__ == '__main__':
    unittest.main()
