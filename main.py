# -*- coding: utf-8 -*-
import sys
import json
import time
import pickle

from relevance import similarity_score
from utils import preprocess, get_candidates, extract_info, query_expansion, overall_score, get_topN_idxs

"""
Q:         query string
algorithm: one of 'bert', 'f1', 'recall', 'bm25'
topN:      number of tweets to return
is_qe:     whether to expand query
additional_attrs: attributes to consider when ranking
return [post_id]
"""
def search(Q_str, algorithm='bert', topN=10, is_qe=True,
           additional_attrs=['retweet_count', 'followers_count']):
    # Query expansion & Preprocess query
    Q_str = '电视剧电影'
    Q = query_expansion(Q_str, 'title', is_qe)
    print('Q', Q)

    # Find tweets that overlaps with keywords of original query
    post_ids = get_candidates(Q)

    # Number of candidate documents is smaller than output number
    if len(post_ids) <= topN:
        return post_ids

    # Load candidate tweets from database
    tweets = load_tweets_from_db(post_ids)

    # Preprocess documents
    if algorithm == 'bert':
        # Extract precalculated embeddings
        D = extract_info(lines, 'vec')
    else:
        # Extract and preprocess texts
        texts = extract_info(lines, 'text')
        D = preprocess(texts)

    # Estimate the degree of similarity between query and documents
    scores = similarity_score(D, Q, algorithm)

    # Compute overall scores including popularity
    overall_scores = overall_score(scores, tweets, ['retweet_count', 'followers_count'])

    # Sort
    topN_idxs = get_topN_idxs(overall_scores, topN)
    result_post_ids = [post_ids[idx] for idx in topN_idxs]
    return result_post_ids

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
    lines=lines[:100]
    algorithm = 'bert'
    for line in lines:
        line['vec'] =  [0.1] * 768

    # query expansion & preprocess query
    orig_Q = '爱情电影'
    Q = query_expansion(orig_Q, 'title', False)
    print('new Q:', Q)

    # Filter irrelevant documents
#   post_ids = get_candidates(orig_Q)
    post_ids = [line['post_id'] for line in lines]

    # Preprocess documents
    if algorithm == 'bert':
        # Extract precalculated embeddings
        D = extract_info(lines, 'vec')
    else:
        # Extract texts
        texts = extract_info(lines, 'text')
        D = preprocess(texts)

    # Return all documents if the number of candidate documents is
    # smaller than output documents number
    topN = 10
    if len(D) <= topN:
        for d in D: print(d)
        results = post_ids
        sys.exit()

    # Estimate the degree of similarity between query and documents
    scores = similarity_score(D, Q, algorithm)

    # Compute overall score including popularity
    overall_scores = overall_score(scores, lines, ['retweet_count', 'followers_count'])
#   overall_scores = overall_score(scores, lines)

    # Sort
    topN_idxs = get_topN_idxs(overall_scores, topN)
    for idx in topN_idxs:
        print(D[idx], overall_scores[idx])
    results = [post_ids[idx] for idx in topN_idxs]
