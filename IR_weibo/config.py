# -*- coding: utf-8 -*-
import argparse as ap


parser = ap.ArgumentParser()
parser.add_argument('--inverted_index_path', default='../IR_weibo/indexfile/invertedIndex.txt', help='Data path for inverted indexfile.', type=str)
parser.add_argument('--tag_index_path', default='../IR_weibo/indexfile/tagIndex.txt', help='Data path for tag indexfile.', type=str)
parser.add_argument('--new_inverted_index', default=False, action="store_true", help='If start a new inverted indexfile.')
parser.add_argument('--new_tag_index', default=False, action="store_true", help='If start a new tag indexfile.')
parser.add_argument('--extract_keywords', action="store_true", default=False, help='when cut words, extracting words or not.')
parser.add_argument('-r', '--relevance', default='bm25', help='method to calculate relevance', type=str)
# parser.add_argument('runserver', default=False, help='')
# bm25, f1score, recall, bert + cossin

args, _ = parser.parse_known_args()
# print(args)