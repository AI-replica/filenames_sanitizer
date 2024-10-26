import os
import argparse

from utils.files import valid_path


def raise_error_if_collision(old_path, new_path):
    """If such a path already exists, raise an error

    >>> try:
    ...     raise_error_if_collision("/old/path.txt", "/existing/path.txt")
    ... except FileExistsError as e:
    ...     print(str(e).startswith("Got a name collision:"))
    True

    """

    msg = f"Got a name collision: "
    msg += f"Proposed a new name: {new_path} for the file: {old_path}. "
    msg += f"But a file with the new name already exists at the same path. "
    msg += "Exiting to prevent potential data loss."
    raise FileExistsError(msg)


def actual_or_dry_run_print(actually_rename7):
    """

    >>> actual_or_dry_run_print(True)
    Actually renaming...
    >>> actual_or_dry_run_print(False)
    This is a dry run of renaming...
    """
    if actually_rename7:
        print("Actually renaming...")
    else:
        print("This is a dry run of renaming...")


def print_proposed_changes(proposed_changes, verbose7=False):
    """

    >>> mock_proposed_changes = {"/old/path.txt": "/new/path.txt", "/old/path2.txt": "/new/path2.txt"}
    >>> print_proposed_changes(mock_proposed_changes, verbose7=True)
    Proposed:
    path.txt
    path.txt
    --------------------------------
    Proposed:
    path2.txt
    path2.txt
    --------------------------------
    """
    if verbose7:
        for old_path, new_path in proposed_changes.items():
            print("Proposed:")
            print(f"{os.path.basename(old_path)}")
            print(f"{os.path.basename(new_path)}")
            print("--------------------------------")


def length_warning(max_full_name_len):
    """

    >>> length_warning(100)
    The max_full_name_len you selected is passing the sanity check

    >>> import io
    >>> import sys
    >>> def mock_input(prompt):
    ...     print(prompt)
    ...     return 'y'
    >>> sys.stdin = io.StringIO('y\\n')
    >>> length_warning(20)
    <BLANKLINE>
                The max_full_name_len you selected is shorter than the practical length (37).
                For example, this one will have to be shortened if you proceed: 'Screenshot 2024-07-06 at 20.56.55.png'.
                Do you want to continue? (y/n)
    <BLANKLINE>

    >>> sys.stdin = io.StringIO('n\\n')
    >>> try:
    ...     length_warning(20)
    ... except ValueError as e:
    ...     print(str(e))
    <BLANKLINE>
                The max_full_name_len you selected is shorter than the practical length (37).
                For example, this one will have to be shortened if you proceed: 'Screenshot 2024-07-06 at 20.56.55.png'.
                Do you want to continue? (y/n)
                Exiting...
    Exiting...
    """

    screenshot_name = "Screenshot 2024-07-06 at 20.56.55.png"
    practical_max_len = len(screenshot_name)
    if max_full_name_len < practical_max_len:
        warning_text = f"""
            The max_full_name_len you selected is shorter than the practical length ({practical_max_len}).
            For example, this one will have to be shortened if you proceed: '{screenshot_name}'.
            Do you want to continue? (y/n)
            """
        user_input = input(warning_text)
        if user_input.lower() != "y":
            print("Exiting...")
            # return
            # exit script
            raise ValueError("Exiting...")
    else:
        print("The max_full_name_len you selected is passing the sanity check")


def parse_terminal_args():
    """
    TODO: move it from here

    Parse command-line arguments for renaming directory with files.

    >>> from unittest.mock import patch
    >>> from utils.files import InvalidPathError
    >>> import sys

    # Test case 1: Valid input with --rename and --in-place flags
    >>> with patch('os.path.exists', return_value=True), patch.object(sys, 'argv', ['script.py', '--path', '/path/to/dir', '--rename', '--in-place', '--max-name-len', '50', '--max-path-len', '256']):
    ...     args = parse_terminal_args()
    ...     print(args.path, args.rename, args.in_place, args.where_to_copy)
    /path/to/dir True True None

    # Test case 2: Valid input with --where-to-copy flag
    >>> with patch('os.path.exists', return_value=True), patch.object(sys, 'argv', ['script.py', '--path', '/path/to/dir', '--where-to-copy', '/new/path', '--max-name-len', '50', '--max-path-len', '256']):
    ...     args = parse_terminal_args()
    ...     print(args.path, args.rename, args.in_place, args.where_to_copy)
    /path/to/dir False False /new/path

    # Test case 3: Valid input with only path specified
    >>> with patch('os.path.exists', return_value=True), patch.object(sys, 'argv', ['script.py', '--path', '/path/to/dir', '--max-name-len', '50', '--max-path-len', '256']):
    ...     args = parse_terminal_args()
    ...     print(args.path, args.rename, args.in_place, args.where_to_copy)
    /path/to/dir False False None

    # Test case 4: Invalid input - both --in-place and --where-to-copy specified
    >>> with patch('os.path.exists', return_value=True), patch.object(sys, 'argv', ['script.py', '--path', '/path/to/dir', '--in-place', '--where-to-copy', '/new/path', '--max-name-len', '50', '--max-path-len', '256']):
    ...     try:
    ...         parse_terminal_args()
    ...     except SystemExit:
    ...         print("SystemExit raised as expected")
    SystemExit raised as expected

    # Test case 5: Invalid input - --rename flag without specifying --in-place or --where-to-copy
    >>> with patch('os.path.exists', return_value=True), patch.object(sys, 'argv', ['script.py', '--path', '/path/to/dir', '--rename', '--max-name-len', '50', '--max-path-len', '256']):
    ...     try:
    ...         parse_terminal_args()
    ...     except SystemExit:
    ...         print("SystemExit raised as expected")
    SystemExit raised as expected

    # Test case 6: Invalid path (parent directory doesn't exist)
    >>> with patch('os.path.exists', return_value=False), patch.object(sys, 'argv', ['script.py', '--path', '/invalid/path', '--max-name-len', '50', '--max-path-len', '256']):
    ...     try:
    ...         parse_terminal_args()
    ...     except InvalidPathError as e:
    ...         print(f"InvalidPathError raised: {str(e)}")
    InvalidPathError raised: Parent directory of '/invalid/path' does not exist
    """

    parser = argparse.ArgumentParser(description="Rename directory with files.")
    parser.add_argument(
        "--path", type=valid_path, required=True, help="Path to the directory"
    )
    parser.add_argument("--rename", action="store_true", help="Actually rename")
    parser.add_argument("--in-place", action="store_true", help="Rename in-place")
    parser.add_argument("--where-to-copy", type=valid_path, help="Expects a path")
    parser.add_argument("--symlinks", action="store_true", help="Replace symlinks")
    parser.add_argument(
        "--max-name-len", type=int, required=True, help="Max full name length"
    )
    parser.add_argument(
        "--max-path-len", type=int, required=True, help="Max path length"
    )
    args = parser.parse_args()

    if args.in_place and args.where_to_copy:
        parser.error("Cannot use both --in-place and --where-to-copy")
    elif args.rename and not (args.in_place or args.where_to_copy):
        parser.error(
            "Must specify either --in-place or --where-to-copy when using --rename"
        )
    return args
