import datetime
import os
import platform
import shutil
import pathlib
import filecmp

JUNK_FILES = [".DS_Store", "Thumbs.db"]


def create_nested_dirs(raw_nested_path, mock_crash7=False, mock_partial_success7=False):
    """
    >>> test_path = "some/path"
    >>> create_nested_dirs(test_path, mock_crash7=True)
    failed to create dir some/path: division by zero
    False
    >>> create_nested_dirs(test_path, mock_partial_success7=True)
    failed to create dir some/path for unknown reasons
    False
    >>> del_sucess7,_ = delete_dir(test_path); del_sucess7
    True
    """
    # Setting the process's file mode creation mask to 0 (don't restrict any file permissions)
    os.umask(0)

    if raw_nested_path.endswith("/"):
        nested_path = raw_nested_path
    else:
        nested_path = raw_nested_path + "/"

    success7 = False
    try:
        1 / 0 if mock_crash7 else None
        pathlib.Path(nested_path).mkdir(parents=True, exist_ok=True)
        if pathlib.Path(nested_path).is_dir() and not mock_partial_success7:
            success7 = True
            # color_print(f"sucessfuly created dir {raw_nested_path}", "green")

        else:
            print(f"failed to create dir {raw_nested_path} for unknown reasons")
    except Exception as e:
        print(f"failed to create dir {raw_nested_path}: {e}")

    return success7


def delete_dir(dir_path, mock_partial_success7=False):
    """
    >>> test_path = "mock_data/mock_dirs_to_delete/doomed_dir/"
    >>> success7 = create_nested_dirs(test_path); success7
    True
    >>> delete_dir(test_path)
    (True, 'successfully deleted mock_data/mock_dirs_to_delete/doomed_dir/')
    >>> delete_dir("non-existent-dir")
    (True, "the dir doesn't exist already: non-existent-dir")
    >>> test_path2 = "some/path"
    >>> success7 = create_nested_dirs(test_path2)
    >>> delete_dir(test_path2, mock_partial_success7=True)
    (False, 'failed to delete some/path')
    """
    success7 = True
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path)
        if os.path.isdir(dir_path) or mock_partial_success7:
            report = f"failed to delete {dir_path}"
            success7 = False
        else:
            report = f"successfully deleted {dir_path}"
    else:
        report = f"the dir doesn't exist already: {dir_path}"
    return success7, report


def is_identical_dir(
    src, dst, mock_funny_file7=False, mock_error7=False, mock_mismatch7=False
):
    """
    A recursive function to verify that the dst directory is an exact copy of the src directory.
    Returns a tuple containing a boolean (True if identical, False otherwise) and a list of mismatches.

    "Funny files" (technical term) in filecmp are files that exist in both directories being compared
    but couldn't be compared normally due to issues like permission problems, symbolic links, or special file types.

    >>> a = "mock_data/identical_and_different_dirs/A"
    >>> b = "mock_data/identical_and_different_dirs/B"
    >>> c = "mock_data/identical_and_different_dirs/C"
    >>> d = "mock_data/identical_and_different_dirs/D"
    >>> is_identical_dir(a, b)
    (True, [])
    >>> identical7, diffs = is_identical_dir(a, c); identical7
    False
    >>> diffs
    ['someFile.txt', 'In subdirectory someDir: Only in mock_data/identical_and_different_dirs/A/someDir: another_file.txt', 'In subdirectory someDir: Only in mock_data/identical_and_different_dirs/C/someDir: different_name.txt']
    >>> is_identical_dir(b, c)[0]
    False
    >>> is_identical_dir(c, d)[0]
    False
    >>> is_identical_dir("bad path", d)[0]
    False
    >>> is_identical_dir(a, b, mock_funny_file7=True)[0]
    True
    >>> is_identical_dir(a, c, mock_error7=True)[0]
    False
    >>> is_identical_dir(a, b, mock_error7=True)[0]
    True
    """

    if not os.path.isdir(src) or not os.path.isdir(dst):
        return False, [f"Directory mismatch: {src} or {dst} is not a directory"]

    if mock_mismatch7:
        return False, ["a fake mismatch, as if directories are not identical"]

    mismatches = []
    dirs_cmp = filecmp.dircmp(src, dst)

    if len(dirs_cmp.left_only) > 0:
        mismatches.extend([f"Only in {src}: {item}" for item in dirs_cmp.left_only])
    if len(dirs_cmp.right_only) > 0:
        mismatches.extend([f"Only in {dst}: {item}" for item in dirs_cmp.right_only])
    if len(dirs_cmp.funny_files) > 0 or mock_funny_file7:
        mismatches.extend([f"Funny file: {item}" for item in dirs_cmp.funny_files])

    (_, mismatch, errors) = filecmp.cmpfiles(
        src, dst, dirs_cmp.common_files, shallow=False
    )
    if len(mismatch) > 0:
        mismatches.extend([f"{item}" for item in mismatch])
    if len(errors) > 0 or mock_error7:
        mismatches.extend([f"Error: {item}" for item in errors])

    for common_dir in dirs_cmp.common_dirs:
        new_src = os.path.join(src, common_dir)
        new_dst = os.path.join(dst, common_dir)
        identical, sub_mismatches = is_identical_dir(new_src, new_dst)
        if not identical:
            mismatches.extend(
                [f"In subdirectory {common_dir}: {item}" for item in sub_mismatches]
            )

    mismatches = [m for m in mismatches if os.path.basename(m) not in JUNK_FILES]
    # print("test mismatches:", mismatches)

    return len(mismatches) == 0, mismatches


def copy_directory(src, dst, mock_mismatch7=False):
    """
    Recursively copy the contents of a directory to another directory.

    >>> src = "mock_data/identical_and_different_dirs/A"
    >>> dst = "mock_data/identical_and_different_dirs/copy of A"
    >>> copy_directory(src, dst)
    True
    >>> delete_dir(dst)
    (True, 'successfully deleted mock_data/identical_and_different_dirs/copy of A')
    >>> copy_directory("bad path", dst)
    An error occurred: [Errno 2] No such file or directory: 'bad path'
    False
    >>> copy_directory(src, dst, mock_mismatch7=True)
    Something terribly wrong happened. The dirs aren't identical:
    a fake mismatch, as if directories are not identical
    False
    """
    success7 = False
    try:
        # Create the destination directory if it doesn't exist
        os.makedirs(dst, exist_ok=True)

        # Walk through the source directory
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                # Recursively copy subdirectories
                copy_directory(s, d)
            else:
                # Copy files, including hidden ones
                shutil.copy2(s, d)

        identical7, mismatches = is_identical_dir(
            src, dst, mock_mismatch7=mock_mismatch7
        )
        if identical7:
            success7 = True
        else:
            success7 = False
            print("Something terribly wrong happened. The dirs aren't identical:")
            for mismatch in mismatches:
                print(mismatch)
    except Exception as e:
        print(f"An error occurred: {e}")
        success7 = False
    return success7


def get_paths_for_renaming(directory):
    """
    >>> paths = get_paths_for_renaming("mock_data/identical_and_different_dirs/A")
    >>> paths["dirs"]
    ['mock_data/identical_and_different_dirs/A/someDir']
    >>> files_paths = paths["files"]
    >>> files_paths = [f for f in files_paths if os.path.basename(f) not in JUNK_FILES]
    >>> files_paths
    ['mock_data/identical_and_different_dirs/A/someDir/another_file.txt', 'mock_data/identical_and_different_dirs/A/someFile.txt']
    """
    # print("directory:", directory)
    dir_paths = []
    file_paths = []

    for root, dirs, files in os.walk(directory, followlinks=False):
        dir_paths.extend(os.path.join(root, d) for d in dirs)
        file_paths.extend(os.path.join(root, f) for f in files)

    # Sort both lists
    dir_paths.sort(key=lambda x: (-x.count(os.path.sep), -len(x)))
    file_paths.sort(key=lambda x: (-x.count(os.path.sep), -len(x)))

    return {"dirs": dir_paths, "files": file_paths}


def replace_symlink(old_path, new_path):
    """
    Replace a symlink with a text file containing information about the original symlink.

    On Linux:
    >>> import os, tempfile, platform
    >>> if platform.system() == 'Linux':
    ...     with tempfile.TemporaryDirectory() as temp_dir:
    ...         target_path = os.path.join(temp_dir, 'target.txt')
    ...         with open(target_path, 'w') as f:
    ...             f.write('Target content')
    ...         link_path = os.path.join(temp_dir, 'link')
    ...         os.symlink(target_path, link_path)
    ...         new_path = os.path.join(temp_dir, 'new_file.txt')
    ...         replace_symlink(link_path, new_path)
    ...         new_path_exists7 = os.path.exists(new_path)
    ...         with open(new_path, 'r') as f:
    ...             content = f.read()
    ...         content_ok7 = 'Original symlink:' in content and 'Target:' in content and 'target.txt' in content

    On non-Linux systems (using mocks):
    >>> import unittest.mock, tempfile, os, shutil
    >>> if platform.system() != 'Linux':
    ...     mock_readlink = unittest.mock.patch('os.readlink')
    ...     mock_islink = unittest.mock.patch('os.path.islink')
    ...     mock_unlink = unittest.mock.patch('os.unlink')
    ...     with mock_readlink as mock_readlink, mock_islink as mock_islink, mock_unlink as mock_unlink:
    ...         temp_dir = tempfile.mkdtemp()
    ...         mock_readlink.return_value = '/path/to/target'
    ...         mock_islink.return_value = True
    ...         old_path = os.path.join(temp_dir, 'old_link')
    ...         new_path = os.path.join(temp_dir, 'new_file.txt')
    ...         replace_symlink(old_path, new_path)
    ...         new_path_exists7 = os.path.exists(new_path)
    ...         with open(new_path, 'r') as f:
    ...             content = f.read()
    ...         content_ok7 = 'Original symlink:' in content and 'Target:' in content and '/path/to/target' in content
    ...         mock_unlink.assert_called_once_with(old_path)
    ...         shutil.rmtree(temp_dir, ignore_errors=True)
    >>> content_ok7
    True
    >>> new_path_exists7
    True
    """
    link_target = os.readlink(old_path)
    with open(new_path, "w") as f:
        f.write(f"Original symlink: {old_path}\n")
        f.write(f"Target: {link_target}\n")
        f.write("The file was created by filenames_sanitiser.")

    # Remove the original symlink
    if os.path.islink(old_path):  # Double-check it's still a symlink
        os.unlink(old_path)


def do_actual_renaming(
    proposed_changes, actually_rename7, mock_error7=False, replace_symlinks7=False
):
    """
    Do a test like this:
    copy a dir
    rename in the copy
    compare the original and the copy with is_identical_dir
    delete the copy

    >>> target_dir = "mock_data/temp"
    >>> source_dir = "mock_data/some_files"
    >>> copy_success7 = copy_directory(source_dir, target_dir); copy_success7
    True
    >>> paths_by_kind = get_paths_for_renaming(target_dir)
    >>> kind = "files"
    >>> files_paths = paths_by_kind[kind]
    >>> def mock_filename_shortener(filepath):
    ...    dir_path, filename = os.path.split(filepath)
    ...    new_filename = filename[-6:]
    ...    return os.path.join(dir_path, new_filename)
    >>> proposed_changes = {}
    >>> for old_path in files_paths:
    ...    new_path = mock_filename_shortener(old_path)
    ...    proposed_changes[old_path] = new_path
    >>> success7, failed_renames,_ = do_actual_renaming(proposed_changes, actually_rename7=True)
    >>> success7
    True
    >>> failed_renames
    []
    >>> delete_dir(target_dir)
    (True, 'successfully deleted mock_data/temp')
    >>> copy_success7 = copy_directory(source_dir, target_dir); copy_success7
    True
    >>> success7, failed_renames,_ = do_actual_renaming(proposed_changes, actually_rename7=True, mock_error7=True)
    >>> success7
    False
    >>> _ = delete_dir(target_dir)

    # Ensuring that renaming dirs will not trigger false positives in failures:
    >>> original_dir = "mock_data/some_files"
    >>> target_dir = "mock_copied_dir"
    >>> _ = copy_directory(original_dir, target_dir)
    >>> proposed_changes = {'mock_copied_dir/pdfs with lengthy names/very long names of pdfs definietly worth renaming them for soure': 'mock_copied_dir/pdfs with lengthy names/vryLngNmsOfPdfsDefinietlyWorthRenamingThemForSoure', 'mock_copied_dir/pdfs with lengthy names': 'mock_copied_dir/pdfs_with_lengthy_names'}
    >>> success7, failed_renames, _ = do_actual_renaming(proposed_changes, actually_rename7=True)
    >>> success7
    True
    >>> failed_renames
    []
    >>> _ = delete_dir(target_dir)

    # Test replace_symlinks7 option (using mocks to make it cross-platform):
    >>> import unittest.mock, tempfile, os, shutil
    >>> with unittest.mock.patch('os.path.islink') as mock_islink, unittest.mock.patch('utils.files.replace_symlink') as mock_replace_symlink:
    ...     mock_islink.return_value = True
    ...     temp_dir = tempfile.mkdtemp()
    ...     old_path = os.path.join(temp_dir, 'old_symlink')
    ...     new_path = os.path.join(temp_dir, 'new_file.txt')
    ...     proposed_changes = {old_path: new_path}
    ...     def side_effect(old, new):
    ...         with open(new, 'w') as f:
    ...             f.write("Mocked symlink replacement")
    ...     mock_replace_symlink.side_effect = side_effect
    ...     success7, failed_renames, _ = do_actual_renaming(proposed_changes, actually_rename7=True, replace_symlinks7=True)
    ...     mock_replace_symlink.assert_called_once_with(old_path, new_path)
    ...     new_file_exists = os.path.exists(new_path)
    ...     shutil.rmtree(temp_dir, ignore_errors=True)
    >>> success7 and len(failed_renames) == 0 and new_file_exists
    True
    """
    success7 = True
    failed_renames = []
    report = dict()
    total = len(proposed_changes)
    if actually_rename7:
        report["status"] = "commenced actual renaming"
        count = 0
        for old_path, new_path in proposed_changes.items():

            if replace_symlinks7 and os.path.islink(old_path):
                replace_symlink(old_path, new_path)
            else:
                os.rename(old_path, new_path)

            count += 1

            if (not os.path.exists(new_path)) or mock_error7:
                failed_renames.append((old_path, new_path))

            # print progress every 10 tsd items
            print(f"{count} of {total}") if count % 10000 == 0 else None

        report["items count"] = f"attempted to rename {count} items"

        if len(failed_renames) > 0:
            success7 = False
        report["failed_renames count"] = len(failed_renames)
    else:
        report["status"] = "haven't touched anything"

    return success7, failed_renames, report


def find_long_paths(directory, max_path_length):
    """
    >>> long_paths = find_long_paths("mock_data/some_files", 100)
    >>> # exclude paths with junk files
    >>> long_paths = [p for p in long_paths if os.path.basename(p) not in JUNK_FILES]
    >>> long_paths[0]
    'mock_data/some_files/pdfs with lengthy names/very long names of pdfs definietly worth renaming them for soure'
    >>> long_paths[1]
    'mock_data/some_files/pdfs with lengthy names/very long names of pdfs definietly worth renaming them for soure/some_very_lengthy_title_1-s2.0-S1116733756302733-main.pdf'
    """
    long_paths = []

    for root, dirs, files in os.walk(directory, followlinks=False):
        for name in files + dirs:
            path = os.path.join(root, name)
            if len(path) > max_path_length:
                long_paths.append(path)

    # sort alphabetically
    long_paths.sort()

    return long_paths


def create_logs_dir():
    """
    >>> logs_dir, success7 = create_logs_dir(); success7
    True
    >>> del_sucess7,_ = delete_dir(logs_dir); del_sucess7
    True
    """
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logs_dir = f"results/renaming_results_{current_time}"

    # os.makedirs(logs_dir)
    success7 = create_nested_dirs(logs_dir)

    return logs_dir, success7


class InvalidPathError(Exception):
    pass


def valid_path(path):
    if not os.path.exists(os.path.dirname(path)):
        msg = f"Parent directory of '{path}' does not exist"
        raise InvalidPathError(msg)
    return path


def get_file_creation_time(path, mock_operational_system=None):
    """
    Get the most appropriate creation/modification time for a file across different OS.

    :param path: Path to the file
    :param mock_operational_system: Optional parameter to mock the OS for testing
    :return: Timestamp of file creation/modification

    >>> import os
    >>> import time
    >>> import tempfile
    >>> # Create a temporary file
    >>> with tempfile.NamedTemporaryFile(delete=False) as temp_file:
    ...     temp_file_path = temp_file.name
    >>> # Get the current time
    >>> current_time = time.time()
    >>> # Get the file's creation time
    >>> file_time = get_file_creation_time(temp_file_path)
    >>> # Check if the times are within 1 second of each other
    >>> abs(current_time - file_time) < 1
    True

    >>> # Test with mocked Windows OS
    >>> windows_time = get_file_creation_time(temp_file_path, mock_operational_system='Windows')
    >>> abs(current_time - windows_time) < 1
    True

    >>> # Test with mocked Unix-like OS
    >>> unix_time = get_file_creation_time(temp_file_path, mock_operational_system='Linux')
    >>> abs(current_time - unix_time) < 1
    True
    >>> # Clean up
    >>> os.unlink(temp_file_path)
    """
    stat = os.stat(path)
    operational_system = mock_operational_system or platform.system()
    if operational_system == "Windows":
        return stat.st_ctime
    else:
        # On Unix-like systems, use the earliest of ctime and mtime
        return min(stat.st_ctime, stat.st_mtime)
