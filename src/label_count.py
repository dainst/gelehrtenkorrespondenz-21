#!/usr/bin/env python3

import argparse
import re
from collections import defaultdict
import glob

from data_access.webanno_tsv import webanno_tsv_read_file

TARGET_LAYER = 'webanno.custom.LetterEntity'
TARGET_FIELD = 'value'


def main(args):
    label_counts = defaultdict(int)
    for path in sorted(glob.glob(args.directory + '/*.tsv')):
        doc = webanno_tsv_read_file(path)
        for annotation in doc.annotations_with_type(TARGET_LAYER, TARGET_FIELD):
            label_counts[annotation.label] += 1
    label_counts['SUM'] = sum(label_counts.values())

    for label, count in sorted(label_counts.items(), key=lambda i: i[1]):
        print('% 6d - %s' % (count, label))


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Print counts of annotations in tsv files in directory.')
    parser.add_argument('directory', type=str, help='Directory to look for .tsv files in.')
    main(parser.parse_args())
