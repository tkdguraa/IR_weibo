import pickle
from SOUWEIBO.models import tweeter
import os
from django.shortcuts import render
from django.http.response import HttpResponse
from SOUMBLOG.SOUWEIBO.search_engine import get_result
import json
import time
import requests
import _thread
os.environ['DJANGO_SETTINGS_MODULE'] = 'SOUMBLOG.settings'
from SOUWEIBO.crawler_theme import auto_search
from SOUWEIBO.crawler_theme import get_parse


# Create your views here.
def search_interface(request):
    return render(request, 'SOUWEIBO/search_interface.html', {'datas': [], 'number': 0})


def update_data(request):
    #这里写倒排文档等更新函数
    return HttpResponse("ok")

def get_complete_data(post_id):
    invi = tweeter.objects.filter(post_id = post_id)
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
    }
    print(invi[0])
    return data

def search(request, words, page):
    # print(request.POST.get('words'))
    invi = get_result(words,topN=100)
    invi = tweeter.objects.filter(theme = words)
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


