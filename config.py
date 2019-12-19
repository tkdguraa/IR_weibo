# -*- coding: utf-8 -*-
import argparse as ap

parser = ap.ArgumentParser()
parser.add_argument('--inverted_index_path', default='./index/invertedIndex.txt', help='Data path for inverted index.', type=str)
parser.add_argument('--tag_index_path', default='./index/tagIndex.txt', help='Data path for tag index.', type=str)
# parser.add_argument('--saved_index_path', default='./index/saved_index.txt', help='Data path for inverted index.', type=str)
parser.add_argument('--extract_keywords', action="store_true", default=False, help='when cut words, extracting words or not.')

args = parser.parse_args()
print(args)