# -*- coding: utf-8 -*-
import sys
sys.path.append('..')

from SOUWEIBO.models import tweeter
import os
from django.shortcuts import render
from django.http.response import HttpResponse
import json
os.environ['DJANGO_SETTINGS_MODULE'] = 'SOUMBLOG.settings'
from IR_weibo.relevance import similarity_score
from IR_weibo.utils import preprocess, get_candidates, extract_info, query_expansion, overall_score, get_topN_idxs


"""
main search algorithm
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
    Q = query_expansion(Q_str, 'title', is_qe)
    print('Q', Q)

    # find tweets that overlaps with keywords of original query
    # TODO
    post_ids = get_candidates(Q)
    print("before", post_ids)
    print("ss",get_candidates(["足球"]))
    invi = tweeter.objects.limit(1000)
    post_ids = []
    for i in range(0,1000):
        obj = invi[i]
        post_ids.append(obj['post_id'])
    # print(type(post_ids[0]))
    # num = tweeter.objects.filter(post_id=str(post_ids[0]))
    # print("www", len(num))
    # print("posts", post_ids)

    tweets = load_tweets_from_db(post_ids)
    print("len(tweets)", len(tweets))
    # extract text
    texts = extract_info(tweets, 'text')

    # preprocess texts
    D = preprocess(texts)

    # number of candidate documents is smaller than output documents number
    print("len(D)", len(D))
    if len(D) <= topN:
        topN = len(D)

    # estimate the degree of similarity between query and documents
    scores = similarity_score(D, Q, algorithm)

    # compute overall scores including popularity
    # overall_scores = overall_score(scores, tweets, ['retweet_count', 'followers_count'])
    overall_scores = scores #temp
    # sort
    topN_idxs = get_topN_idxs(overall_scores, topN)
    results = [post_ids[idx] for idx in topN_idxs]
    return results

# Create your views here.
def search_interface(request):
    return render(request, 'SOUWEIBO/search_interface.html', {'datas': [], 'number': 0})


def update_data(request):
    #这里写倒排文档等更新函数
    return HttpResponse("ok")

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

def click_search(request, words, page):
    # print(request.POST.get('words'))

    invi = search(words, algorithm='bm25', topN=10, is_qe=False)

    print(len(invi))
    data_list = []
    if len(invi) <= 5:
        for post_id in invi:
            x = tweeter.objects.filter(post_id = post_id)[0]
            data = {
                "character_count": x['character_count'],
                "like": x['collect_count'],
                "hash": x['hash'],
                "origin_text": x['origin_text'],
                "post_id": x['post_id'],
                "retweet_count": x['retweet_count'],
                "text": x['text'],
                "theme": x['theme'],
                "pics": x['pics'],
                "user": x['user'],
                "search": words,
            }
            data_list.append(data)
    else:
        for i in range(0, 5):
            post_id = invi[i + (page - 1) * 5]
            x = tweeter.objects.filter(post_id = post_id)[0]
            data = {
                "character_count": x['character_count'],
                "like": x['collect_count'],
                "hash": x['hash'],
                "origin_text": x['origin_text'],
                "post_id": x['post_id'],
                "retweet_count": x['retweet_count'],
                "text": x['text'],
                "theme": x['theme'],
                "pics": x['pics'],
                "user": x['user'],
                "search": words,
            }
            data_list.append(data)

    return render(request, 'SOUWEIBO/search_interface.html', {'datas': json.dumps(data_list), 'number': len(invi)})


if __name__ == "__main__":
    update_data('qwq')