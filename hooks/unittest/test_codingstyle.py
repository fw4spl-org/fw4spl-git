import os
import shutil
import unittest

import codingstyle
import common


class TestCodingstyle(unittest.TestCase):
    @staticmethod
    def __execute_codingstyle(test, enableReformat):
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
                result, reformatted = codingstyle.codingstyle(files, True, True)

            except:
                shutil.rmtree(test_data_path_copy)
                raise

            # Cleanup
            shutil.rmtree(test_data_path_copy)
        else:
            # Find the files to check
            files = common.directory_on_disk(test_data_path)

            # Apply the hook on source directly
            result, reformatted = codingstyle.codingstyle(files, False, True)

        return result, reformatted

    def test_codingstyle_formatted(self):
        result, reformatted = self.__execute_codingstyle('data/Codingstyle/Formatted', False)

        # Check result
        self.assertFalse(result, "Codingstyle function should return no error.")
        self.assertFalse(len(reformatted) > 0, "No file should have been reformatted.")

    def test_codingstyle_lgpl_check(self):
        result, reformatted = self.__execute_codingstyle('data/Codingstyle/Lgpl', False)

        # Check result
        self.assertTrue(result, "Codingstyle function should return False as one file at least contains one error.")
        self.assertFalse(len(reformatted) > 0, "No file should have been fixed.")

    def test_codingstyle_lgpl_reformat(self):
        result, reformatted = self.__execute_codingstyle('data/Codingstyle/Lgpl', True)

        # Check result
        self.assertFalse(result, "Codingstyle function should return no error.")
        self.assertTrue(len(reformatted) > 0, "Some files should have been fixed.")


if __name__ == '__main__':
    unittest.main()
