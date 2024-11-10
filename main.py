import os

from utils.case_insensitive_twin_files import handle_for_case_insensitive_twins
from utils.files import copy_directory, get_paths_for_renaming
from utils.files import do_actual_renaming, find_long_paths, create_logs_dir
from utils.languages import transliterate_russian_and_german, remove_bad_chars
from utils.name_shortening import shorten_name
from utils.prints_and_envs import parse_terminal_args, raise_error_if_collision
from utils.prints_and_envs import actual_or_dry_run_print, print_proposed_changes
from utils.prints_and_envs import length_warning
from utils.sanity_checks import sanity_check_user_inputs

"""
Principles:
- better to ruin a name than to ruin a file during a transfer between OS. Thus, if the name is too long, always shorten it enough.
- it attempts to preserve as much meaning of the filename as possible, especially of the names containing digits
- if there is a risk of data loss, better to raise an error and exit than to proceed

--------------------------------------------------------------------------------

TODO for future versions:
- if the total path is too long, rename dirs, starting from the deepest. Keep only 1 letter if necessary
- maybe add an optional flag: the end result must always contain only ascii letters and numbers
- before the actual renaming ask the user: "Do you want to proceed with the actual renaming? N files will be renamed."
- before the renaming, measure the number of files, dir size. After everythig is done, compare
- optional command-line arg for max_ext_len 
"""


def sanitize_name(name, max_length=255, just_preserve_left7=False):
    """
    The proper order of renaming:
    --- first, transliterate if necessary
    --- then, remove bad characters
    --- then, shorten

    >>> sanitize_name("some-html_files", max_length=9)
    'som_files'
    >>> sanitize_name("живой журнал_files", max_length=9)
    'zhv_files'
    >>> sample_path = "media/k/R/misc/aufg/Erweiterung/aufg/Intellekt/знание/hum/психпед/психо/психология памяти/The Woman Who Never Forgets - - science news articles online technology magazine articles The Woman Who Never Forgets"
    >>> names = sample_path.split("/")
    >>> clean_names = [sanitize_name(name, max_length=30) for name in names]
    >>> clean_path = "/".join(clean_names)
    >>> clean_path
    'media/k/R/misc/aufg/Erweiterung/aufg/Intellekt/znanije/hum/psikhpjed/psikho/psikhologija_pamjati/thWmnWhNvrFrgtsScncNwsrtcl_gts'

    >>> target_len = len("Screenshot 2024-07-06 at 20.56.55.png")
    >>> sanitize_name("Эй, жлоб! Где:туз? Прячь юных съёмщиц в шкаф.", max_length=target_len)
    'jZhlbGdjTzPrjchjhhnyhkhSqhjmxhcVShkaf'
    >>> sanitize_name("скриншот упоротый 2024-07-06 в 20.56.55 лол", 50)
    'skrinshot_uporotyhji_2024-07-06_v_20.56.55_lol'
    >>> sanitize_name("скриншот упоротый 2024-07-06 в 20.56.55 лол", 40)
    'skrnshotUporotyhji2024-07-06V20.56.55Lol'
    >>> sanitize_name("скриншот упоротый 2024-07-06 в 20.56.55 лол", 30)
    'skrnshtpr2024-07-06V20.56.55Ll'
    >>> sanitize_name("скриншот упоротый 2024-07-06 в 20.56.55 лол", 20)
    '2024-07-06V20.56.55l'
    >>> sanitize_name("скриншот упоротый 2024-07-06 в 20.56.55 лол", 10)
    '202407_655'
    >>> sanitize_name("__init__.cpython-38.pyc", 50)
    '__init__.cpython-38.pyc'
    >>> sanitize_name("GMT+7", 50) # is present in some python libraries
    'GMT+7'
    >>> sanitize_name(".~lock.canned_responses.csv#", 50)
    '.tilde_lock.canned_responses.csv_'
    >>> sanitize_name("", 50).startswith("unnamed_")
    True
    """

    name = remove_bad_chars(name)

    """Note: the translit must be done AFTER removing bad chars,
    because the func also handles unicode normalization.
    Othwerwise, it will fail to handle some umlauts etc. 
    """
    name = transliterate_russian_and_german(name)

    name = shorten_name(name, max_length, just_preserve_left7)

    return name


def sanitize_ext(ext, max_ext_len=4):
    """To handle cases like "Thumbs.db:encryptable"

    >>> sanitize_ext(".db:encryptable")
    '.db_e'
    >>> sanitize_ext(".d:b")
    '.d_b'
    >>> sanitize_ext(".хуй")
    '.khuj'
    >>> sanitize_ext(".html")
    '.html'
    >>> sanitize_ext(".txt")
    '.txt'
    """
    ext = ext.strip()
    if len(ext) == 0:
        res = ""
    else:
        # max_ext_len+1 because ext is ".txt", not just "txt"
        res = sanitize_name(ext, max_length=max_ext_len + 1, just_preserve_left7=True)
    return res


def write_proposed_changes_to_file(proposed_changes, logs_dir, kind):
    """
    >>> import os
    >>> from utils.files import delete_dir
    >>> mock_proposed_changes = {"/1/path_a.txt": "/1/new_path_a.txt", "/2/path_b.txt": "/2/new_path_b.txt"}
    >>> mock_logs_dir = "mock_logs_dir"
    >>> os.makedirs(mock_logs_dir, exist_ok=True)
    >>> _ = write_proposed_changes_to_file(mock_proposed_changes, mock_logs_dir, kind="files")
    >>> with open(os.path.join(mock_logs_dir, "proposed_files_changes.txt"), "r") as f:
    ...     content = f.read()
    >>> print(content)
    path_a.txt
    new_path_a.txt
    /1/new_path_a.txt
    <BLANKLINE>
    path_b.txt
    new_path_b.txt
    /2/new_path_b.txt
    <BLANKLINE>
    <BLANKLINE>
    >>> delete_dir(mock_logs_dir)
    (True, 'successfully deleted mock_logs_dir')
    """
    logs_path = os.path.join(logs_dir, f"proposed_{kind}_changes.txt")
    content = ""
    for old_path in sorted(proposed_changes.keys()):
        new_path = proposed_changes[old_path]
        content += os.path.basename(old_path) + "\n"
        content += os.path.basename(new_path) + "\n"
        content += new_path + "\n"
        content += "\n"

    with open(logs_path, "w") as f:
        f.write(content)

    return logs_path


def cond_proposed_change(old_path, new_path, proposed_changes):
    """
    >>> cond_proposed_change("path.txt", "path.txt", {})
    {}
    >>> cond_proposed_change("path.txt", "new_path.txt", {})
    {'path.txt': 'new_path.txt'}
    >>> with open("new_path.txt", "w") as f:
    ...     f.write("test")
    4
    >>> try:
    ...     cond_proposed_change("path.txt", "new_path.txt", {})
    ... except Exception as e:
    ...     print(e)
    Got a name collision: Proposed a new name: new_path.txt for the file: path.txt. But a file with the new name already exists at the same path. Exiting to prevent potential data loss.
    >>> os.remove("new_path.txt")
    """
    if old_path != new_path:
        if os.path.exists(new_path):
            raise_error_if_collision(old_path, new_path)
        proposed_changes[old_path] = new_path
    return proposed_changes


def build_new_path(name, ext, parent_dir, sanitize_len):
    """

    >>> build_new_path(name="Thumbs", ext=".db:encryptable", parent_dir="some_dir", sanitize_len=50)
    'some_dir/Thumbs.db_e'

    """
    sanitized_name = sanitize_name(name, sanitize_len)
    sanitized_ext = sanitize_ext(ext)
    new_name = sanitized_name + sanitized_ext
    new_path = os.path.join(parent_dir, new_name)
    return new_path


def propose_sanitisations(paths, kind, max_full_name_len, replace_symlinks7=False):
    """
    Proposes sanitized names for files or directories, handling symlinks if specified.

    >>> import os
    >>> from unittest.mock import patch
    >>> paths = [
    ...     "/path/to/some-very-long-filename.txt",
    ...     "/path/to/symlink",
    ...     "/path/to/directory with spaces",
    ... ]
    >>> with patch('os.path.islink') as mock_islink:
    ...     mock_islink.side_effect = [False, True, False]
    ...     proposed = propose_sanitisations(paths, "files", max_full_name_len=20, replace_symlinks7=True)
    >>> for old, new in proposed.items():
    ...     print(f"{os.path.basename(old)} -> {os.path.basename(new)}")
    some-very-long-filename.txt -> smVryLngFilename.txt
    symlink -> symlink.slk
    directory with spaces -> directoryWithSpaces

    >>> # Test for directories
    >>> paths = [
    ...     "/path/to/very long directory name",
    ...     "/path/to/another dir",
    ... ]
    >>> proposed = propose_sanitisations(paths, "dirs", max_full_name_len=15)
    >>> for old, new in proposed.items():
    ...     print(f"{os.path.basename(old)} -> {os.path.basename(new)}")
    very long directory name -> vryLngDrctryNme
    another dir -> another_dir
    """
    proposed_changes = dict()
    for old_path in paths:
        parent_dir = os.path.dirname(old_path)
        old_name = os.path.basename(old_path)

        if replace_symlinks7 and os.path.islink(old_path):
            name = old_name
            ext = ".slk"
            sanitize_len = max_full_name_len - len(ext)
        else:
            if kind == "files":
                name, ext = os.path.splitext(old_name)
                sanitize_len = max_full_name_len - len(ext)
            else:  # item_type == 'dirs'
                name = old_name
                ext = ""
                sanitize_len = max_full_name_len

        new_path = build_new_path(name, ext, parent_dir, sanitize_len)
        proposed_changes = cond_proposed_change(old_path, new_path, proposed_changes)

    return proposed_changes


def build_proposed_changes(paths, kind, max_full_name_len, replace_symlinks7=False):
    """
    >>> paths = []
    >>> paths.append("some files/some_very_lengthy_title_1-s2.0-S1116733756302733-main.pdf")
    >>> paths.append("Screenshot 2024-07-09 at 11.58.17.png")
    >>> paths.append("pics/без-перевода-смешные-картинки-Опять-о-своих-бабах-думает-Мемы-5285020.png")
    >>> proposed = build_proposed_changes(paths, kind="files", max_full_name_len=30)
    >>> for k, v in proposed.items():
    ...     print(k)
    ...     print(v)
    some files/some_very_lengthy_title_1-s2.0-S1116733756302733-main.pdf
    some files/sm1S2.0S1116733756302733Mn.pdf
    Screenshot 2024-07-09 at 11.58.17.png
    scrnsht2024-07-09t11.58.17.png
    pics/без-перевода-смешные-картинки-Опять-о-своих-бабах-думает-Мемы-5285020.png
    pics/bjzPjrjvdSmjshnyhjKrtn_020.png

    >>> paths = []
    >>> paths.append("pics")
    >>> paths.append("pdfs with lengthy names")
    >>> paths.append("pdfs with lengthy names/very long names of pdfs definietly worth renaming them for soure")
    >>> proposed = build_proposed_changes(paths, kind="dirs", max_full_name_len=30)
    >>> for k, v in proposed.items():
    ...     print(k)
    ...     print(v)
    pdfs with lengthy names
    pdfs_with_lengthy_names
    pdfs with lengthy names/very long names of pdfs definietly worth renaming them for soure
    pdfs with lengthy names/vryLngNmsfPdfsDfntlyWrthRn_rSr
    """
    proposed_changes = propose_sanitisations(
        paths, kind, max_full_name_len, replace_symlinks7
    )
    proposed_changes, _ = handle_for_case_insensitive_twins(paths, proposed_changes)

    return proposed_changes


def rename_items(
        paths,
        max_full_name_len,
        logs_dir,
        kind="files",
        actually_rename7=False,
        verbose7=False,
        replace_symlinks7=False,
):
    """
    Renames files or directories based on the given parameters.
    First generates the list of proposed renames, then optionally does the actual renaming.

    :param paths: List of paths to rename
    :param max_full_name_len: Maximum length for the full name
    :param kind: 'files' or 'dirs'
    :param actually_rename: Boolean to determine if renaming should actually occur
    :return: Dictionary of proposed changes

    >>> paths = []
    >>> paths.append("some files/some_very_lengthy_title_1-s2.0-S1116733756302733-main.pdf")
    >>> paths.append("Screenshot 2024-07-09 at 11.58.17.png")
    >>> paths.append("pics/без-перевода-смешные-картинки-Опять-о-своих-бабах-думает-Мемы-5285020.png")
    >>> logs_dir = "mock_logs_dir"
    >>> os.makedirs(logs_dir, exist_ok=True)
    >>> succes7, proposed_changes, log_path, report, _ = rename_items(paths, max_full_name_len=60, logs_dir=logs_dir, kind="files", actually_rename7=False)
    This is a dry run of renaming...
    >>> succes7
    True
    >>> log_path
    'mock_logs_dir/proposed_files_changes.txt'
    >>> with open(log_path, "r") as f:
    ...     content = f.read()
    >>> print(content)
    Screenshot 2024-07-09 at 11.58.17.png
    Screenshot_2024-07-09_at_11.58.17.png
    Screenshot_2024-07-09_at_11.58.17.png
    <BLANKLINE>
    без-перевода-смешные-картинки-Опять-о-своих-бабах-думает-Мемы-5285020.png
    bjzPjrjvdSmjshnyhjKrtnkpjtjhSvkhBbkhDumajetMjemyh5285020.png
    pics/bjzPjrjvdSmjshnyhjKrtnkpjtjhSvkhBbkhDumajetMjemyh5285020.png
    <BLANKLINE>
    <BLANKLINE>
    >>> report
    {'status': "haven't touched anything"}
    >>> from utils.files import delete_dir
    >>> delete_dir(logs_dir)
    (True, 'successfully deleted mock_logs_dir')
    """
    actual_or_dry_run_print(actually_rename7)

    proposed_changes = build_proposed_changes(
        paths, kind, max_full_name_len, replace_symlinks7=replace_symlinks7
    )
    print_proposed_changes(proposed_changes, verbose7)

    log_path = write_proposed_changes_to_file(proposed_changes, logs_dir, kind=kind)
    success7, failed_renames, rename_report = do_actual_renaming(
        proposed_changes, actually_rename7, replace_symlinks7=replace_symlinks7
    )

    return success7, proposed_changes, log_path, rename_report, failed_renames


def handle_long_paths(directory_path, max_path_len, logs_dir):
    """

    >>> import os
    >>> from utils.files import create_nested_dirs
    >>> from utils.files import delete_dir
    >>> files_path = "mock_data/some_files"
    >>> temp_log_dir = "temp_log_dir"
    >>> _ = create_nested_dirs(temp_log_dir)
    >>> long_paths_remain7, long_paths, log_path = handle_long_paths(files_path, max_path_len=30, logs_dir=temp_log_dir)
    Searching for long paths...
    <BLANKLINE>
    WARNING! Ther are still 9 full paths that longer than the specified max_path_len of 30 characters.
    >>> with open(log_path, "r") as f:
    ...     lines = f.readlines()
    >>> len(lines)
    9
    >>> lines[0].strip()
    'mock_data/some_files/0001-feat-all-support-multi-message-chats-refactor-improv.patch'
    >>> _, _ = delete_dir(temp_log_dir)

    >>> _ = create_nested_dirs(temp_log_dir)
    >>> long_paths_remain7, long_paths, log_path = handle_long_paths(files_path, max_path_len=256, logs_dir=temp_log_dir)
    Searching for long paths...
    <BLANKLINE>
    Good news! All paths are within the limits
    >>> _, _ = delete_dir(temp_log_dir)
    """

    print("Searching for long paths...")
    long_paths = find_long_paths(directory_path, max_path_len)
    if len(long_paths) > 0:
        print(
            f"\nWARNING! Ther are still {len(long_paths)} full paths that longer than the specified max_path_len of {max_path_len} characters."
        )
        long_paths_remain7 = True
    else:
        print("\nGood news! All paths are within the limits")
        long_paths_remain7 = False

    log_path = os.path.join(logs_dir, "long_paths.txt")
    # save the list to a file
    with open(log_path, "w") as f:
        for path in long_paths:
            f.write(path + "\n")

    return long_paths_remain7, long_paths, log_path


def make_renaming_preparations(
        directory_path, where_to_copy, in_place7, max_full_name_len
):
    """
    >>> from utils.files import delete_dir, copy_directory
    >>> target_dir = "mock_copied_dir"
    >>> _ = delete_dir(target_dir)
    >>> logs_dir, paths_by_kind, copy_success7 = make_renaming_preparations("mock_data/some_files", where_to_copy=target_dir, in_place7=False, max_full_name_len=100)
    The max_full_name_len you selected is passing the sanity check
    As per args, the renaming will be done in a copy. Copying...
    >>> logs_dir.startswith("results/renaming_results_")
    True
    >>> copy_success7
    True
    >>> paths_by_kind["dirs"][0]
    'mock_copied_dir/pdfs with lengthy names/very long names of pdfs definietly worth renaming them for soure'
    >>> paths_by_kind["dirs"][1]
    'mock_copied_dir/pdfs with lengthy names'
    >>> paths_by_kind["files"][0]
    'mock_copied_dir/pdfs with lengthy names/very long names of pdfs definietly worth renaming them for soure/some_very_lengthy_title_1-s2.0-S1116733756302733-main.pdf'
    >>> _ = delete_dir(target_dir)

    >>> target_dir = "mock_in_place_dir"
    >>> _ = copy_directory("mock_data/some_files", target_dir)
    >>> logs_dir, paths_by_kind, copy_success7 = make_renaming_preparations(target_dir, where_to_copy=None, in_place7=True, max_full_name_len=100)
    The max_full_name_len you selected is passing the sanity check
    >>> paths_by_kind["files"][0]
    'mock_in_place_dir/pdfs with lengthy names/very long names of pdfs definietly worth renaming them for soure/some_very_lengthy_title_1-s2.0-S1116733756302733-main.pdf'
    >>> _ = delete_dir(target_dir)
    """

    length_warning(max_full_name_len)

    copy_success7 = True

    if where_to_copy and not in_place7:
        print("As per args, the renaming will be done in a copy. Copying...")
        copy_success7 = copy_directory(directory_path, where_to_copy)
        directory_path = where_to_copy

    logs_dir, _ = create_logs_dir()
    paths_by_kind = get_paths_for_renaming(directory_path)

    return logs_dir, paths_by_kind, copy_success7


def rename_dir_with_files(
        directory_path,
        max_full_name_len=30,
        max_path_len=64,
        actually_rename7=False,
        in_place7=False,
        where_to_copy=None,
        replace_symlinks7=False,
        mock_rename_fail7=False,
        mock_copy_fail7=False,
):
    """
    E.g. if you want to migrate to Mac, set:
    max_full_name_len to 255.
    max_path_len to 1023.

    But if you want to write to CDs etc, set max_full_name_len to 30 chars.

    >>> from utils.files import delete_dir
    >>> target_dir = "mock_copied_dir"
    >>> total_success7, report = rename_dir_with_files(
    ...     "mock_data/some_files",
    ...     max_full_name_len=50,
    ...     max_path_len=256,
    ...     actually_rename7=True,
    ...     in_place7=False,
    ...     where_to_copy=target_dir
    ... ) # doctest: +NORMALIZE_WHITESPACE
    The max_full_name_len you selected is passing the sanity check
    As per args, the renaming will be done in a copy. Copying...
    Renaming files...
    Actually renaming...
    Renaming dirs...
    Actually renaming...
    <BLANKLINE>
    Renaming process completed.
    Searching for long paths...
    <BLANKLINE>
    Good news! All paths are within the limits
    >>> total_success7
    True
    >>> _ = delete_dir(target_dir)

    >>> total_success7, report = rename_dir_with_files(
    ...     "mock_data/some_files",
    ...     max_full_name_len=50,
    ...     max_path_len=256,
    ...     actually_rename7=True,
    ...     in_place7=False,
    ...     where_to_copy=target_dir,
    ...     mock_rename_fail7=True
    ... ) # doctest: +NORMALIZE_WHITESPACE
    The max_full_name_len you selected is passing the sanity check
    As per args, the renaming will be done in a copy. Copying...
    Renaming files...
    Actually renaming...
    Renaming dirs...
    Actually renaming...
    Some renames failed: {'files': True, 'dirs': True}
    <BLANKLINE>
    Renaming process completed.
    Searching for long paths...
    <BLANKLINE>
    Good news! All paths are within the limits
    >>> total_success7
    False
    >>> _ = delete_dir(target_dir)

    >>> total_success7, report = rename_dir_with_files(
    ...     "mock_data/some_files",
    ...     max_full_name_len=50,
    ...     max_path_len=256,
    ...     actually_rename7=True,
    ...     in_place7=False,
    ...     where_to_copy=target_dir,
    ...     mock_copy_fail7=True
    ... ) # doctest: +NORMALIZE_WHITESPACE
    The max_full_name_len you selected is passing the sanity check
    As per args, the renaming will be done in a copy. Copying...
    Copying failed. No renaming was done to avoid data loss.
    >>> total_success7
    False
    >>> _ = delete_dir(target_dir)

    """

    args_to_check = {
        "directory_path": directory_path,
        "where_to_copy": where_to_copy,
        "max_full_name_len": max_full_name_len,
        "max_path_len": max_path_len,
        "actually_rename7": actually_rename7,
        "in_place7": in_place7,
        "replace_symlinks7": replace_symlinks7,
    }
    sanity_check_user_inputs(**args_to_check)

    report = dict()
    total_success7 = False

    logs_dir, paths_by_kind, copy_success7 = make_renaming_preparations(
        directory_path, where_to_copy, in_place7, max_full_name_len
    )
    report["copy_success7"] = copy_success7

    if copy_success7 and not mock_copy_fail7:
        kinds = ["files", "dirs"]
        successes_by_kind = dict()
        for kind in kinds:
            print(f"Renaming {kind}...")
            (
                rename_success7,
                proposed_changes,
                log_file_path,
                items_rename_report,
                failed_renames,
            ) = rename_items(
                paths_by_kind[kind],
                max_full_name_len,
                logs_dir,
                kind=kind,
                actually_rename7=actually_rename7,
                replace_symlinks7=replace_symlinks7,
                verbose7=False,
            )
            successes_by_kind[kind] = rename_success7
            report[f"{kind} renaming successful?"] = rename_success7
            report[f"{kind} renaming report"] = items_rename_report
            report[f"{kind} failed renames"] = failed_renames
            report[f"{kind} log file path"] = log_file_path
            # report[f"{kind} proposed changes"] = proposed_changes # don't enable this for dirs with millions of files

        if all(successes_by_kind.values()) and not mock_rename_fail7:
            total_success7 = True
        else:
            print(f"Some renames failed: {successes_by_kind}")

        print("\nRenaming process completed. ")

        long_paths_remain7, _, long_log_path = handle_long_paths(
            directory_path, max_path_len, logs_dir
        )
        report["long_paths_remain7"] = long_paths_remain7
        report["long_paths_log_path"] = long_log_path
    else:
        msg = "Copying failed. No renaming was done to avoid data loss."
        print(msg)
        report["not renaming"] = msg

    return total_success7, report


def execute(mock_args=None):
    """
    Execute the main functionality of the script.

    This function parses command-line arguments, calls rename_dir_with_files
    with the parsed arguments, and returns the results.

    Returns:
        tuple: A tuple containing (args, total_success7, report)

    >>> import sys
    >>> from utils.files import delete_dir, create_nested_dirs, valid_path
    >>> source_dir = "mock_data/some_files"
    >>> target_dir = "mock_data/mock_copied_dir5"
    >>> create_nested_dirs(source_dir)
    True

    >>> original_argv = sys.argv.copy()
    >>> sys.argv = ['main.py', '--path', source_dir, '--where-to-copy', target_dir, '--max-name-len', '50', '--max-path-len', '256']
    >>> args, total_success7, report = execute() # doctest: +NORMALIZE_WHITESPACE
    The max_full_name_len you selected is passing the sanity check
    As per args, the renaming will be done in a copy. Copying...
    Renaming files...
    This is a dry run of renaming...
    Renaming dirs...
    This is a dry run of renaming...
    <BLANKLINE>
    Renaming process completed.
    Searching for long paths...
    <BLANKLINE>
    Good news! All paths are within the limits

    >>> args.path == source_dir
    True
    >>> args.rename
    False
    >>> args.where_to_copy == target_dir
    True
    >>> args.max_name_len
    50
    >>> args.max_path_len
    256
    >>> total_success7
    True
    >>> 'copy_success7' in report
    True
    >>> delete_dir(target_dir)
    (True, 'successfully deleted mock_data/mock_copied_dir5')

    >>> sys.argv = original_argv  # Restore original sys.argv
    """

    args = parse_terminal_args() if mock_args is None else mock_args

    total_success7, report = rename_dir_with_files(
        args.path,
        actually_rename7=args.rename,
        in_place7=args.in_place,
        where_to_copy=args.where_to_copy,
        replace_symlinks7=args.symlinks,
        max_full_name_len=args.max_name_len,
        max_path_len=args.max_path_len,
    )

    return args, total_success7, report


if __name__ == "__main__":  # pragma: no cover
    execute()
