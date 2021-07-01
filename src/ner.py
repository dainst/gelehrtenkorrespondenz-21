import os
import re
from pathlib import Path

from flair.data import Sentence as Flair_Sentence
from flair.models import SequenceTagger

from src.data_access.book_viewer_json import BookViewerJsonBuilder, Kind
from src.data_access.iob_data_transformer import (IOB_INSIDE, IOB_NULL,
                                                  IOB_OUTSIDE)
from src.data_access.webanno_tsv import NO_LABEL_ID, Annotation, Document
from src.data_access.webanno_tsv import Sentence as WebAnno_Sentence
from src.data_access.webanno_tsv import Token, webanno_tsv_write
from src.match_webanno_ocr import (OUTPUT_LAYERS, PAGE_SEP, TARGET_FIELD,
                                   TARGET_LAYER, clean_ocr, sentence_tokenizer)
from src.write_book_viewer_json import convert_annotation

LABELS_TO_KINDS = [
    (re.compile('PER'), Kind.person),
    (re.compile('PLACE'), Kind.location),
    (re.compile('DATE'), Kind.timex),
    (re.compile('(OBJ|ORG|LIT|MISC)'), Kind.keyterm)
]

class NER:

    def __init__(self, model_path: str):
        self.tagger = SequenceTagger.load(model_path)

    def annotate_files(self, source_path: str, output_webanno_path: str, output_bookviewer_path: str):
        for root, dirs, files in os.walk(os.path.abspath(source_path)):
            for file in files:
                self.annotate_file(
                    file = os.path.join(root, file),
                    output_webanno_path = output_webanno_path,
                    output_bookviewer_path = output_bookviewer_path)
    
    def annotate_file(self, file: str, output_webanno_path: str, output_bookviewer_path: str):
        with open(file, mode='r', encoding='utf-8') as f:
            pages = f.read().split(PAGE_SEP)
            builder = BookViewerJsonBuilder()
            last_annotation = None
            for page_number, page_text in enumerate(pages):
                doc = self.annotate_page(
                    page_text = page_text,
                    last_annotation = last_annotation)
                
                self.write_webanno_file(
                    output_path = output_webanno_path, 
                    file = file, 
                    page_number = page_number, 
                    doc = doc)

                for annotation in doc.annotations_with_type(TARGET_LAYER, TARGET_FIELD):
                    convert_annotation(
                        builder = builder, 
                        page_no = page_number, 
                        a = annotation, 
                        labels_to_kinds = LABELS_TO_KINDS)
            
            self.write_bookviewer_file(
                output_path = output_bookviewer_path,
                file = file,
                builder = builder
            )
                

    def annotate_page(self, page_text: str, last_annotation: Annotation):
        next_token_idx = 0
        next_label_idx = 1
        last_label_prefix = None
        doc = Document(OUTPUT_LAYERS)
        sentences = sentence_tokenizer.tokenize(clean_ocr(page_text), realign_boundaries=True)
        for i, sentence_text in enumerate(sentences):
            text = sentence_text.replace('\n', ' ')
            flair_sentence = Flair_Sentence(text)
            self.tagger.predict(flair_sentence)
            webanno_sentence = WebAnno_Sentence(doc, idx=i+1, text=text)
            for token_idx, flair_token in enumerate(flair_sentence, start=1):
                webanno_token = self.create_token(
                    text = flair_token.text,
                    next_token_idx = next_token_idx,
                    current_token_idx = token_idx)
                webanno_token.sentence = webanno_sentence 
                webanno_sentence.add_token(webanno_token)
                
                label_id = NO_LABEL_ID
                label = flair_token.get_tag('ner').value.replace(IOB_INSIDE, '').replace(IOB_OUTSIDE, '')
                
                if label != IOB_NULL:
                    if IOB_INSIDE in flair_token.get_tag('ner').value:
                        label_id = next_label_idx
                        last_label_prefix = IOB_INSIDE

                        if last_annotation != None and last_annotation.label == label:
                            last_annotation.label_id = label_id

                        # for the rare case that on a new page the first annotation
                        # was falsely identified as 'I-' we treat it as 'B-' 
                        if last_annotation == None:
                            last_label_prefix = IOB_OUTSIDE
                            label_id = NO_LABEL_ID

                    if IOB_OUTSIDE in flair_token.get_tag('ner').value:
                        if last_label_prefix == IOB_INSIDE:
                            next_label_idx += 1
                        last_label_prefix = IOB_OUTSIDE

                    last_annotation = Annotation(
                        tokens=[webanno_token],
                        label=label,
                        layer_name=TARGET_LAYER,
                        field_name=TARGET_FIELD,
                        label_id=label_id,
                    )
                    doc._annotations[
                        doc._anno_type(last_annotation.layer_name, 
                        last_annotation.field_name)].append(last_annotation)
            doc.add_sentence(webanno_sentence)
        return doc


    def create_token(self, text: str, next_token_idx: int, current_token_idx: int):
        token_utf16_length = int(len(text.encode('utf-16-le')) / 2)
        end = next_token_idx + token_utf16_length
        webanno_token = Token(
            sentence = None,
            idx = current_token_idx, 
            start = next_token_idx, 
            end = end, 
            text = text)
        next_token_idx = end + 1
        return webanno_token


    def write_webanno_file(self, output_path: str, file: str, page_number: int, doc: Document):
        output_file = self.create_webanno_file(
            output_path = output_path, 
            file = file, 
            page_number = page_number)
        with open(output_file, mode='w+', encoding='utf-8') as writer:
            writer.write(webanno_tsv_write(doc))


    def create_webanno_file(self, output_path: str, file: str, page_number: int):
        output_path = os.path.join(output_path, Path(file).stem)
        Path(output_path).mkdir(parents=True, exist_ok=True)
        output_file = os.path.abspath(os.path.join(output_path, Path(file).stem + "_page%03d" % (page_number + 1)))
        os.remove(output_file) if os.path.exists(output_file) else None
        return output_file


    def write_bookviewer_file(self, output_path: str, file: str, builder: BookViewerJsonBuilder):
        output_file = self.create_bookviewer_file(
            output_path = output_path, 
            file = file)

        with open(output_file, mode='w+', encoding='utf-8') as writer:
            writer.write(builder.to_json())
    

    def create_bookviewer_file(self, output_path: str, file: str):
        Path(output_path).mkdir(parents=True, exist_ok=True)
        output_file = os.path.abspath(os.path.join(output_path, Path(file).stem + '.json'))
        os.remove(output_file) if os.path.exists(output_file) else None
        return output_file
