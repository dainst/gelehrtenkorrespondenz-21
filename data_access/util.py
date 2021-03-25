import re
from typing import List, Sequence, TypeVar

T = TypeVar('T')


def find_subsequence(containing: Sequence, contained: Sequence) -> int:
    """
    Return the index of contained in containing or -1 if there is no match
    or if the empty sequence is searched.

    :param containing: The sequence to search in.
    :param contained: The sequence to search for.
    :return: An int that if bigger than -1 has an element in containing.
    """
    if len(contained) == 0 or len(contained) > len(containing):
        return -1
    for i in range(len(containing) - len(contained) + 1):
        if containing[i] == contained[0]:
            if containing[i:i + len(contained)] == contained:
                return i
    return -1


def subsequences_of_length(sequence: Sequence[T], *lengths: int) -> Sequence[Sequence[T]]:
    """
    Examples:
         ([1, 2, 3, 4], 2)  -> [[1, 2], [2, 3], [3, 4]]
         ("abcde", 3)       -> ["abc", "bcd", "cde"]
         ("abcde", 3, 4, 5) -> ["abc", "bcd", "cde", "abcd", "bcde", "abcde"]
    """
    combinations = []
    for length in lengths:
        if length > 0:
            combinations += [sequence[i:i + length] for i in range(0, len(sequence) - length + 1)]
    return combinations


def remove_hyphenation(lines: List[str]) -> List[str]:
    """
    Removes hyphenations ("-") at the end of each input line by
    looking at both words and merging them if the second does not start
    with an uppercase letter. (This works reasonably well for german texts.)

    :param lines: A list of strings to replace hyphens in.
    :return: The same list with hyphens removed in place.
    """
    hyphen_end = re.compile('-$')
    last_word = re.compile('[^\\s]+-$')
    first_word = re.compile('^[^\\s]+')
    for i in range(0, len(lines) - 1):
        word1 = last_word.search(lines[i])
        if word1:
            word2 = first_word.search(lines[i + 1])
            if word2 and word2.group()[0].islower():
                combined = hyphen_end.sub('', word1.group()) + word2.group()
                lines[i] = last_word.sub(lambda _: combined, lines[i])  # lambda keeps repl from being interpreted
                lines[i + 1] = first_word.sub('', lines[i + 1]).lstrip()
    return lines
