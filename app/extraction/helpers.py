import re
from typing import Optional


NUMBER_WORDS = {
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
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}


def number_from_text(value: str) -> Optional[int]:
    """Convert a numeric or written number into an integer."""

    value = value.lower().strip()

    if value.isdigit():
        return int(value)

    return NUMBER_WORDS.get(value)


def find_number(text: str, pattern: str) -> Optional[int]:
    """Find a number using a regular expression pattern."""

    match = re.search(pattern, text.lower())

    if not match:
        return None

    return int(match.group(1))