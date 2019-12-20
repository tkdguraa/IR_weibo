# -*- coding: utf-8 -*-
import json
import pickle

from relevance import relevance_algorithms
from utils import preprocess, get_candidates, get_corpus, query_expansion, overall_score, get_topN_idxs

"""
algorithm is one of 'bert', 'f1', 'recall', 'bm25'
Q = ['query']
return [post_id]
"""
def search(Q, algorithm='bert', topN=10):
    # query expansion & preprocess query
    orig_Q = ['电视剧电影韩国']
    Q = query_expansion(orig_Q, 'title', True)
    print('Q', Q)

    # find tweets that overlaps with keywords of original query
    post_ids = get_candidates(Q)
    # FIXME: LiXiangHe needs to implement load_tweets_from_db
    # tweets = [dict]
    tweets = load_tweets_from_db(post_ids)

    # extract useful information
    texts = [tweet['text'] for tweet in tweets]
    mbranks = [tweet['user']['mbrank'] for tweet in tweets]
    uranks = [tweet['user']['urank'] for tweet in tweets]

    # preprocess texts
    D = preprocess(texts)

    # number of candidate documents is smaller than output documents number
    if len(D) <= topN:
        return  post_ids

    # estimate the degree of similarity between query and documents
    relevance_algorithm = relevance_algorithms[algorithm]
    scores = relevance_algorithm(D, Q)

    # compute overall scores including popularity
    overall_scores = overall_score(scores, mbranks, uranks)

    # sort
    topN_idxs = get_topN_idxs(overall_scores, topN)
    results = [post_ids[idx] for idx in topN_idxs]
    return results

if __name__ == '__main__':
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
    orig_Q = ['电视剧电影韩国']
    Q = query_expansion(orig_Q, 'title', True)
    print('Q', Q)

    # filter irrelevant documents
#    post_ids = get_candidates(orig_Q)
    post_ids = [line['post_id'] for line in lines]
    D, mbranks, uranks = get_corpus(post_ids, D, lines)

    topN = 5    # num of documents to return
    # number of candidate documents is smaller than output documents number
    if len(D) <= topN:
        for d in D: print(d)
        results = post_ids
    else:
        # Estimate the degree of similarity between query and documents
        scores = relevance_algorithms['bert'](D, Q)

        overall_scores = overall_score(scores, mbranks, uranks)

        # sort
        topN_idxs = get_topN_idxs(overall_scores, topN)
        for idx in topN_idxs:
            print(D[idx], overall_scores[idx])
        results = [post_ids[idx] for idx in topN_idxs]
