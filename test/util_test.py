import unittest

from data_access.util import subsequences_of_length, find_subsequence, items_around


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


class ItemsAroundTest(unittest.TestCase):

    def test_normal_inputs(self):
        nums = '0123456789'
        tests = [
            # Normal ranges
            (nums, 2, 1, ['2', '1', '3']),
            (nums, 2, 2, ['2', '1', '3', '0', '4']),
            (nums, 5, 3, ['5', '4', '6', '3', '7', '2', '8']),
            # Ranges touching start/end
            (nums, 2, 4, ['2', '1', '3', '0', '4', '5', '6']),
            (nums, 8, 4, ['8', '7', '9', '6', '5', '4']),
            # start and end
            (nums, 0, 3, ['0', '1', '2', '3']),
            (nums, len(nums) - 1, 3, ['9', '8', '7', '6']),
            # Empty/negative window size
            (nums, 2, 0, []),
            (nums, 2, -1, []),
            # Start outside of input
            (nums, -1, 3, []),
            (nums, len(nums), 3, []),
        ]
        for (items, start, window_size, expected) in tests:
            self.assertEqual(expected, list(items_around(items, start, window_size)))
