import os
import random
from difflib import SequenceMatcher
from typing import Callable, List

import matplotlib.pyplot as plt
import numpy as np
from src.data_access.iob_data_transformer import FINE_COARSE_NER_MAPPING
from src.data_access.webanno_tsv import (NO_LABEL_ID, Token,
                                         webanno_tsv_read_file)
from wordcloud import WordCloud


class WordCloudGenerator:

    def __init__(
            self,
            text_annotations: dict = {}, 
            text_with_frequencies: dict = {}):
        self.text_annotations = text_annotations
        self.text_with_frequencies = text_with_frequencies

    def extract_total_data(self, src_dir: str) -> dict:
        self.text_annotations = {}
        self.text_with_frequencies = {}

        for f in self._retrieve_files(src_dir):
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
            src_dir: str,
            base_entity: str,
            base_entity_types: List[str] = None,
            relation_entity_types: List[str] = None) -> dict:
        self.text_annotations = {}
        self.text_with_frequencies = {}
        for f in self._retrieve_files(src_dir):
            prev_label_id: int = NO_LABEL_ID
            prev_text: str = ''
            prev_token: Token = None
            temp_text_with_frequencies: dict = {}
            temp_text_annotations: dict = {}
            save: bool = False
            for sentence in webanno_tsv_read_file(f).sentences:
                for token in sentence.tokens:
                    if token.annotations:
                        if token.annotations[0].label_id == prev_label_id and token.annotations[0].label_id != NO_LABEL_ID:
                            prev_text += ' '
                            prev_text += token.text
                        else:
                            if prev_token != None:
                                if (prev_text.lower() == base_entity and (base_entity_types == None or
                                    prev_token.annotations[0].label in base_entity_types 
                                        or FINE_COARSE_NER_MAPPING[prev_token.annotations[0].label] in base_entity_types)):
                                    save = True
                                elif (relation_entity_types == None or (prev_token.annotations[0].label in relation_entity_types 
                                        or FINE_COARSE_NER_MAPPING[prev_token.annotations[0].label] in relation_entity_types)):
                                    frequency = temp_text_with_frequencies.get(prev_text.lower(), 0)
                                    temp_text_with_frequencies[prev_text.lower()] = frequency + 1
                                    temp_text_annotations[prev_text.lower()] = FINE_COARSE_NER_MAPPING[prev_token.annotations[0].label]
                            prev_token = token
                            prev_text = token.text
                        prev_label_id = token.annotations[0].label_id
            if save:
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

    def generate(self, 
            file_path: str = None,
            color_func: Callable = None,
            exclude_entities: List[str] = [],
            exclude_entity_types: List[str] = []):
        text_with_frequencies = self._filter(exclude_entities, exclude_entity_types)
        self._generate_word_cloud(text_with_frequencies, file_path, color_func)

    def _filter(self,
            exclude_entities: List[str] = None,
            exclude_entity_types: List[str] = []) -> dict:
        return {text: frequency 
                for text, frequency in self.text_with_frequencies.items() 
                if text not in exclude_entities and FINE_COARSE_NER_MAPPING[self.text_annotations[text]] not in exclude_entity_types}

    def _generate_word_cloud(
            self,
            text_with_frequencies: dict,
            file_path: str = None,
            color_func: Callable = None):
        mask = self._circle_mask()
        
        wordcloud = WordCloud(
            max_words = 100,
            width = 1000,
            height = 1000,
            background_color = 'white',
            include_numbers = True,
            mask = mask,
            prefer_horizontal=1.0).generate_from_frequencies(text_with_frequencies)

        if color_func == None:
            color_func = GroupedColorFunc(self.text_annotations)
        wordcloud.recolor(color_func = color_func)
        
        plt.figure()
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.show()

        if file_path != None:
            wordcloud.to_file(file_path)

    def _circle_mask(self): 
        x, y = np.ogrid[:1000, :1000]

        mask = (x - 500) ** 2 + (y - 500) ** 2 > 500 ** 2
        return 255 * mask.astype(int)

class GroupedColorFunc(object):
    """Create a color function object which assigns colors of
       specified colors to words based on the annotation.

       Uses wordcloud.get_single_color_func

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
