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
from IR_weibo.utils import preprocess, get_candidates, get_candidates_tag, extract_info, query_expansion, overall_score, get_topN_idxs


"""
main search algorithm
Q:         query string
algorithm: one of 'bert', 'f1', 'recall', 'bm25'
topN:      number of tweets to return
is_qe:     whether to expand query
additional_attrs: attributes to consider when ranking
return [post_id]
"""
def search(Q_str, algorithm='bert', topN=50, is_qe=False,
           additional_attrs=['retweet_count', 'followers_count']):
    # Query expansion & preprocess query
    Q = query_expansion(Q_str, jieba.lcut_for_search, 'title', is_qe)
    print('Q', Q)

    # Find tweets that overlaps with keywords of original query
    post_ids = get_candidates(list(Q))
    print("before", post_ids)

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
    scores = similarity_score(D, Q, algorithm)

    # Compute overall scores including popularity
    # overall_scores = overall_score(scores, tweets, ['retweet_count', 'followers_count'])
    overall_scores = scores #FIXME

    # Number of candidate documents is smaller than output documents number
    print("len(scores)", len(overall_scores))
    if len(overall_scores) <= topN:
        topN = len(overall_scores)

    # Sort
    topN_idxs = get_topN_idxs(overall_scores, topN)
    results = [tweets[idx] for idx in topN_idxs]
    return results


def search_tag(Q_str, topN=50):
    post_ids = get_candidates_tag([Q_str])
    tweets = load_tweets_from_db(post_ids)
    print("len(tweets)", len(tweets))
    return tweets[:topN]


def search_interface(request):
    return render(request, 'SOUWEIBO/search_interface.html', {'datas': [], 'number': 0})


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


def click_search(request, words, page, type):
    # print(request.POST.get('words'))
    if type == 'tag':
        print("search TAG")
        invi = search_tag(words)
        print("Search results: %d data" % len(invi))
        Q = words

    else:
        print("search NORMAL")
        invi = search(words, algorithm='bert', topN=10, is_qe=False)
        Q = query_expansion(words, jieba.lcut_for_search, 'title', False) #获取搜索输入的分词集
        Q = list(Q)
        # print("before sort", Q)
        Q.sort(key = lambda i:len(i),reverse=True)
        # print("after sort", Q)
        print("Search results: %d data" % len(invi))

    data_list = []
    if len(invi) <= 5:
        for x in invi:
            data = x
            data['search'] = words
            data['divided'] = Q
            data['type'] = type
            data_list.append(data)
    else:
        for i in range((page - 1) * 5, (page - 1) * 5 + 5):
            # post_id = invi[i + (page - 1) * 5]
            # x = tweeter.objects.filter(post_id = post_id)[0]
            data = invi[i]
            data['search'] = words
            data['divided'] = Q
            data['type'] = type
            data_list.append(data)

    return render(request, 'SOUWEIBO/search_interface.html', {'datas': json.dumps(data_list), 'number': len(invi)})


def page_not_found(request,exception):
    return render(request, 'SOUWEIBO/page404.html')


if __name__ == "__main__":
    pass
