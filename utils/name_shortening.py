from utils.languages import (
    HTML_DIR_ENDINGS,
    find_non_digit_between_digits,
    proportion_of_digits_in_name,
    to_camel_case,
)


def shrink_the_middle(
    name,
    max_length,
    keep_start=3,
    keep_end=3,
    separator="_",
    fallback_to_original7=False,
):
    """
    Shorten a name to a maximum allowed length by removing characters from the middle.

    >>> shrink_the_middle("sun", 10)
    'sun'
    >>> shrink_the_middle("hello-world", 10)
    'hello-_rld'
    >>> shrink_the_middle("lenthy-name-with-ind-5", 10)
    'lenthy_d-5'
    >>> shrink_the_middle("lenthy-name-with-ind-5", 8)
    'lent_d-5'
    >>> shrink_the_middle("lenthy-name-with-ind-5", 7)
    'len_d-5'
    >>> shrink_the_middle("some-html_files", 9)
    'som_files'
    >>> shrink_the_middle("some-lengthy-string", 3)
    'ing'
    >>> shrink_the_middle("short", keep_start=10, keep_end=10, separator="", max_length=3)
    'ort'
    >>> shrink_the_middle("short", keep_start=10, keep_end=10, separator="", max_length=3, fallback_to_original7=True)
    'short'
    >>> shrink_the_middle("Asimov, Isaac - The Early Asimov - Volume 03 - 1972.html_files", 40)
    'Asimov, Isaac - The Early Asi.html_files'
    """
    if len(name) <= max_length:
        res = name

    else:

        """For properly handling dirs of saved html files: "_files", " Files", ".files", "-files" """
        for ending in HTML_DIR_ENDINGS:
            if name.endswith(ending):
                keep_end = len(ending)
                separator = ""  # because the ending already contains a separator
                break

        middle_max_length = max_length - keep_start - keep_end - len(separator)

        if middle_max_length < 0:  # in such cases prioritize the end
            # raise ValueError("keep_start and keep_end are too large for the max_length")
            keep_start = 0
            middle_max_length = max_length - keep_start - keep_end - len(separator)

            if middle_max_length < 0:
                if fallback_to_original7:
                    return name
                else:  # just keep as much as end as possible
                    separator = ""
                    keep_start = 0
                    keep_end = max_length
                    middle_max_length = 0

        start_str = name[:keep_start]
        end_str = name[-keep_end:]

        middle = name[keep_start:-keep_end]
        shortened_middle = middle[:middle_max_length]

        res = start_str + shortened_middle + separator + end_str

    return res


def cond_remove_non_digits_between_digits(name, max_length):
    """
    The process, as illustrated by the this case: "Screenshot 2024-07-06 at 20.56.55 dog":

    If (and only if) it can shorten the name, replace non-digit chars between digits with "_":
    "Screenshot 2024-07-06 at 20.56.55 dog" -> "Screenshot 2024-07-06_20.56.55 dog"
    repeat until the name is short enough or no such cases remain.

    >>> cond_remove_non_digits_between_digits("Screenshot 2024-07-06 at 20.56.55 dogcat 2", 50) # no need to shorten
    'Screenshot 2024-07-06 at 20.56.55 dogcat 2'
    >>> cond_remove_non_digits_between_digits("Screenshot 2024-07-06 at 20.56.55 dogcat 2", 40) # remove one intron
    'Screenshot 2024-07-06_20.56.55 dogcat 2'
    >>> cond_remove_non_digits_between_digits("Screenshot 2024-07-06 at 20.56.55 dogcat 2", 30) # remove two introns
    'Screenshot 2024-07-06_20.56.55_2'
    """
    inter_non_digit_substrings = find_non_digit_between_digits(name)
    inter_non_digit_substrings = [s for s in inter_non_digit_substrings if len(s) > 1]

    res = name
    # replace them with "_", starting from the shortest, until the name is short enough
    for substring in sorted(inter_non_digit_substrings, key=len):
        if len(res) > max_length:
            res = res.replace(substring, "_")
        else:
            break
    return res


def shorten_non_digits_between_start_and_first_digit(name, max_length):
    """
    >>> nm = "Screenshot 2024-07-06 at 20.56.55 dog"
    >>> shorten_non_digits_between_start_and_first_digit(nm, 30)
    'Scre2024-07-06 at 20.56.55 dog'
    >>> shorten_non_digits_between_start_and_first_digit(nm, 20)
    '2024-07-06 at 20.56.55 dog'
    >>> shorten_non_digits_between_start_and_first_digit("no digits", 5)
    'no digits'
    """
    if len(name) <= max_length:
        return name

    # find the first digit
    first_digit_ind = -1
    for i, ch in enumerate(name):
        if ch.isdigit():
            first_digit_ind = i
            break

    if first_digit_ind >= 0:
        text_start = name[:first_digit_ind]
        digit_end = name[first_digit_ind:]

        # preserve digit_end, and reduce text_start as necessary
        chars_to_remove = len(text_start) + len(digit_end) - max_length

        chars_to_remove = min(chars_to_remove, len(text_start))

        # remove them from the end of text_start
        name = text_start[:-chars_to_remove] + digit_end

    else:
        pass

    return name


def shorten_non_digits_between_last_digit_and_end(name, max_length):
    """
    >>> shorten_name_containing_digits("2 some long str after digit", 5)
    '2igit'

    """

    if len(name) <= max_length:
        return name

    # find the last digit
    last_digit_ind = -1
    for i, ch in enumerate(reversed(name)):
        if ch.isdigit():
            last_digit_ind = len(name) - i - 1
            break

    if last_digit_ind >= 0:
        chars_between_last_dig_and_end = len(name) - last_digit_ind - 1
        chars_to_remove = len(name) - max_length
        chars_to_remove = min(chars_to_remove, chars_between_last_dig_and_end)
        digits_start = name[: last_digit_ind + 1]
        text_end = name[last_digit_ind + 1 :]

        # remove them from the start of text_end
        name = digits_start + text_end[chars_to_remove:]

    return name


def remove_non_digits(name, max_length):
    """
    >>> remove_non_digits("2024-07-06 20.56.55", 30) # do nothing
    '2024-07-06 20.56.55'
    >>> remove_non_digits("2024-07-06 20.56.55", 17)
    '20240706 20.56.55'
    >>> remove_non_digits("2024-07-06 20.56.55", 10)
    '20240706205655'
    """

    if len(name) <= max_length:
        return name

    how_many_chars_to_remove = len(name) - max_length

    # it shouldn't be more than the number of non-digits in name
    how_many_non_digits = sum(1 for ch in name if not ch.isdigit())
    how_many_chars_to_remove = min(how_many_chars_to_remove, how_many_non_digits)

    # iteratively remove non-digits, starting from the start of name
    clean_name = ""
    for ch in name:
        if ch.isdigit() or how_many_chars_to_remove == 0:
            clean_name += ch
        else:
            how_many_chars_to_remove -= 1

    return clean_name


def shorten_name_containing_digits(name, max_length):
    """

    >>> shorten_name_containing_digits("Screenshot 2024-07-06 at 20.56.55 dog", 30)
    'Screens2024-07-06_20.56.55 dog'
    >>> shorten_name_containing_digits("Screenshot 2024-07-06 at 20.56.55 dog", 20)
    '2024-07-06_20.56.55g'
    >>> shorten_name_containing_digits("Screenshot 2024-07-06 at 20.56.55 dog", 14)
    '20240706205655'
    >>> shorten_name_containing_digits("Screenshot 2024-07-06 at 20.56.55 dog", 10)
    '202407_655'
    >>> shorten_name_containing_digits("2 some long str after digit", 5)
    '2igit'

    """
    name = cond_remove_non_digits_between_digits(name, max_length)
    name = shorten_non_digits_between_start_and_first_digit(name, max_length)
    name = shorten_non_digits_between_last_digit_and_end(name, max_length)
    name = remove_non_digits(name, max_length)

    # we tried to shorten it gently. If it's still too long, we just remove the middle
    name = shrink_the_middle(name, max_length)

    return name


def skip_vowels(name, max_length):
    """
    >>> skip_vowels("Screenshot on Mac 2024-07-06 at 20.56.55 dog", 50)
    'Screenshot on Mac 2024-07-06 at 20.56.55 dog'
    >>> skip_vowels("Screenshot on Mac 2024-07-06 at 20.56.55 dog", 40)
    'Scrnsht n Mac 2024-07-06 at 20.56.55 dog'
    >>> skip_vowels("Screenshot on Mac 2024-07-06 at 20.56.55 dog", 30)
    'Scrnsht n Mc 2024-07-06 t 20.56.55 dg'
    >>> skip_vowels("Screenshot on Mac 2024-07-06 at 20.56.55 dog", 10)
    'Scrnsht n Mc 2024-07-06 t 20.56.55 dg'
    >>> skip_vowels("some_cool_html_files", 5)
    'sm_cl_html_files'
    """
    if len(name) <= max_length:
        return name

    english_vowels = "aeiou"

    # Check for HTML directory endings
    ending = ""
    for html_ending in HTML_DIR_ENDINGS:
        if name.endswith(html_ending):
            ending = html_ending
            name = name[: -len(html_ending)]
            break

    vowels_num = sum(1 for ch in name if ch.lower() in english_vowels)

    how_many_chars_to_remove = len(name) - max_length
    how_many_chars_to_remove = min(how_many_chars_to_remove, vowels_num)

    clean_name = ""
    for ch in name:
        if ch.lower() in english_vowels and how_many_chars_to_remove > 0:
            how_many_chars_to_remove -= 1
        else:
            clean_name += ch

    return clean_name + ending


def shorten_name(name, max_length):
    """
    >>> shorten_name("Screenshot on Mac 2024-07-06 at 20.56.55 dog", 50)
    'Screenshot on Mac 2024-07-06 at 20.56.55 dog'
    >>> shorten_name("Screenshot on Mac 2024-07-06 at 20.56.55 dog", 43)
    'screenshotOnMac2024-07-06At20.56.55Dog'
    >>> shorten_name("Screenshot on Mac 2024-07-06 at 20.56.55 dog", 35)
    'scrnshtOnMac2024-07-06At20.56.55Dog'
    >>> shorten_name("Screenshot on Mac 2024-07-06 at 20.56.55 dog", 30)
    'scrnshtnM2024-07-06t20.56.55Dg'
    >>> shorten_name("Screenshot on Mac 2024-07-06 at 20.56.55 dog", 20)
    '2024-07-06t20.56.55g'
    >>> shorten_name("Screenshot on Mac 2024-07-06 at 20.56.55 dog", 17)
    '20240706t20.56.55'
    >>> shorten_name("Screenshot on Mac 2024-07-06 at 20.56.55 dog", 15)
    '202407062056.55'
    >>> shorten_name("Screenshot on Mac 2024-07-06 at 20.56.55 dog", 10)
    '202407_655'
    """
    if len(name) <= max_length:
        return name

    name = to_camel_case(name, max_length, preserve_separators_between_digits7=True)

    name = skip_vowels(name, max_length)

    if proportion_of_digits_in_name(name) > 0.33:
        res = shorten_name_containing_digits(name, max_length)
    else:
        res = shrink_the_middle(name, max_length)
    return res
