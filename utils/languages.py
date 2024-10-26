import re
import unicodedata
import random

HTML_DIR_ENDINGS = ["_files", " Files", ".files", "-files", ".html_files"]
HTML_DIR_ENDINGS.sort(key=len, reverse=True)  # sort by length, descending


def transliterate_according_to_scheme(text, source_target_dict):
    """ """

    result = ""
    for char in text:
        if char.isupper():
            result += source_target_dict.get(char.lower(), char).upper()
        else:
            result += source_target_dict.get(char, char)
    return result


def transliterate_german(text):
    """
    >>> transliterate_german("Grüße aus Berlin!")
    'Gruesse aus Berlin!'
    >>> transliterate_german("Café")
    'Cafe'
    >>> transliterate_german("Nyx’ Bö drückt Vamps Quiz-Floß jäh weg.") # A pangram
    'Nyx’ Boe drueckt Vamps Quiz-Floss jaeh weg.'
    """

    german_letters_and_common_loan_letters = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "é": "e",
        "ç": "c",
        "à": "a",
        "è": "e",
        "ì": "i",
        "ò": "o",
        "ù": "u",
        "ñ": "n",
        "ï": "i",
    }

    result = transliterate_according_to_scheme(
        text, german_letters_and_common_loan_letters
    )
    return result


def transliterate_russian(text):
    """
    Properties of this transliteration scheme:
    - it is fully reversible
    - each Russian letter is transliterated to a 1-2 Latin letters
    - h and j serve only as a special letters to ensure that the transliteration is reversible
    - h is always the second letter in a pair, never alone
    - j is always the first letter in a pair, never alone

    >>> transliterate_russian("Привет, мир!")
    'Privjet, mir!'
    >>> transliterate_russian("ПРИВЕТ, МИР!")
    'PRIVJET, MIR!'
    >>> transliterate_russian("психотерапия")
    'psikhotjerapija'
    >>> transliterate_russian("Эй, жлоб! Где туз? Прячь юных съёмщиц в шкаф.") # A pangram
    'Eji, zhlob! Gdje tuz? Prjachjh uhnyhkh sqhjomxhic v shkaf.'
    >>> transliterate_russian("Экс-граф? Плюш изъят. Бьём чуждый цен хвощ!") # A pangram
    'Eks-graf? Pluhsh izqhjat. Bjhjom chuzhdyhji cjen khvoxh!'
    >>> transliterate_russian("Вступив в бой с шипящими змеями — эфой и гадюкой — маленький, цепкий, храбрый ёж чуть не съел их.") # A pangram
    'Vstupiv v boji s shipjaxhimi zmjejami — efoji i gaduhkoji — maljenjhkiji, cjepkiji, khrabryhji jozh chutjh nje sqhjel ikh.'
    >>> transliterate_russian("non-russian text")
    'non-russian text'
    """
    Russian_letters = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "je",
        "ё": "jo",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "ji",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "kh",
        "ц": "c",
        "ч": "ch",
        "ш": "sh",
        "щ": "xh",
        "ъ": "qh",
        "ы": "yh",
        "ь": "jh",
        "э": "e",
        "ю": "uh",
        "я": "ja",
    }

    result = transliterate_according_to_scheme(text, Russian_letters)
    return result


def transliterate_russian_and_german(text):
    """

    >>> transliterate_russian_and_german("Übung делает мастера")
    'UEbung djelajet mastjera'
    """
    text = transliterate_russian(text)
    text = transliterate_german(text)
    return text


def to_camel_case(name, max_length, preserve_separators_between_digits7=False):
    """Convert to camelCase while preserving all letters and digits, but removing other characters.
    If HTML directory endings are present, only modify the part before them.
    >>> to_camel_case("hello-world", 5)
    'helloWorld'
    >>> to_camel_case("hello-world-123", 5)
    'helloWorld123'
    >>> to_camel_case("hello-world_files", 5)
    'helloWorld_files'
    >>> to_camel_case("hi", 500)
    'hi'
    """
    if len(name) <= max_length:
        return name

    # Check for HTML directory endings
    ending = ""
    for html_ending in HTML_DIR_ENDINGS:
        if name.endswith(html_ending):
            ending = html_ending
            name = name[: -len(html_ending)]
            break

    result = []
    capitalize_next = False

    for i, char in enumerate(name):
        if char.isalnum():
            if capitalize_next:
                result.append(char.upper())
                capitalize_next = False
            else:
                result.append(char.lower())
        else:
            if preserve_separators_between_digits7:
                if (
                    i > 0
                    and i < len(name) - 1
                    and name[i - 1].isdigit()
                    and name[i + 1].isdigit()
                ):
                    result.append(char)
                    capitalize_next = False
                    continue
            capitalize_next = True

    if result:
        result[0] = result[0].lower()

    return "".join(result) + ending


def remove_questionable_chars(name):
    """
    Removes characters that are usually not problematic for filesystems,
    but can cause problems in scripts etc.


    >>> remove_questionable_chars("3_Isaac Asimov's Robot Mysteries")
    '3_Isaac Asimovs Robot Mysteries'
    >>> remove_questionable_chars("26 - Asimov, Isaac - Bicentennial Man - 1976")
    '26 - Asimov_ Isaac - Bicentennial Man - 1976'
    >>> remove_questionable_chars("9-10 - Brandon, Shea & Moore")
    '9-10 - Brandon_ Shea _and_ Moore'
    >>> remove_questionable_chars("Комментарии к пройденному [Другая редакция].txt")
    'Комментарии к пройденному _Другая редакция_.txt'
    >>> remove_questionable_chars("Отель «У погибшего альпиниста».txt")
    'Отель _У погибшего альпиниста_.txt'
    >>> remove_questionable_chars("Asimov, Isaac - Found! - 1978.txt")
    'Asimov_ Isaac - Found_ - 1978.txt'
    """
    suspicious_chars = r"[](){}«»!@#%^=;,`’!—―‒"

    special_replacements = {
        "&": "_and_",
        "'": "",  # e.g. Asimov's -> Asimovs
        "~": "tilde_", # e.g. .~lock.canned_responses.csv
    }

    for char in suspicious_chars:
        name = name.replace(char, "_")

    for char, replacement in special_replacements.items():
        name = name.replace(char, replacement)

    return name


def remove_bad_chars(name):
    """

    Note:
    If the original name contains __ (double underscores),
    and doesn't need to be shortened, we keep it.
    This is important, because in some software projects it creates so many renamings,
    they bury important changes in the list of changes.


    >>> remove_bad_chars("hello") # no bad characters
    'hello'
    >>> remove_bad_chars("hello:world")
    'hello_world'
    >>> remove_bad_chars("Alice" + chr(0) + "Bob") # control character
    'AliceBob'
    >>> remove_bad_chars("Ａｌｉｃｅ")  # fullwidth characters
    'Alice'
    >>> remove_bad_chars("йод übung")  # non-ascii characters
    'йод_übung'
    >>> remove_bad_chars("world.")
    'world'
    >>> remove_bad_chars("world..")
    'world'
    >>> remove_bad_chars("world ")
    'world'
    >>> res = remove_bad_chars("") # empty string
    >>> res.startswith("unnamed_")
    True
    >>> remove_bad_chars("9-10 - Brandon, Shea & Moore")
    '9-10_Brandon_Shea_and_Moore'
    >>> remove_bad_chars("__init__.cpython-38.pyc")
    '__init__.cpython-38.pyc'
    >>> remove_bad_chars("__pycache__")
    '__pycache__'
    >>> remove_bad_chars("__MACOSX")
    '__MACOSX'
    >>> remove_bad_chars("test__datasource.cpython-36.pyc")
    'test__datasource.cpython-36.pyc'
    """
    already_had_double_underscores7 = "__" in name

    # Define bad characters
    bad_chars = r'<>:"/\|?*'

    # Replace bad characters with underscore
    for char in bad_chars:
        name = name.replace(char, "_")

    # Remove control characters
    name = "".join(ch for ch in name if unicodedata.category(ch)[0] != "C")

    # Normalize unicode characters
    name = unicodedata.normalize("NFKC", name)

    # Remove trailing periods or spaces
    name = name.rstrip(". ")

    name = remove_questionable_chars(name)

    # remove spaces
    name = name.replace(" ", "_")

    if not already_had_double_underscores7:  # to avoid damaging "__pycache__" etc
        # remove duplicated underscores, regardless of their number
        while "__" in name:
            name = name.replace("__", "_")

    common_white_space_artifacts = ["_-_", "_-", "-_"]
    for artifact in common_white_space_artifacts:
        name = name.replace(artifact, "_")

    # Ensure the name is not empty
    if not name:
        name += "unnamed_" + str(random.randint(10000, 99999))
    return name


def proportion_of_digits_in_name(name):
    """
    >>> proportion_of_digits_in_name("hello")
    0.0
    >>> proportion_of_digits_in_name("hello123")
    0.375
    >>> proportion_of_digits_in_name("123")
    1.0
    >>> round(proportion_of_digits_in_name("Screenshot 2024-07-06 at 20.56.55"), 2)
    0.42
    >>> proportion_of_digits_in_name("")
    0
    """
    if len(name) > 0:
        digits = sum(1 for ch in name if ch.isdigit())
        res = digits / len(name)
    else:
        res = 0
    return res


def find_non_digit_between_digits(text):
    """
    >>> find_non_digit_between_digits("Screenshot 2024-07-06 at 20.56.55 dog")
    ['-', '-', ' at ', '.', '.']
    >>> find_non_digit_between_digits("123abc456def789")
    ['abc', 'def']
    >>> find_non_digit_between_digits("No digits here!")
    []
    >>> find_non_digit_between_digits("1a2b3c4")
    ['a', 'b', 'c']
    >>> find_non_digit_between_digits("1  2")
    ['  ']
    >>> find_non_digit_between_digits("12345")
    []
    >>> find_non_digit_between_digits("")
    []
    >>> find_non_digit_between_digits("abc123")
    []
    >>> find_non_digit_between_digits("123abc")
    []
    >>> find_non_digit_between_digits("1a2b3c")
    ['a', 'b']
    >>> find_non_digit_between_digits("1.2,3")
    ['.', ',']
    >>> find_non_digit_between_digits("1abc2def3")
    ['abc', 'def']
    >>> find_non_digit_between_digits("12345_6789")
    ['_']
    >>> find_non_digit_between_digits("7abc7")
    ['abc']
    """
    result = []
    current_substring = ""
    between_digits7 = False
    # last_was_digit7 = False

    for char in text:
        if char.isdigit():
            if between_digits7 and current_substring:
                result.append(current_substring)
                current_substring = ""
            between_digits7 = True
            # last_was_digit7 = True
        elif between_digits7:
            current_substring += char
            # last_was_digit7 = False
        else:
            # last_was_digit7 = False
            pass

    # Don't add the last substring if it's not followed by a digit
    # if between_digits7 and current_substring and last_was_digit7:
    #    result.append(current_substring)

    return result
