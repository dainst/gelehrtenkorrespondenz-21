import os
import unittest

from src.data_access.iob_data_transformer import (DataSplit,
                                                  WebAnnoIobDataTransformer)

RESSOURCE_PATH='resources/test_iob_data_transformer/'

class DataSplitTest(unittest.TestCase):

    def test_bad_params(self):
        self.assertRaises(ValueError, DataSplit, 0)
        self.assertRaises(ValueError, DataSplit, 1)
        self.assertRaises(ValueError, DataSplit, 0.1, 0)
        self.assertRaises(ValueError, DataSplit, 0.1, 1)
        self.assertRaises(ValueError, DataSplit, 0.1, 0.1, 0)
        self.assertRaises(ValueError, DataSplit, 0.1, 0.1, 1)
        self.assertRaises(ValueError, DataSplit, 0.4, 0.4, 0.1)
        self.assertRaises(ValueError, DataSplit, 0.4, 0.4, 0.3)

    def test_split_defaults(self):
        data = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        data_split = DataSplit()

        self.assertEqual(['1', '2', '3', '4', '5', '6', '7', '8'], data_split.train_split(data))
        self.assertEqual(['9'], data_split.test_split(data))
        self.assertEqual(['10'], data_split.dev_split(data))

    def test_split_custom(self):
        data = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        data_split = DataSplit(train_size=0.1, test_size=0.5, dev_size=0.4)

        self.assertEqual(['1'], data_split.train_split(data))
        self.assertEqual(['2', '3', '4', '5', '6'], data_split.test_split(data))
        self.assertEqual(['7', '8', '9', '10'], data_split.dev_split(data))

class WebAnnoIobDataTransformerTest(unittest.TestCase):

    def test_transform(self):
        source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), RESSOURCE_PATH, 'input'))
        output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), RESSOURCE_PATH, 'output'))
        transformer = WebAnnoIobDataTransformer()

        transformer.transform(source_path=source_path, output_path=output_path)

        self.assertTrue(os.path.exists(os.path.join(output_path, 'train.txt')))
        self.assertTrue(os.path.exists(os.path.join(output_path, 'test.txt')))
        self.assertTrue(os.path.exists(os.path.join(output_path, 'dev.txt')))

        os.remove(os.path.join(output_path, 'train.txt'))
        os.remove(os.path.join(output_path, 'test.txt'))
        os.remove(os.path.join(output_path, 'dev.txt'))

