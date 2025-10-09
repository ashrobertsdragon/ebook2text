NOT_CHAPTER = {
    "about",
    "acknowledgements",
    "afterward",
    "annotation",
    "appendix",
    "assessment",
    "backmatter",
    "bibliography",
    "colophon",
    "conclusion",
    "contents",
    "contributors",
    "copyright",
    "cover",
    "credits",
    "dedication",
    "division",
    "endnotes",
    "epigraph",
    "errata",
    "footnotes",
    "forward",
    "frontmatter",
    "glossary",
    "imprintur",
    "imprint",
    "index",
    "introduction",
    "landmarks",
    "list",
    "notice",
    "page",
    "preamble",
    "preface",
    "prologue",
    "question",
    "rear",
    "revision",
    "sign up",
    "table",
    "toc",
    "volume",
    "warning",
}


def roman_to_int(roman_num: str) -> int:
    """
    Convert a Roman numeral to an integer.

    Arguments:
        roman_num (str): A string representing the Roman numeral.

    Returns:
        int: The integer value of the Roman numeral.

    Raises:
        ValueError if string is not a Roman numeral.
    """
    if not isinstance(roman_num, str):
        raise TypeError("Input must be a string")

    roman: str = roman_num.upper()

    for numeral in ("V", "L", "D"):
        if roman.count(numeral) > 1:
            raise ValueError("Not roman numeral")

    roman_numerals = {
        "I": 1,
        "V": 5,
        "X": 10,
        "L": 50,
        "C": 100,
        "D": 500,
        "M": 1000,
    }

    total: int = 0
    prev_value: int = 0
    consecutive_count: int = 1
    previous_char: str = ""

    for char in reversed(roman):
        if char not in roman_numerals:
            raise ValueError("Not roman numeral")

        consecutive_count = (
            consecutive_count + 1 if char == previous_char else 1
        )
        if consecutive_count > 3:
            raise ValueError("Not roman numeral")

        value = roman_numerals[char]
        if value >= prev_value:
            total += value
        else:
            if previous_char == "":
                raise ValueError("Not roman numeral")
            elif previous_char in ("V", "X") and char != "I":
                raise ValueError("Not roman numeral")
            elif previous_char in ("L", "C") and char != "X":
                raise ValueError("Not roman numeral")
            elif previous_char in ("D", "M") and char != "C":
                raise ValueError("Not roman numeral")
            total -= value
        prev_value = value
        previous_char = char
    if not total:
        raise ValueError("Not roman numeral")
    return total


def word_to_num(number_string: str) -> int:
    """
    Convert a spelled-out number without spaces or hyphens to a string of the
    integer. The function supports numbers from 0 to 99 and is case
    insensitive.
    Args:
        number_string (str): A string representing the spelled-out number.
    Returns:
        int: The integer value of the spelled-out number.
    """
    if not isinstance(number_string, str):
        raise TypeError("Must be a string")
    if not number_string:
        raise ValueError("Must have a value")

    num_words = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "teen": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "twenty": 20,
        "thirty": 30,
        "forty": 40,
        "fifty": 50,
        "sixty": 60,
        "seventy": 70,
        "eighty": 80,
        "ninety": 90,
    }

    num_str_lower: str = number_string.lower()
    cleaned_num_str: str = num_str_lower.replace("-", "").replace(" ", "")
    total: int = 0
    temp_word: str = ""

    for char in reversed(cleaned_num_str):
        temp_word = char + temp_word
        if temp_word in num_words:
            total += num_words[temp_word]
            temp_word = ""

    if temp_word:
        raise ValueError(f"Unknown number word: {temp_word}")
    return total


def is_spelled_out_number(s: str) -> bool:
    """
    Try to convert the word to an integer. If it's not a valid spelled-out
    number, it will raise a ValueError
    """

    try:
        word_to_num(s)
        return True
    except ValueError:
        return False


def is_roman_numeral(word: str) -> bool:
    """
    Try to convert the word to an integer. If it"s not a valid roman numeral,
    it will raise a ValueError
    """

    try:
        roman_to_int(word)
        return True
    except (ValueError, TypeError):
        return False


def is_number(s: str) -> bool:
    """
    Check if a string contains a number value either as digits,
    roman numerals, or spelled-out numbers.
    """

    return s.isdigit() or is_roman_numeral(s) or is_spelled_out_number(s)


def is_chapter(s: str) -> bool:
    """
    Check if a string contains the word "chapter", a Roman numeral, a
    spelled-out number, or a digit.
    Arguments:
        s (str): The string to check.
    Returns bool: True if the string meets the criteria, False otherwise.
    """
    lower_s = s.lower().strip()
    return lower_s.startswith("chapter") or (
        len(lower_s.split()) == 1 and is_number(lower_s)
    )


def is_not_chapter(paragraph: str, metadata: dict) -> bool:
    """
    Checks if the given text indicates that it is not a chapter.
    """
    title = metadata.get("title", "no title found")
    author = metadata.get("author", "no author found")
    paragraph = paragraph.lower()
    return any(
        paragraph.startswith(title.lower())
        or paragraph.startswith(author.lower())
        or paragraph.startswith(not_chapter_word)
        for not_chapter_word in NOT_CHAPTER
    )
