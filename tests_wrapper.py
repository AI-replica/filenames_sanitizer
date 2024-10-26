import glob
import unittest
import doctest
import coverage
import sys
import re
import sys
import os
from unittest.mock import patch, MagicMock


def genereate_coverage_badge(cov, name_suffix=""):
    """
    Generate a coverage badge SVG based on the coverage report.

    This function creates an SVG badge showing the coverage percentage and color-codes it
    based on the coverage level.

    Inspired by this code by Danilo Bargen, released under MIT License:
    https://github.com/dbrgn/coverage-badge

    Args:
        cov (coverage.Coverage): A coverage.py Coverage object.
        name_suffix (str, optional): Suffix to add to the SVG filename. Defaults to "".

    Returns:
        list: A list of strings representing the lines of the generated SVG file.

    Examples:
        >>> import os
        >>> from unittest.mock import Mock
        >>> mock_cov = Mock()
        >>> mock_cov.report.return_value = 85.5
        >>> badge_lines = genereate_coverage_badge(mock_cov, name_suffix="_mock")
        >>> len(badge_lines) > 0
        True
        >>> any('86%' in line for line in badge_lines)
        True
        >>> any('#aa1' in line for line in badge_lines)
        True
        >>> os.path.exists('coverage_mock.svg')
        True
        >>> os.remove('coverage_mock.svg')

    Note:
        This function writes the SVG to a file named 'coverage{suffix}.svg' in the current directory.
        The doctests will create and delete this file during testing.
    """
    coverage_template = """<?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg" width="104" height="20">
    <rect width="63" height="20" fill="#555"/>
    <rect x="63" width="41" height="20" fill="{{ color }}"/>
    <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
        <text x="31.5" y="14">coverage</text>
        <text x="83.5" y="14">{{ total }}%</text>
    </g>
    </svg>
"""
    total_str = str(int(round(cov.report(show_missing=True, skip_covered=True))))
    color = next(
        c
        for r, c in [
            (95, "#4c1"),  # green
            (90, "#9c0"),
            (75, "#aa1"),
            (60, "#db2"),
            (40, "#f70"),
            (0, "#e54"),  # red
        ]
        if int(total_str) >= r
    )
    badge = coverage_template.replace("{{ total }}", total_str).replace(
        "{{ color }}", color
    )
    filename = f"coverage{name_suffix}.svg"
    with open(filename, "w") as f:
        f.write(badge)
    return open(filename).readlines()


def recursive_file_search(path, file_type):
    """
    Recursively search for files of a specific type in the given path.

    Args:
        path (str): The directory path to start the search from.
        file_type (str): The file extension to search for (e.g., '.py', '.txt').

    Returns:
        list: A sorted list of file paths matching the given file type.

    Examples:
        >>> import tempfile
        >>> import os
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Create a temporary directory structure
        ...     os.makedirs(os.path.join(tmpdir, 'subdir1'))
        ...     os.makedirs(os.path.join(tmpdir, 'subdir2'))
        ...     open(os.path.join(tmpdir, 'file1.txt'), 'w').close()
        ...     open(os.path.join(tmpdir, 'file2.py'), 'w').close()
        ...     open(os.path.join(tmpdir, 'subdir1', 'file3.txt'), 'w').close()
        ...     open(os.path.join(tmpdir, 'subdir2', 'file4.py'), 'w').close()
        ...
        ...     # Test the function
        ...     result = recursive_file_search(tmpdir, '.txt')
        ...     len(result)
        2
        >>> any('file1.txt' in path for path in result)
        True
        >>> any('file3.txt' in path for path in result)
        True
        >>> any('file2.py' in path for path in result)
        False

        >>> # Test with empty directory
        >>> with tempfile.TemporaryDirectory() as empty_dir:
        ...     result = recursive_file_search(empty_dir, '.txt')
        ...     len(result)
        0

        >>> # Test with non-existent file type
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     open(os.path.join(tmpdir, 'file1.txt'), 'w').close()
        ...     result = recursive_file_search(tmpdir, '.nonexistent')
        ...     len(result)
        0
    """
    # print("path", path)
    files = glob.glob(os.path.join(path, "**", "*" + file_type), recursive=True)
    sorted_files = sorted(files)
    return sorted_files


def find_modules(exclusions=None):
    """
    Find Python modules in the current directory and its subdirectories, excluding specified paths.

    Args:
        exclusions (list, optional): List of strings to exclude from the search. Defaults to None.

    Returns:
        list: A list of module names (as strings) found in the directory structure.

    Examples:
        >>> import tempfile
        >>> import os
        >>> original_dir = os.getcwd()  # Save the original directory
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Create a temporary directory structure
        ...     os.chdir(tmpdir)
        ...     os.makedirs('pkg1')
        ...     os.makedirs('pkg2')
        ...     open('module1.py', 'w').close()
        ...     open(os.path.join('pkg1', 'module2.py'), 'w').close()
        ...     open(os.path.join('pkg2', 'module3.py'), 'w').close()
        ...     open(os.path.join('pkg2', 'excluded.py'), 'w').close()
        ...
        ...     # Test with no exclusions
        ...     result = find_modules()
        ...     sorted_result = sorted(result)
        ...     os.chdir(original_dir)  # Restore the original directory
        ...     sorted_result
        ['module1', 'pkg1.module2', 'pkg2.excluded', 'pkg2.module3']

        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     os.chdir(tmpdir)
        ...     os.makedirs('pkg1')
        ...     os.makedirs('pkg2')
        ...     open('module1.py', 'w').close()
        ...     open(os.path.join('pkg1', 'module2.py'), 'w').close()
        ...     open(os.path.join('pkg2', 'module3.py'), 'w').close()
        ...     open(os.path.join('pkg2', 'excluded.py'), 'w').close()
        ...
        ...     # Test with exclusions
        ...     result = find_modules(exclusions=['pkg2'])
        ...     sorted_result = sorted(result)
        ...     os.chdir(original_dir)  # Restore the original directory
        ...     sorted_result
        ['module1', 'pkg1.module2']

        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     os.chdir(tmpdir)
        ...     # Test with empty directory
        ...     result = find_modules()
        ...     os.chdir(original_dir)  # Restore the original directory
        ...     result
        []

        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     os.chdir(tmpdir)
        ...     # Test with non-Python files
        ...     open('not_a_module.txt', 'w').close()
        ...     result = find_modules()
        ...     os.chdir(original_dir)  # Restore the original directory
        ...     result
        []
    """
    file_names = recursive_file_search("", ".py")
    if exclusions is None:
        exclusions = []
    module_names = []
    for name in file_names:
        if not any(exclusion in name for exclusion in exclusions):
            clean_name = name.replace("/", ".").replace(".py", "")
            module_names.append(clean_name)
    return module_names


def build_test_suite(module_names):
    test_suite = unittest.TestSuite()
    for name in module_names:
        test_suite.addTests(doctest.DocTestSuite(name))
        print("Added to the test_suite:", name)
    return test_suite


def run_test_suite(test_suite):
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(test_suite)


def run_tests_with_coverage():
    """
    Run tests with coverage measurement.

    This function sets up coverage measurement, runs tests, and returns the results along with the coverage object.

    Returns:
        tuple: A tuple containing the test result and the coverage object.

    Examples:
        >>> import unittest.mock
        >>> with unittest.mock.patch('tests_wrapper.coverage.Coverage') as mock_coverage, unittest.mock.patch('tests_wrapper.build_test_suite') as mock_build_suite, unittest.mock.patch('tests_wrapper.run_test_suite') as mock_run_suite:
        ...     # Set up mock objects
        ...     mock_cov = unittest.mock.MagicMock()
        ...     mock_coverage.return_value = mock_cov
        ...     mock_result = unittest.mock.MagicMock()
        ...     mock_run_suite.return_value = mock_result
        ...
        ...     # Run the function
        ...     result, cov = run_tests_with_coverage()
        ...
        ...     # Verify function behavior
        ...     mock_coverage.assert_called_once_with(omit=['*/venv/'])
        ...     mock_cov.start.assert_called_once()
        ...     mock_cov.stop.assert_called_once()
        ...     mock_cov.save.assert_called_once()
        ...     mock_cov.load.assert_called_once()
        ...     mock_build_suite.assert_called_once()
        ...     mock_run_suite.assert_called_once()
        ...     assert result == mock_result
        ...     assert cov == mock_cov

    Note:
        This doctest uses mocking to avoid actually running tests or measuring real coverage.
    """
    exclusions = ["venv/"]

    module_names = find_modules(exclusions)

    exclusions_for_cov = ["*/" + exclusion for exclusion in exclusions]

    cov = coverage.Coverage(omit=exclusions_for_cov)
    cov.start()

    test_suite = build_test_suite(module_names)
    result = run_test_suite(test_suite)

    cov.stop()
    cov.save()
    cov.load()

    return result, cov


def test(badge_name_suffix=""):
    """
    Run tests with coverage and generate a coverage badge.

    This function copies and renames the state class, runs tests with coverage,
    and generates a coverage badge.

    Args:
        state_class_path_prefix (str): Prefix for the path where the mock state class will be created.
        badge_name_suffix (str): Suffix for the name of the generated coverage badge.

    Returns:
        tuple: A tuple containing:
            - copy_success7 (bool): Whether the state class was successfully copied and renamed.
            - result (unittest.TestResult): The result of running the tests.
            - cov (coverage.Coverage): The coverage object.
            - svg_lines (list): The lines of the generated SVG badge.

    Examples:
        >>> import tempfile
        >>> import os
        >>> import unittest.mock
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Set up the test environment
        ...     original_dir = os.getcwd()
        ...     os.chdir(tmpdir)
        ...
        ...     # Mock run_tests_with_coverage
        ...     mock_result = unittest.mock.MagicMock()
        ...     mock_cov = unittest.mock.MagicMock()
        ...     mock_cov.report.return_value = 85.5
        ...     with unittest.mock.patch('tests_wrapper.run_tests_with_coverage', return_value=(mock_result, mock_cov)):
        ...         # Run the test function
        ...         copy_success, result, cov, svg_lines = test(badge_name_suffix='_test')
        ...
        ...     # Check the results
        ...     print(copy_success)
        ...     print(result == mock_result)
        ...     print(cov == mock_cov)
        ...     print(len(svg_lines) > 0)
        ...     print(os.path.exists('coverage_test.svg'))
        ...
        ...     # Clean up
        ...     os.chdir(original_dir)
        True
        True
        True
        True
        True

    Note:
        This test creates temporary files and directories which are cleaned up after the test.
        It mocks the `run_tests_with_coverage` function to avoid running actual tests.
    """
    result, cov = run_tests_with_coverage()
    svg_lines = genereate_coverage_badge(cov, badge_name_suffix)
    # sys.exit(not result.wasSuccessful())
    return True, result, cov, svg_lines


if __name__ == "__main__":  # pragma: no cover
    test()
