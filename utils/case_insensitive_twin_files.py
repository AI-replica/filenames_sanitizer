import os
from utils.files import get_file_creation_time
import tempfile
import time


def identify_twins(paths, proposed_changes):
    """
    
    >>> paths = ['/a/h::.7z', '/a/h:.7z']
    >>> proposed_changes = {'/a/h::.7z': '/a/h_.7z', '/a/h:.7z': '/a/h_.7z'}
    >>> twins_families = identify_twins(paths, proposed_changes)
    >>> twins_families
    {'/a/h::.7z': [{'filesystem_path': '/a/h::.7z', 'proposed_path': '/a/h_.7z'}, {'filesystem_path': '/a/h:.7z', 'proposed_path': '/a/h_.7z'}]}
    """
    # Build combined_paths
    combined_paths = []
    for path in paths:
        combined_paths.append({
            'filesystem_path': path,
            'proposed_path': proposed_changes.get(path, path)
        })

    twins_families = {}
    path_dict = {}

    # Check for twins in combined_paths
    for path_info in combined_paths:
        lower_path = path_info['proposed_path'].lower()

        if lower_path in path_dict:
            # We found a twin
            existing_path_info = path_dict[lower_path]
            existing_path = existing_path_info['filesystem_path']
            # Use the existing path's filesystem and proposed paths
            if existing_path in twins_families:
                twins_families[existing_path].append(path_info)
            else:
                twins_families[existing_path] = [
                    existing_path_info,
                    path_info
                ]
        else:
            # Store the entire path_info, not just the filesystem_path
            path_dict[lower_path] = path_info

    return twins_families


def apply_creation_times_to_twins(twins_families, creation_times_available7=True):
    """
    Adds creation/modification time to each twin in the twins_families dictionary.
    If creation times are not available, assigns fake times based on alphabetical order.

    :param twins_families: Dictionary of twin families
    :param creation_times_available7: Boolean indicating if real creation times are available
    :return: Updated twins_families dictionary

    >>> twins = {
    ...     '/path/to/file.txt': [
    ...         {'filesystem_path': '/path/to/file.txt', 'proposed_path': '/path/to/file.txt'},
    ...         {'filesystem_path': '/path/to/FILE.TXT', 'proposed_path': '/path/to/FILE.TXT'},
    ...         {'filesystem_path': '/path/to/File.txt', 'proposed_path': '/path/to/File.txt'}
    ...     ]
    ... }
    >>> updated = apply_creation_times_to_twins(twins, creation_times_available7=False)
    >>> [twin['ctime'] for twin in updated['/path/to/file.txt']]
    [1, 2, 3]
    
    # Test with empty twins_families
    >>> updated = apply_creation_times_to_twins({})
    >>> len(updated)
    0

    # Test with real creation times
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     file1_path = os.path.join(tmpdir, 'file1.txt')
    ...     file2_path = os.path.join(tmpdir, 'file2.txt')
    ...     
    ...     # Create two files with different creation times
    ...     with open(file1_path, 'w') as f:
    ...         f.write('File 1 content')
    ...     time.sleep(1)  # Ensure different creation times
    ...     with open(file2_path, 'w') as f:
    ...         f.write('File 2 content')
    ...     
    ...     twins = {
    ...         file1_path: [
    ...             {'filesystem_path': file1_path, 'proposed_path': file1_path},
    ...             {'filesystem_path': file2_path, 'proposed_path': file2_path}
    ...         ]
    ...     }
    ...     
    ...     updated = apply_creation_times_to_twins(twins)
    ...     
    ...     # Check if creation times are different and in the correct order
    ...     ctimes = [twin['ctime'] for twin in updated[file1_path]]
    ...     assert ctimes[0] < ctimes[1], f"Expected {ctimes[0]} < {ctimes[1]}"
    ...     print("Creation times are different and in the correct order")
    14
    14
    Creation times are different and in the correct order
    """
    for twins in twins_families.values():
        if creation_times_available7:
            for twin in twins:
                if 'ctime' not in twin:
                    twin['ctime'] = get_file_creation_time(twin['filesystem_path'])
        else:
            # Sort twins alphabetically by filesystem_path
            sorted_twins = sorted(twins, key=lambda x: x['filesystem_path'].lower())
            # Assign fake creation times (1, 2, 3, etc.) based on alphabetical order
            for index, twin in enumerate(sorted_twins, start=1):
                twin['ctime'] = index

    return twins_families


def fix_twins(proposed_changes, twins_families, mock_updated_families=None, creation_times_available7=True):
    """
    Fixes twin files by adding prefixes based on creation time.

    :param proposed_changes: Dictionary of proposed changes {old_path: new_path}
    :param twins_families: Dictionary of twin families
    :return: Updated proposed_changes dictionary

    >>> import os
    >>> # Mock data for testing
    >>> mock_updated_families = {
    ...     '/path/to/file.txt': [
    ...         {'filesystem_path': '/path/to/file.txt', 'proposed_path': '/path/to/file.txt', 'ctime': 3000},
    ...         {'filesystem_path': '/path/to/FILE.TXT', 'proposed_path': '/path/to/FILE.TXT', 'ctime': 1000},
    ...         {'filesystem_path': '/path/to/File.txt', 'proposed_path': '/path/to/File.txt', 'ctime': 2000}
    ...     ],
    ...     '/another/path/doc.pdf': [
    ...         {'filesystem_path': '/another/path/doc.pdf', 'proposed_path': '/another/path/doc.pdf', 'ctime': 4000},
    ...         {'filesystem_path': '/another/path/DOC.PDF', 'proposed_path': '/another/path/DOC.PDF', 'ctime': 5000}
    ...     ]
    ... }
    >>> proposed_changes = {
    ...     '/path/to/FILE.TXT': '/path/to/new_file.txt',
    ...     '/another/path/DOC.PDF': '/another/path/new_doc.pdf'
    ... }
    >>> updated_changes = fix_twins(proposed_changes, {}, mock_updated_families)
    >>> for old_path, new_path in sorted(updated_changes.items()):
    ...     print(f"{old_path} -> {new_path}")
    /another/path/DOC.PDF -> /another/path/tw1_DOC.PDF
    /another/path/doc.pdf -> /another/path/tw0_doc.pdf
    /path/to/FILE.TXT -> /path/to/tw0_FILE.TXT
    /path/to/File.txt -> /path/to/tw1_File.txt
    /path/to/file.txt -> /path/to/tw2_file.txt

    >>> # Test with empty proposed_changes
    >>> empty_proposed_changes = {}
    >>> updated_empty_changes = fix_twins(empty_proposed_changes, {}, mock_updated_families)
    >>> for old_path, new_path in sorted(updated_empty_changes.items()):
    ...     print(f"{old_path} -> {new_path}")
    /another/path/DOC.PDF -> /another/path/tw1_DOC.PDF
    /another/path/doc.pdf -> /another/path/tw0_doc.pdf
    /path/to/FILE.TXT -> /path/to/tw0_FILE.TXT
    /path/to/File.txt -> /path/to/tw1_File.txt
    /path/to/file.txt -> /path/to/tw2_file.txt

    >>> # Test with empty twins_families
    >>> updated_no_twins = fix_twins(proposed_changes, {}, {})
    >>> updated_no_twins == proposed_changes
    True
    
    # Test for "h:" and "h::" in the same dir (encountered in the wild)
    >>> proposed_changes = {'/a/h::.7z': '/a/h_.7z', '/a/h:.7z': '/a/h_.7z'}
    >>> twins_families =  {'/a/h::.7z': [{'filesystem_path': '/a/h::.7z', 'proposed_path': '/a/h_.7z'}, {'filesystem_path': '/a/h:.7z', 'proposed_path': '/a/h_.7z'}]}
    >>> updated_changes = fix_twins(proposed_changes, twins_families, creation_times_available7=False)
    >>> for old_path, new_path in sorted(updated_changes.items()):
    ...     print(f"{old_path} -> {new_path}")
    /a/h:.7z -> /a/tw0_h_.7z
    /a/h::.7z -> /a/tw1_h_.7z
    """
    twins_families = apply_creation_times_to_twins(twins_families, creation_times_available7)
    twins_families = mock_updated_families or twins_families

    for existing_path, twins in twins_families.items():
        # Sort twins by creation time
        sorted_twins = sorted(twins, key=lambda x: x['ctime'])

        for index, twin in enumerate(sorted_twins):
            old_path = twin['filesystem_path']
            current_proposed_path = twin['proposed_path']

            # Generate new name with prefix
            dir_name = os.path.dirname(current_proposed_path)
            file_name = os.path.basename(current_proposed_path)
            new_name = f"tw{index}_{file_name}"
            new_path = os.path.join(dir_name, new_name)

            # Update proposed_changes
            if old_path in proposed_changes:
                proposed_changes[old_path] = new_path
            else:
                proposed_changes[old_path] = new_path

    return proposed_changes


def handle_for_case_insensitive_twins(paths, proposed_changes, creation_times_available7=True):
    """
    Checks for case-insensitive duplicates among existing paths and proposed changes.

    :param paths: List of all file or directory paths
    :param proposed_changes: Dictionary of proposed changes {old_path: new_path}
    :return: Tuple of (proposed_changes, dict of twins families)

    dict of twins families has the a structure like this:
    {
        '/path/to/existing_file.txt': [
            {'filesystem_path': '/path/to/existing_file.txt', 'proposed_path': '/path/to/NewFile.txt'},
            ...
        ],
        ...
    }

    # The proposed change has already removed a twin, so no twins left in the dir
    >>> paths = ['/path/to/File.txt', '/path/to/file.txt', '/path/to/OTHER.txt']
    >>> proposed_changes = {'/path/to/File.txt': '/path/to/NewFile.txt'}
    >>> _, twins = handle_for_case_insensitive_twins(paths, proposed_changes, creation_times_available7=False)
    >>> len(twins)
    0

    # The files in different dirs, and thus are not twins
    >>> paths = ['/path/A/file.txt', '/path/B/FILE.TXT', '/path/C/File.txt']
    >>> proposed_changes = {}
    >>> _, twins = handle_for_case_insensitive_twins(paths, proposed_changes, creation_times_available7=False)
    >>> len(twins)
    0

    # The files have different names after being lowered, so no twins
    >>> paths = ['/unique/path1.txt', '/unique/PATH2.txt', '/unique/Path3.txt']
    >>> proposed_changes = {}
    >>> _, twins = handle_for_case_insensitive_twins(paths, proposed_changes, creation_times_available7=False)
    >>> len(twins)
    0

    # The dir has only one file, so no twins
    >>> paths = ['/path/file.txt']
    >>> proposed_changes = {'/path/file.txt': '/path/FILE.TXT'}
    >>> _, twins = handle_for_case_insensitive_twins(paths, proposed_changes, creation_times_available7=False)
    >>> len(twins)
    0

    # found twins
    >>> paths = ['/same/path/file1.txt', '/same/path/FILE1.TXT', '/same/path/File2.txt']
    >>> proposed_changes = {}
    >>> proposed_changes, twins = handle_for_case_insensitive_twins(paths, proposed_changes, creation_times_available7=False)
    >>> proposed_changes
    {'/same/path/file1.txt': '/same/path/tw0_file1.txt', '/same/path/FILE1.TXT': '/same/path/tw1_FILE1.TXT'}

    # Proposed changes that create new twins
    >>> paths = ['/path/file1.txt', '/path/FILE1.txt', '/path/file2.txt', '/path/mega_long_name_for_file2.txt']
    >>> proposed_changes = {'/path/mega_long_name_for_file2.txt': '/path/file2.txt'}
    >>> proposed_changes, twins = handle_for_case_insensitive_twins(paths, proposed_changes, creation_times_available7=False)
    >>> proposed_changes
    {'/path/mega_long_name_for_file2.txt': '/path/tw1_file2.txt', '/path/file1.txt': '/path/tw0_file1.txt', '/path/FILE1.txt': '/path/tw1_FILE1.txt', '/path/file2.txt': '/path/tw0_file2.txt'}

    # Empty input (empty paths and proposed_changes)
    >>> paths = []
    >>> proposed_changes = {}
    >>> _, twins = handle_for_case_insensitive_twins(paths, proposed_changes)
    >>> len(twins)
    0

    # Test case for appending to an existing twins family
    >>> paths = ['/path/file1.txt', '/path/FILE1.txt', '/path/File1.txt', '/path/file2.txt']
    >>> proposed_changes = {}
    >>> _, twins = handle_for_case_insensitive_twins(paths, proposed_changes, creation_times_available7=False)
    >>> sorted([item['filesystem_path'] for item in twins['/path/file1.txt']])
    ['/path/FILE1.txt', '/path/File1.txt', '/path/file1.txt']
    """

    twins_families = identify_twins(paths, proposed_changes)
    proposed_changes = fix_twins(proposed_changes, twins_families, creation_times_available7=creation_times_available7)

    return proposed_changes, twins_families