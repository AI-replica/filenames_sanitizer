[![Coverage](coverage.svg)](https://coverage.readthedocs.io)

You want to move a lot of files to a different OS, but the OS can't handle some charecters in the file names?

The new OS silently discards some of your old files because their names contain ":"? (Hello, MacOS!)

You can't back up the files to a Blu-ray, because some file names are too long?

The news file system doesn't support symlinks?

If you answered yes to any of these questions, this is the tool for you!

# Features

- Sanitizes file and directory names:
  - Removes many kinds of problematic characters
  - Handles Unicode characters, including multi-byte UTF-8 encodings
  - Shortens names according to user-defined parameters, while preserving as much meaning as possible
  - Transliterates Russian and German characters to Latin equivalents
- Supports both in-place renaming and renaming in a copy of the directory. The copy option is the default, for additional safety.
- Dry-run mode by default
- Preserves file extensions during renaming
- Generates detailed logs of proposed changes
- Handles case-insensitive file systems to prevent collisions. For example, if the same dir contains AAA.txt and aaa.txt, they will be renamed to tw0_AAA.txt and tw1_aaa.txt, to prevent data loss if you move them to a case-insensitive file system.
- Optionally, converts symlinks to txt files (because not all file systems support symlinks)

# Sample renaming results:

max_full_name_len = 55:
```
Asimov, Isaac & Silverberg, Robert - The Positronic Man - 1992.txt ->
asimovIsaacAndSilverbergRobertThePositronicMan1992.txt

Дни затмения [по мотивам повести «За миллиард лет до конца света»].txt ->
dnZtmjnjPMotivamPovjestiZaMilliardLjetDoKoncaSvjeta.txt
```

max_full_name_len = 30:
```
Screenshot 2024-09-23 at 15.35.27.png ->
scrnsht2024-09-23t15.35.27.png
```

The algoritm uses some simple heuristics to shorten the name while preserving as much info in the name as possible.

An illustration of how the result changes if you make the max_full_name_len smaller:

```
original name: 
Asimov, Isaac & Silverberg, Robert - The Positronic Man - 1992.txt

100: # no shortening in this case, only replacement of questionable characters
Asimov_Isaac_and_Silverberg_Robert_The_Positronic_Man_1992.txt

60: # removed underscores 
asimovIsaacAndSilverbergRobertThePositronicMan1992.txt

40: # removed some vowels 
smvscndSlvrbrgRbrtThPstronicMan1992.txt

37: # removed all vowels 
smvscndSlvrbrgRbrtThPstrncMn1992.txt

20: # removed some characters from the middle
smvscndSlvr_992.txt

```

# How to use

- clone the repo
- run the script as described below
- (optionally) install requirements with ```pip install -r requirements.txt``` . The script itself doesn't have any. This is only useful if you want to run doctests.


## Usage examples:

Example #1: A dry run. Nothing will change, except the reports will be created in the script's dir, showing the proposed changes. 
The reports will be in a new dir named ```results_<timestamp>```.
```
python3 main.py --max-name-len 7 --max-path-len 45 --path /path/to/dir
```

Example #2: An actual renaming, but in a copy of the dir, for additional safety. 
If you actually want to rename stuff, this is the recommended usage.
```
python3 main.py --max-name-len 7 --max-path-len 45 --rename --path /path/to/dir --where-to-copy /path/to/new_dir_to_be_created
```

Example #3: An actual renaming, in the **original dir**. This is a danger zone. Back up the dir before doing this.
```
python3 main.py --max-name-len 7 --max-path-len 45 --rename --in-place --path /path/to/dir
```


## Arguments:

```--path``` <path/do/dir>: (required) path to the directory with the stuff you want to rename

```--max-name-len``` (int, required): maximum length of the full name of the file.

```--max-path-len``` (int, required): maximum length of the path of the file.

```--rename``` : if stated, it will actually rename stuff (not just dry run)

```--in-place``` : if stated, it will rename stuff in the original directory. Otherwise it will copy stuff to new location and rename there.

```--where-to-copy``` (path/do/new_dir): where to copy the stuff.

```--symlinks``` : if stated, it will replace symlinks with txt files that contain the symlink target.

## Sanity checks

It doesn't make sense to state both ```--in-place``` and ```--where-to-copy```. 

If you stated ```--rename```, you must state either ```--in-place``` or ```--where-to-copy```. 

# Notes:

We recommend preserving the renaming reports, for the cases where you'll want to restore an original name.

We also recommend to do a dry run first, and check the reports. Only after that, if you're happy with proposed renames, do the actual run. 

The script uses an unique **reversible** transliteration of Russian. 
If a name is not otherwise shortened, it's possible to get back the exact same original Russian letters, because of our special mapping of characters. 
A sample transliteration:
```
Волны гасят ветер.txt ->
Volnyh_gasjat_vjetjer.txt
```

During checks, the script ignores junk system files like ".DS_Store", "Thumbs.db".

# Limitations

Currently, we don't fix the cases where the total path lengh is too long for the file system. The cases are saved to a report though.

If you have .html stuff with the linked images (e.g. in a "_files" dir), 
be warned that renaming the dir may make the html to work not as expected. Same for other stuff with hardcoded pathes, including some software. That's one of the reasons we recommend preserving the renaming reports, for the cases where you'll want to restore an original name.

The script doesn't follow symlinks.

# Some common file system limits:

| Filesystem | Max path Len     | Max name len      | <- in chars** |
|------------|------------------|-------------------|---------------|
| Btrfs      | No limit defined | 255 bytes         | 63            |
| ext2       | No limit defined | 255 bytes         | 63            |
| ext3       | No limit defined | 255 bytes         | 63            |
| ext4 (🟠🐧) | No limit defined | 255 bytes         | 63            |
| XFS        | No limit defined | 255 bytes         | 63            |
| ZFS        | No limit defined | 255 bytes         | 63            |
| APFS (🍎)  | 1023 UTF-8 chars | 255 UTF-8 chars   | 255           |
| exFAT      | 32760 UTF-8 chars| 255 UTF-16 chars  | 255           |
| NTFS (🪟)  | 32767 UTF-8 chars| 255 chars         | 255           |
| ReFS       | 32767 UTF-8 chars| 255 bytes         | 63            |
| UDF        | 1023 bytes       | 255 bytes         | 63            |
| ISO9660(💿)| 180 - 222 bytes  | 30 - 255 bytes    | 7             |
| FAT32      | 32760 UTF-8 chars| 8ch name, 3 ext*** | 11            |

** - worst case (not considering max path len)


*** - 255 UCS-2 code units with VFAT LFNs


E.g. if you want to migrate to Mac, set:
 max_full_name_len to 255.
 max_path_len to 1023.

Note: In UTF-8, a single Unicode char can take up to 4 bytes.
Thus, 255 bytes can be as little as 63 characters, if all of them are 4-byte chars.
