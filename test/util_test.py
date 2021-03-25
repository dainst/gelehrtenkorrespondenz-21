import unittest

from data_access.util import subsequences_of_length, find_subsequence, remove_hyphenation


class SubsequencesOfLengthTest(unittest.TestCase):

    def test_normal_input(self):
        nums = [1, 2, 3, 4]
        result = subsequences_of_length(nums, 3)
        self.assertEqual([[1, 2, 3], [2, 3, 4]], result)

        chars = 'abcde'
        result = subsequences_of_length(chars, 3)
        self.assertEqual(['abc', 'bcd', 'cde'], result)

        result = subsequences_of_length(chars, 3, 4, 5)
        self.assertEqual(['abc', 'bcd', 'cde', 'abcd', 'bcde', 'abcde'], result)

        result = subsequences_of_length(chars, 1)
        self.assertEqual(['a', 'b', 'c', 'd', 'e'], result)

    def test_negative_or_empty_inputs(self):
        chars = 'abcde'

        self.assertEqual([], subsequences_of_length(chars, -1))
        self.assertEqual([], subsequences_of_length(chars, 0))
        self.assertEqual([], subsequences_of_length(chars, len(chars) + 1))
        self.assertEqual([], subsequences_of_length([], 1))
        self.assertEqual([], subsequences_of_length([], 1, 2, 3))
        self.assertEqual([], subsequences_of_length([], -1))

        result = subsequences_of_length(chars, 3, -1)
        self.assertEqual(['abc', 'bcd', 'cde'], result)


class FindSubsequenceTest(unittest.TestCase):

    def test_normal_inputs(self):
        nums = '0123456789'
        tests = [
            ('0', 0),
            ('9', 9),
            ('345', 3),
            ('5678', 5),
            ('12345', 1),
            (nums, 0),
            ('abc', -1),
            ('334', -1),
        ]
        for (item, expected) in tests:
            self.assertEqual(expected, find_subsequence(nums, item))
            # the result should not change if the sequence is repeated
            self.assertEqual(expected, find_subsequence(nums + nums, item))

    def test_seqeunces_other_than_string(self):
        self.assertEqual(2, find_subsequence([0, 1, 2, 3], [2, 3]))
        self.assertEqual(1, find_subsequence([23, 'abc', None, -0.3], ['abc', None]))

    def test_empty_inputs(self):
        nums = '0123456789'
        self.assertEqual(-1, find_subsequence([], []))
        self.assertEqual(-1, find_subsequence(nums, []))
        self.assertEqual(-1, find_subsequence([], 'abc'))
        self.assertEqual(-1, find_subsequence([], ''))
        self.assertEqual(-1, find_subsequence([], [None]))
        self.assertEqual(0, find_subsequence([None, None], [None]))


class RemoveHyphenationTest(unittest.TestCase):

    def test_working_inputs(self):
        tests = [
            (['Ein Zeilen-', 'umbruch weniger'],
             ['Ein Zeilenumbruch', 'weniger'],
             'Should remove normal linebreak.'),
            (['Ein Zeilen-', 'ümbruch weniger'],
             ['Ein Zeilenümbruch', 'weniger'],
             'Should handle Umlauts correctly.'),
            (['Zeilen-', 'umbruch'],
             ['Zeilenumbruch', ''],
             'Should handle one-word lines.'),
            (['\\eil$en-', 'umb[r]uch'],
             ['\\eil$enumb[r]uch', ''],
             'Should handle characters that need escaping.')
        ]
        for text, expected, msg in tests:
            self.assertEqual(expected, remove_hyphenation(text), msg)

    def test_inputs_without_result(self):
        tests = [
            (['Ein SPD-', 'Abgeordneter'], 'Should not remove linebreak if 2nd word is uppercase.'),
            (['Ein Zeilen-', ''], 'Should do nothing if the second line is empty.'),
            (['Ein Zeilen-'], 'Should do nothing if there is no second line.'),
            ([], 'Should handle the empty list without error'),
        ]
        for text, msg in tests:
            self.assertEqual(text, remove_hyphenation(text), msg)
