# -*- coding: utf-8 -*-

import pickle
from SOUWEIBO.models import tweeter
import os
from django.shortcuts import render
from django.http.response import HttpResponse
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
    # path =  open('data/emb_json4.pickle','rb')
    # print("start")
    # try:
    #     while True:
    #         data = pickle.load(path)
    #         print(data['post_id'])
    #         character_count = data['character_count']
    #         collect_count = str(data['collect_count'])
    #         hash = data['hash']
    #         origin_text = data['origin_text']
    #         post_id = data['post_id']
    #         retweet_count = str(data['retweet_count'])
    #         text = data['text']
    #         theme = data['theme']
    #         pics = data['pics']
    #         user = data['user']
    #         if len(tweeter.objects.filter(post_id=post_id)) == 0:
    #             add_tweet = tweeter(character_count = character_count, collect_count = collect_count, 
    #                                 hash = hash, pics = pics, origin_text = origin_text, post_id = post_id, retweet_count = retweet_count, text = text, theme = theme, user = user)
    #             add_tweet.save()
    # except:
    #     pass

    theme_list = [
        {
            "id": 4288,
            "name": "明星"
        },
        {
            "id": 4388,
            "name": "搞笑"
        },
        {
            "id": 1988,
            "name": "情感"
        },
        {
            "id": 4288,
            "name": "明星"
        },
        {
            "id": 4188,
            "name": "社会"
        },
        {
            "id": 5088,
            "name": "数码"
        },
        {
            "id": 1388,
            "name": "体育"
        },
        {
            "id": 5188,
            "name": "汽车"
        },
        {
            "id": 3288,
            "name": "电影"
        },
        {
            "id": 4888,
            "name": "游戏"
        },
    ]
    for theme in theme_list:
        try:
            res = requests.get("https://m.weibo.cn/api/container/getIndex?containerid=102803_ctg1_" + str(theme['id']) + "_-_ctg1_" + str(theme['id']) + "&openApp=0")
            for i in range(0, len(res.json()["data"]["cards"])):
                post_id = res.json()["data"]["cards"][i]['mblog']['id']
                if len(tweeter.objects.filter(post_id=post_id)) == 0:
                    data = get_parse(res.json()["data"]["cards"][i], theme["name"])
                    if data != []:
                        character_count = data['character_count']
                        collect_count = str(data['collect_count'])
                        hash = data['hash']
                        origin_text = data['origin_text']
                        post_id = data['post_id']
                        retweet_count = str(data['retweet_count'])
                        text = data['text']
                        theme_ = data['theme']
                        pics = data['pics']
                        user = data['user']
                        add_tweet = tweeter(character_count = character_count, collect_count = collect_count, 
                                            hash = hash, pics = pics, origin_text = origin_text, post_id = post_id, retweet_count = retweet_count, text = text, theme = theme_, user = user)
                        add_tweet.save()
                        print("post_id =", post_id, "is added")
                else:
                    print("post_id =", post_id, "is already exists")
            time.sleep(10)
            print(theme)
        except:
            print("request error")
            time.sleep(10)

    return HttpResponse("ok")

def search(request, words, page):
    # print(request.POST.get('words'))
    invi = tweeter.objects.filter(theme = words)
    print(len(invi))
    data_list = []
    if len(invi) <= 5:
        for x in invi:
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
            x = invi[i + (page - 1) * 5]
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