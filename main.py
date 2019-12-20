# -*- coding: utf-8 -*-
import json
import pickle

from relevance import BERT_score, f1_score, recall, bm25
from utils import preprocess, remove_no_overlap, leave_useful_info, query_expansion, overall_score, get_topN_idxs


if __name__ == '__main__':
    # for test
    with open('tweets.pickle', 'rb') as f:
        lines = []
        while True:
            try:
                line = pickle.load(f)
            except EOFError:
                break
            lines.append(line)
    print(len(lines))

    # from dict to list
    texts = [line['text'] for line in lines]

    # preprocess documents
    D = preprocess(texts)

    # query expansion & preprocess query
    orig_Q = ['男女爱情剧']
    Q = query_expansion(orig_Q, 'title', True)
    Q = set(preprocess(Q)[0])
    print('Q', Q)

    # filter irrelevant documents
    useful_idxs = remove_no_overlap(orig_Q, D)
    D, post_ids, mbranks, uranks = leave_useful_info(useful_idxs, D, lines)
    print('D', D)
    print('=====')

    topN = 5    # num of documents to return
    # number of candidate documents is smaller than output documents number
    if len(D) <= topN:
        for d in D: print(d)
        results = post_ids
    else:
        # Estimate the degree of similarity between query and documents
        scores = BERT_score(D, Q)
#        scores = bm25(D, Q)
#        scores = f1_score(D, Q)
#        scores = recall(D, Q)

        overall_scores = overall_score(scores, mbranks, uranks)

        # sort
        topN_idxs = get_topN_idxs(overall_scores, topN)
        for idx in topN_idxs:
            print(D[idx], overall_scores[idx])
        results = [post_ids[idx] for idx in topN_idxs]
