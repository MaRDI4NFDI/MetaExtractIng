import unittest
import subprocess
import os
import filecmp

class TestExtractOutput(unittest.TestCase):
    def test_expected_result(self):
        os.chdir(f'src/meta_extractIng')
        for name in ['csv', 'netcdf', 'open_dihu', 'gromacs']:
            _ = subprocess.run(
                ['python', f'{name}_extractor.py'],
                input=f'simulations/{name}', 
                text=True,
                capture_output=True
            )
            
            output = f'simulations//{name}/__output__'
            expected = f'simulations//{name}/__expected__'

            # Check if folder __output__ and __expected__ exist
            self.assertTrue(os.path.exists(output), f"For {name}, folder __output__ does not exist.")
            self.assertTrue(os.path.exists(expected), f"For {name}, folder __expected__ does not exist.")

            # Helper function to filter out .DS_Store files
            def filter_ds_store(names):
                return [name for name in names if name != '.DS_Store']

            # Compare the contents of folder __output__ and folder __expected__
            comparison = filecmp.dircmp(output, expected)
            comparison.left_only = filter_ds_store(comparison.left_only)
            comparison.right_only = filter_ds_store(comparison.right_only)
            comparison.diff_files = filter_ds_store(comparison.diff_files)

            # Check that there are no differences in files or subdirectories
            self.assertEqual(comparison.left_only, [], f"For {name}, files only in {output}: {comparison.left_only}")
            self.assertEqual(comparison.right_only, [], f"For {name}, files only in {expected}: {comparison.right_only}")
            self.assertEqual(comparison.diff_files, [], f"For {name}, files with differences between {output} and {expected}: {comparison.diff_files}")

            # Optionally, check the contents of common subdirectories recursively
            _, mismatch, errors = filecmp.cmpfiles(output, expected, filter_ds_store(comparison.common_files), shallow=False)
            self.assertEqual(mismatch, [], f"For {name}, files that differ in content between {output} and {expected}: {mismatch}")
            self.assertEqual(errors, [], f"For {name}, errors encountered while comparing files between {output} and {expected}: {errors}")

if __name__ == '__main__':
    unittest.main()
