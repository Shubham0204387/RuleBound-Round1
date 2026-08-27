import re
from typing import Optional


def extract_capacity(text: str) -> Optional[int]:
    """
    Extract capacity from phrases such as:

    12-person
    16 person
    team of 10
    for 14 people
    """

    patterns = [
        r"(\d+)\s*[- ]?person",
        r"team\s+of\s+(\d+)",
        r"for\s+(\d+)\s+people",
        r"(\d+)\s+people",
    ]

    lower = text.lower()

    for pattern in patterns:
        match = re.search(pattern, lower)

        if match:
            return int(match.group(1))

    return None