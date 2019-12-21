# -*- coding: utf-8 -*-
import sys
sys.path.append('../')
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
def search(Q_str, algorithm='bert', topN=10, is_qe=False,
           additional_attrs=['retweet_count', 'followers_count']):
    # query expansion & preprocess query
    Q_str = '电视剧电影'
    Q = query_expansion(Q_str, 'title', is_qe)
    print('Q', Q)

    # find tweets that overlaps with keywords of original query
    post_ids = get_candidates(Q)
    # FIXME: LiXiangHe needs to implement load_tweets_from_db
    # tweets = [dict]
    tweets = load_tweets_from_db(post_ids)

    # extract text
    texts = extract_info(tweets, 'text')

    # preprocess texts
    D = preprocess(texts)

    # number of candidate documents is smaller than output documents number
    if len(D) <= topN:
        return  post_ids

    # estimate the degree of similarity between query and documents
    scores = similarity_score(D, Q, algorithm)

    # compute overall scores including popularity
    overall_scores = overall_score(scores, tweets, ['retweet_count', 'followers_count'])

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
    lines = lines[:1000]

    # from dict to list
    texts = [line['text'] for line in lines]

    # preprocess documents
    D = preprocess(texts)

    # query expansion & preprocess query
    orig_Q = '爱情电影'
    Q = query_expansion(orig_Q, 'title', False)
    print('new Q:', Q)

    # filter irrelevant documents
#    post_ids = get_candidates(orig_Q)
    post_ids = [line['post_id'] for line in lines]

    topN = 10    # num of documents to return
    # number of candidate documents is smaller than output documents number
    if len(D) <= topN:
        for d in D: print(d)
        results = post_ids
    else:
        # Estimate the degree of similarity between query and documents
        scores = similarity_score(D, Q, 'f1')

        # Compute overall score including popularity
        overall_scores = overall_score(scores, lines, ['retweet_count', 'followers_count'])
#        overall_scores = overall_score(scores, lines)

        # sort
        topN_idxs = get_topN_idxs(overall_scores, topN)
        for idx in topN_idxs:
            print(D[idx], overall_scores[idx])
        results = [post_ids[idx] for idx in topN_idxs]
