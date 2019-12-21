# -*- coding: utf-8 -*-
import argparse as ap

parser = ap.ArgumentParser()
parser.add_argument('--inverted_index_path', default='./index/invertedIndex.txt', help='Data path for inverted index.', type=str)
parser.add_argument('--tag_index_path', default='./index/tagIndex.txt', help='Data path for tag index.', type=str)
parser.add_argument('--load_inverted_index', default=False, help='If load old inverted index.')
parser.add_argument('--load_tag_index', default=False, help='If load old tag index.')
parser.add_argument('--extract_keywords', action="store_true", default=False, help='when cut words, extracting words or not.')
parser.add_argument('-r', '--relevance', default='bm25', help='method to calculate relevance', type=str)
# bm25, f1score, recall, cossin, bert, correlation
args = parser.parse_args()
# print(args)