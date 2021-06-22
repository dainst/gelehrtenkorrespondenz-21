import os
import random
from pathlib import Path
from typing import List

from src.data_access.webanno_tsv import (NO_LABEL_ID, Annotation, Document,
                                         Sentence, Token,
                                         webanno_tsv_read_file)

RANDOM_SEED = 10

class DataSplit:

    def __init__(self, train_size: float = 0.8, test_size: float = 0.1, dev_size: float = 0.1):
        if (train_size <= 0 or train_size >= 1 or 
            test_size <= 0 or test_size >= 1 or
            dev_size <= 0 or dev_size >= 1 or 
            (train_size + test_size + dev_size) != 1.0):
            raise ValueError('All arguments must be between 0 and 1 and sum must be 1')

        self.train_size = train_size
        self.test_size = test_size
        self.dev_size = dev_size

    def train_split(self, files: List[str]) -> List[str]:
        return files[:int(self.train_size * len(files))]

    def test_split(self, files: List[str]) -> List[str]:
        train_idx = int(self.train_size * len(files))
        test_idx = int(self.test_size * len(files))
        return files[train_idx:train_idx + test_idx]

    def dev_split(self, files: List[str]) -> List[str]:
        train_idx = int(self.train_size * len(files))
        test_idx = int(self.test_size * len(files))
        return files[train_idx + test_idx:]

class WebAnnoIobDataTransformer:

    def __init__(
            self,
            data_split: DataSplit = DataSplit(),
            train_file_name = 'train.txt',
            test_file_name = 'test.txt',
            dev_file_name = 'dev.txt',
            iob_inside = 'I-',
            iob_null = 'O',
            iob_outside = 'B-',
            delimiter: str = '\t',
            lineterminator: str = '\n',
            coarse_ner_mapping: dict = {
                'PERmentioned' : 'PER',
                'PERaddressee' : 'PER',
                'PERauthor' : 'PER',
                'PER': 'PER',
                'DATEletter': 'DATE',
                'DATEmentioned': 'DATE',
                'DATErecieved': 'DATE',
                'DATEanswered': 'DATE',
                'DATEpoststamp': 'DATE',
                'DATE': 'DATE',
                'PLACEmentioned': 'PLACE',
                'PLACEfrom': 'PLACE',
                'PLACEto': 'PLACE',
                'PLACE': 'PLACE',
                'OBJtopography': 'OBJ',
                'OBJ': 'OBJ',
                'ORGmentioned': 'ORG',
                'ORGaddressee': 'ORG',
                'ORG': 'ORG',
                'MISC': 'MISC',
                'LIT': 'LIT'
            }):
        self.data_split = data_split
        self.train_file_name = train_file_name
        self.test_file_name = test_file_name
        self.dev_file_name = dev_file_name
        self.iob_inside = iob_inside
        self.iob_null = iob_null
        self.iob_outside = iob_outside
        self.delimiter = delimiter
        self.lineterminator = lineterminator
        self.coarse_ner_mapping = coarse_ner_mapping

    def transform(
            self, 
            source_path: str,
            output_path: str):
        """
        Transforms the WebAnno TSV annotations to an IOB format.
        The class configuration is used to store the output in three different
        output files (train, test and dev) with configurable split sizes 
        (default: Train -> 80%, Test -> 10%, Dev -> 10%).

        the output files will have fine grained entities as well as the coarse
        entity. The second column contains the fine entity and the third column
        contains the coarse entity.

        Example:
            WebAnno:
            1-3	4-9	Braun	*	PERauthor

            IOB output:
            Braun   B-PERauthor B-PER

        :param source_path: directory of WebAnno annotations
        :param output_path: directory of target output files
        """
        files: List[str] = self._retrieve_randomized_files(source_path)

        self._write_data(self.data_split.train_split(files), output_path, self.train_file_name)
        self._write_data(self.data_split.test_split(files), output_path, self.test_file_name)
        self._write_data(self.data_split.dev_split(files), output_path, self.dev_file_name)

    def _retrieve_randomized_files(self, source_path: str) -> List[str]:
        data: List[str] = []
        for root, dirs, files in os.walk(os.path.abspath(source_path)):
            for file in files:
                data.append(os.path.join(root, file))
        data.sort()
        random.seed(RANDOM_SEED)
        random.shuffle(data)
        return data

    def _write_data(self, files: List[str], output_dir: str, file_name: str):
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        output_file = os.path.abspath(os.path.join(output_dir, file_name))
        os.remove(output_file) if os.path.exists(output_file) else None
        with open(output_file, mode='a+', encoding='utf-8') as writer:
            for f in files:
                prev_label_id: int = NO_LABEL_ID
                for sentence in webanno_tsv_read_file(f).sentences:
                    for token in sentence.tokens:
                        writer.write(token.text)
                        writer.write(self.delimiter)
                        if token.annotations:
                            if (token.annotations[0].label_id == prev_label_id and token.annotations[0].label_id != NO_LABEL_ID):
                                self._write_annotation(writer, token.annotations[0], self.iob_inside)
                            else:
                                self._write_annotation(writer, token.annotations[0], self.iob_outside)
                            prev_label_id = token.annotations[0].label_id
                        else:
                            writer.write(self.iob_null)
                            writer.write(self.delimiter)
                            writer.write(self.iob_null)
                        writer.write(self.lineterminator)
                    writer.write(self.lineterminator)

    def _write_annotation(self, writer, annotation: Annotation, iob: str):
        writer.write(iob)
        writer.write(annotation.label)
        writer.write(self.delimiter)
        writer.write(iob)
        writer.write(self.coarse_ner_mapping[annotation.label])
