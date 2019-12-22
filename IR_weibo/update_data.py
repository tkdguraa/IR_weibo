# -*- coding: utf-8 -*-
import sys
sys.path.append('../')

from pymongo import MongoClient
import time
import pickle
import requests
from IR_weibo.relevance import BERT_embedding
from IR_weibo.inverted_index import InvertedIndex, TagIndex
from IR_weibo.crawler_theme import get_parse

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

#实时爬取数据
def update_data(tweeter):

    invertedIndex = InvertedIndex(newIndex=False)
    tagIndex = TagIndex(newIndex=False)
    bert = BERT_embedding()

    for theme in theme_list:
        print('Search for %s' %theme['name'])
        tag_dict = {}
        text_dict = {}
        user_dict = {}
        try:
            res = requests.get("https://m.weibo.cn/api/container/getIndex?containerid=102803_ctg1_" + str(theme['id']) + "_-_ctg1_" + str(theme['id']) + "&openApp=0")
            for i in range(0, len(res.json()["data"]["cards"])):
                post_id = res.json()["data"]["cards"][i]['mblog']['id']
                if tweeter.find(filter={'post_id':post_id}).count() == 0:
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
                        if tweeter.find(filter={'post_id': post_id}).count() == 0:
                            D_vector = bert.encoder([text])[0].tolist()
                            tweeter.insert_one({'character_count': character_count, 'collect_count': collect_count,
                                            'hash': hash, 'pics': pics, 'origin_text': origin_text,
                                            'post_id': post_id, 'retweet_count': retweet_count, 'text': text,
                                            'theme': theme_, 'user': user, 'vec': D_vector})

                            text_dict[post_id] = text #D={key: value}, key:在数据库中该微博的序号， value:文本
                            tag_dict[post_id] = hash #D={key: value}, key:在数据库中该微博的序号， value:tags
                            user_dict[user['screen_name']] = user['followers_count']
                        print("Post_id =", post_id, "is added.")
                        print(tweeter.count())
                else:
                    print("Post_id =", post_id, "already exists")
            time.sleep(10)
        except:
            print("request error")
            time.sleep(10)

        # update index
        print("Tweeter count: %d" % tweeter.count_documents({}))
        invertedIndex.update_invert_index(text_dict)
        tagIndex.update_tag_index(tag_dict)
        print("Inverted index length: %d" % len(invertedIndex.inverted_index))
        print("Tag index length: %d" % len(tagIndex.tag_index))
        # print(invertedIndex.inverted_index)
        # print(tagIndex.tag_index)



#直接读取data文件夹里的pickle文件到数据库
def read_data(tweeter):
    invertedIndex = InvertedIndex(newIndex=True)
    tagIndex = TagIndex(newIndex=True)

    path =  open('tweets_with_embeddings.pickle','rb')
    text_dict = {}
    tag_dict = {}
    user_dict = {}

    try:
        while True:
            data = pickle.load(path)
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
            D_vector = data['vec'].tolist()
            if tweeter.count_documents(filter={'post_id':post_id}) == 0:
                tweeter.insert_one({'character_count': character_count, 'collect_count': collect_count,
                                'hash': hash, 'pics': pics, 'origin_text': origin_text,
                                'post_id': post_id, 'retweet_count': retweet_count, 'text': text,
                                'theme': theme_, 'user': user, 'vec': D_vector})
                text_dict[post_id] = text
                tag_dict[post_id] = hash
                user_dict[user['screen_name']] = user['followers_count']
                # print(text_dict)
    except:
        pass

    # update index
    print("Tweeter count: %d" %tweeter.count_documents({}))
    invertedIndex.update_invert_index(text_dict)
    tagIndex.update_tag_index(tag_dict)
    print("Inverted index length: %d" %len(invertedIndex.inverted_index))
    print("Tag index length: %d" % len(tagIndex.tag_index))
    # print(invertedIndex.inverted_index)
    # print(tagIndex.tag_index)


if __name__ == "__main__":
    #建立MongoDB数据库连接
    client = MongoClient('localhost',27017)

    #连接所需数据库,test为数据库名
    db=client.weibodata

    #连接所用集合，也就是我们通常所说的表，test为表名

    collection=db.tweeter

    # for item in collection.find():
    # print(collection.count())
    read_data(collection)

    while 1:
        update_data(collection)
        time.sleep(300)
