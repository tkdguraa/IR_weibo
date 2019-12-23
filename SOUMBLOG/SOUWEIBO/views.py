# -*- coding: utf-8 -*-

import sys
sys.path.append('..')

from SOUWEIBO.models import tweeter
import os
from django.shortcuts import render
from django.http.response import HttpResponse
import json
import jieba
os.environ['DJANGO_SETTINGS_MODULE'] = 'SOUMBLOG.settings'
from IR_weibo.relevance import similarity_score
from IR_weibo.utils import preprocess, preprocess_query, get_candidates, get_candidates_tag, extract_info, query_expansion, overall_score, get_topN_idxs


"""
Main search algorithm
Q:         query string
algorithm: one of 'bert', 'f1', 'recall', 'bm25'
topN:      number of tweets to return
is_qe:     whether to expand query
additional_attrs: attributes to consider when ranking
attr_params: weights of additional attributes
"""
def search(Q_str, algorithm='bert', topN=50, is_qe=False,
           additional_attrs=['retweet_count', 'followers_count', 'post_id'],
           attr_params=[0.1, 0.1, 0.1]):
    # Query expansion & preprocess query
    Q = preprocess_query(Q_str, jieba.lcut_for_search)
    print('Q: ', Q)

    # Find tweets that overlaps with keywords of original query
    post_ids = get_candidates(list(Q))

    # print("before", post_ids)

    # print(type(post_ids[0]))
    # num = tweeter.objects.filter(post_id=str(post_ids[0]))
    # print("www", len(num))
    # print("posts", post_ids)

    tweets = load_tweets_from_db(post_ids)
    print("len(tweets)", len(tweets))

    # Preprocess documents
    if algorithm == 'bert':
        # Extract precalculated embeddings
        D = extract_info(tweets, 'vec')
    else:
        # Extract and preprocess texts
        texts = extract_info(tweets, 'text')
        D = preprocess(texts, jieba.lcut_for_search)

    # Estimate the degree of similarity between query and documents
    if is_qe:
        Q = query_expansion(Q_str, jieba.lcut_for_search, info_type='title', max_q_token_len=10)
    scores = similarity_score(D, Q, algorithm)

    # Compute overall scores including popularity
    overall_scores = overall_score(scores, tweets, additional_attrs, attr_params)
    # overall_scores = scores

    # Number of candidate documents is smaller than output documents number
    if len(overall_scores) <= topN:
        topN = len(overall_scores)

    # Sort
    topN_idxs = get_topN_idxs(overall_scores, topN)
    results = [tweets[idx] for idx in topN_idxs]

    print('sim scores:', [overall_scores[idx] for idx in topN_idxs])

    return results


def search_tag(Q_str, topN=50):
    post_ids = get_candidates_tag([Q_str])
    tweets = load_tweets_from_db(post_ids)
    print("len(tweets)", len(tweets))
    return tweets[:topN]


def search_interface(request):
    info = dict()
    info['search'] = ''
    info['divided'] = ''
    info['type'] = 'normal'
    return render(request, 'SOUWEIBO/search_interface.html', {'datas': [], 'number': 0,'info': info})


def load_tweets_from_db(post_id):
    data_list = []
    for id in post_id:
        invi = tweeter.objects.filter(post_id = id)[0]
        data = {
                "character_count": invi['character_count'],
                "like": invi['collect_count'],
                "hash": invi['hash'],
                "origin_text": invi['origin_text'],
                "post_id": invi['post_id'],
                "retweet_count": invi['retweet_count'],
                "text": invi['text'],
                "theme": invi['theme'],
                "pics": invi['pics'],
                "user": invi['user'],
                "vec": invi['vec'],
            }
        data_list.append(data)
    return data_list


def click_search(request, words, type):
    if type == 'tag':
        print("search TAG")
        invi = search_tag(words)
        print("Search results: %d data" % len(invi))
        Q = words
    else:
        print("search NORMAL")

        """
        Main Weibo Search API
        """
        invi = search(words, algorithm='bert', topN=50, is_qe=False,
                      additional_attrs=['retweet_count', 'followers_count', 'post_id'],
                      attr_params=[0.1, 0.1, 0.1])

        Q = preprocess_query(words, jieba.lcut_for_search)

        Q.sort(key = lambda i:len(i),reverse=True)
        print("Search results: %d data" % len(invi))

    data_list = []
    for x in invi:
        data = x
        data['search'] = words
        data['divided'] = Q
        data['type'] = type
        del data['vec']
        data_list.append(data)

    info = dict()
    info['search'] = words
    info['divided'] = Q
    info['type'] = type

    return render(request, 'SOUWEIBO/search_interface.html', {'datas': json.dumps(data_list), 'number': len(invi), 'info': info})


def page_not_found(request,exception):
    return render(request, 'SOUWEIBO/page404.html')


if __name__ == "__main__":
    pass
