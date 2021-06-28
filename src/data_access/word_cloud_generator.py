import os
from enum import Enum
from typing import Callable, List

import matplotlib.pyplot as plt
import numpy as np
from src.data_access.iob_data_transformer import FINE_COARSE_NER_MAPPING
from src.data_access.webanno_tsv import (NO_LABEL_ID, Token,
                                         webanno_tsv_read_file)
from wordcloud import WordCloud


class Operator(Enum):
    OR = 1
    AND = 2

class WordCloudGenerator:

    def __init__(
            self,
            text_annotations: dict = {}, 
            text_with_frequencies: dict = {}):
        self.text_annotations = text_annotations
        self.text_with_frequencies = text_with_frequencies

    def extract_total_data(self, source_path: str) -> dict:
        """
        Iterates through all WebAnno TSV files and retrieves all
        entities and their frequency within all files

        Parameters
        ----------
        source_path : str
            The source path of the TSV files
        """
        self.text_annotations = {}
        self.text_with_frequencies = {}

        for f in self._retrieve_files(source_path):
            prev_label_id: int = NO_LABEL_ID
            prev_text: str = ''
            prev_token: Token = None
            for sentence in webanno_tsv_read_file(f).sentences:
                for token in sentence.tokens:
                    if token.annotations:
                        if token.annotations[0].label_id == prev_label_id and token.annotations[0].label_id != NO_LABEL_ID:
                            prev_text += ' '
                            prev_text += token.text
                        else:
                            if prev_token != None:
                                frequency = self.text_with_frequencies.get(prev_text.lower(), 0)
                                self.text_with_frequencies[prev_text.lower()] = frequency + 1
                                self.text_annotations[prev_text.lower()] = FINE_COARSE_NER_MAPPING[prev_token.annotations[0].label]
                            prev_token = token
                            prev_text = token.text
                        prev_label_id = token.annotations[0].label_id

    def extract_coocurrences(
            self, 
            source_path: str,
            word_entities: dict,
            entity_only: bool = True,
            operator: Operator = Operator.OR,
            relation_entity_types: List[str] = None) -> dict:
        """
        Iterates through all WebAnno TSV files and counts
        frequencies within a file for tokens (either entities
        or non entity tokens). The tokens for the calculations
        can be concatenated logically, i.e. AND or OR operator
        and also specified with what entity type it should be
        calculated, e.g. as PERauthor or as PERaddressee.

        Further, the co-ocurrences can also be constrained to
        given entity types.

        Parameters
        ----------
        source_path : str
            Source path of the TSV files
        
        word_entities: dict
            Key: Tokens to calculate co-ocurrences, either non
            entity tokens or entities. 
            Value: If specified the entity type for which the
            co-occurrences should be calculated.

        entity_only:
            Flag to indicate if word_entities are to be treated
            as non entity token or entity.

        operator:
            Logical operator (AND or OR) to concatenate the items
            of word_entities.

        relation_entity_types:
            List of entity types for which co-occurrences should
            be calculated.

        """
        self.text_annotations = {}
        self.text_with_frequencies = {}
        for f in self._retrieve_files(source_path):
            prev_label_id: int = NO_LABEL_ID
            prev_text: str = ''
            prev_token: Token = None
            temp_text_with_frequencies: dict = {}
            temp_text_annotations: dict = {}
            matched: int = 0
            for sentence in webanno_tsv_read_file(f).sentences:
                for token in sentence.tokens:
                    if not entity_only and token.text.lower() in word_entities:
                        matched += 1
                    if token.annotations:
                        if token.annotations[0].label_id == prev_label_id and token.annotations[0].label_id != NO_LABEL_ID:
                            prev_text += ' '
                            prev_text += token.text
                        else:
                            if prev_token != None:
                                if self._token_in_word_entities(prev_token, word_entities):
                                    matched += 1
                                elif (relation_entity_types == None or (prev_token.annotations[0].label in relation_entity_types 
                                        or FINE_COARSE_NER_MAPPING[prev_token.annotations[0].label] in relation_entity_types)):
                                    frequency = temp_text_with_frequencies.get(prev_text.lower(), 0)
                                    temp_text_with_frequencies[prev_text.lower()] = frequency + 1
                                    temp_text_annotations[prev_text.lower()] = FINE_COARSE_NER_MAPPING[prev_token.annotations[0].label]
                            prev_token = token
                            prev_text = token.text
                        prev_label_id = token.annotations[0].label_id
            if operator == Operator.OR and matched > 0 or Operator.AND and matched >= len(word_entities):
                for text, freq in temp_text_with_frequencies.items():
                    stored_freq = self.text_with_frequencies.get(text, 0)
                    self.text_with_frequencies[text] = stored_freq + freq
                for text, annotation in temp_text_annotations.items():
                    self.text_annotations[text] = annotation

    def _retrieve_files(self, source_path: str) -> List[str]:
        data: List[str] = []
        for root, dirs, files in os.walk(os.path.abspath(source_path)):
            for file in files:
                data.append(os.path.join(root, file))
        return data

    def _token_in_word_entities(
            self, 
            token: Token, 
            word_entities: dict):
        for word, entity in word_entities.items():
            if token.text.lower() == word.lower() and (
                    not entity or entity == '' 
                    or token.annotations[0].label == entity
                    or FINE_COARSE_NER_MAPPING[token.annotations[0].label] == entity):
                return True
        return False

    def generate(self, 
            output_path: str = None,
            color_func: Callable = None,
            exclude_entities: List[str] = [],
            exclude_entity_types: List[str] = []):
        """
        Generates a word cloud and uses interal data, i.e.
        frequency calculation must be done before calling
        this function. It is possible to exclude certain
        entities or groups of entities, i.e. entity types.

        Parameters
        ----------
        output_path : str
            If give, output path to store word clouds as PNGs.
        
        color_func: dict
            If given, uses own color function. Otherwise
            GroupedColorFunc will be used.

        exclude_entities:
            If given, entity tokens to be ignored for the 
            word cloudgeneration.

        exclude_entity_types:
            If give, entity types to be ignored for the 
            word cloud generation. 
        """
        text_with_frequencies = self._filter(exclude_entities, exclude_entity_types)
        self._generate_word_cloud(text_with_frequencies, output_path, color_func)

    def _filter(self,
            exclude_entities: List[str] = None,
            exclude_entity_types: List[str] = []) -> dict:
        return {text: frequency 
                for text, frequency in self.text_with_frequencies.items() 
                if text not in exclude_entities and FINE_COARSE_NER_MAPPING[self.text_annotations[text]] not in exclude_entity_types}

    def _generate_word_cloud(
            self,
            text_with_frequencies: dict,
            output_path: str = None,
            color_func: Callable = None):
        mask = self._circle_mask()
        
        wordcloud = WordCloud(
            max_words = 100,
            width = 1000,
            height = 1000,
            background_color = 'white',
            include_numbers = True,
            repeat = False,
            mask = mask,
            prefer_horizontal=1.0).generate_from_frequencies(text_with_frequencies)

        if color_func == None:
            color_func = GroupedColorFunc(self.text_annotations)
        wordcloud.recolor(color_func = color_func)
        
        plt.figure()
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.show()

        if output_path != None:
            wordcloud.to_file(output_path)

    def _circle_mask(self): 
        x, y = np.ogrid[:1000, :1000]

        mask = (x - 500) ** 2 + (y - 500) ** 2 > 500 ** 2
        return 255 * mask.astype(int)

class GroupedColorFunc(object):
    """Create a color function object which assigns colors of
       specified colors to words based on the annotation.

       Parameters
       ----------
       text_annotations : dict(str -> str)
         A dictionary that contains a word with its annotation.

       default_color : str
         Color that will be assigned to a word that's not a member
         of any value from color_to_words.
    """

    def __init__(self, text_annotations, default_color='grey'):
        color_def = self.random_color_definition()
        self.word_to_color = {word: color_def.get(annotation)
                              for (word, annotation) in text_annotations.items()}
        self.default_color = default_color

    def random_color_definition(self) -> dict:
        return {
                'PER': '#ed8311',
                'DATE': '#ba0404',
                'PLACE': '#40ab02',
                'OBJ': '#0283ba',
                'ORG': '#4c02ba',
                'MISC': '#02a8ba',
                'LIT': '#f0e800'
            }

    def __call__(self, word, **kwargs):
        return self.word_to_color.get(word, self.default_color)
