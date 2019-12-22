# -*- coding: utf-8 -*-
import requests
import re
import os
import time
import emoji
import pickle

output_dir = "./"
emb_filename1 = os.path.join(output_dir, 'emb_json4.json')
emb_filename2 = os.path.join(output_dir, 'data/emb_json4.pickle')
def give_emoji_free_text(text):
    allchars = [str for str in text]
    emoji_list = [c for c in allchars if c in emoji.UNICODE_EMOJI]
    for i in range(0, len(emoji_list)):
        text = re.sub(emoji_list[i], '', text)

    return text
def get_parse(info, theme):
    print(info)
    # print(res.json()['data']['cards'][1])
    # res = requests.get("https://m.weibo.cn/api/container/getIndex?containerid=102803_ctg1_4888_-_ctg1_4888&openApp=0")
    id = info['mblog']['user']['id']
    gender = info['mblog']['user']['gender']
    mbrank = info['mblog']['user']['mbrank'] #vipç­çş§
    urank = info['mblog']['user']['urank'] #ĺžŽĺç­çş§
    screen_name = info['mblog']['user']['screen_name']
    statuses_count = info['mblog']['user']['statuses_count']
    followers_count = info['mblog']['user']['followers_count']
    text = info['mblog']['text']
    image = info['mblog']['user']['avatar_hd']
    origin_text = text
    pics_list = []

    if 'retweeted_status' in info['mblog']:
        print("It's retweeted tweeter")
        return []

    try:
        for i in range(0, len(info['mblog']['pics'])):
            pics_list.append(info['mblog']['pics'][i]['url'])
    except:
        pics_list = []
    post_id = info['mblog']['id']
    retweet = info['mblog']['reposts_count']
    collect = info['mblog']['attitudes_count']
    user_info = requests.get("https://m.weibo.cn/api/container/getIndex?containerid=230283" + str(id) + "_-_INFO&title=%E5%9F%BA%E6%9C%AC%E8%B5%84%E6%96%99&luicode=10000011&lfid=230283" + str(id))
    company = user_info.json()['data']['cards'][0]['card_group'][2]['item_content']
    try:
        addr = user_info.json()['data']['cards'][1]['card_group'][2]['item_content']
    except:
        addr = user_info.json()['data']['cards'][1]['card_group'][1]['item_content']
    

    isLongText = info['mblog']['isLongText']
    isHash = re.findall(r"#(.*?)#", text, re.M | re.I)
    hash = ""
    if isLongText:
        try:
            text = requests.get("https://m.weibo.cn/statuses/extend?id=" + post_id).json()['data']['longTextContent']
        except:
            print("request_error")
            return []
    if isHash:
        for i in range(0, len(isHash)):
            hash = hash + isHash[i] + ","

    text = give_emoji_free_text(text)
    text = re.sub(r'#|@', '', text) 
    dr = re.compile(r'<[^>]+>',re.S)
    text = dr.sub('',text)
    text = re.sub("[\s+\.\!\/_,$%^*(+\"\')]+|[+——()?【】“”！，。？、~@#￥%……&*（）:-《》：~～]+", "",text)
    ndata = {
    "user":{
        "image": image,
        "id": id,
        "mbrank": mbrank,
        "company": company,
        "gender": gender,
        "addr": addr,
        "urank": urank,
        "screen_name": screen_name,
        "statuses_count": statuses_count,
        "followers_count": followers_count,
    },
    "pics": pics_list,
    "theme": theme,
    "character_count": len(text),
    "retweet_count": retweet,
    "collect_count": collect,
    "origin_text": origin_text,
    "post_id": post_id,
    "text": text,
    "hash": hash
    }

    # data.append(ndata)
    # pickle.dump(ndata,f_pk)
    # json.dump(ndata, f_json, ensure_ascii=False,sort_keys=True, indent=5)
    return ndata

    # print(len(res.json()["data"]["cards"]))
    # print(res.json())



def auto_search():
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
                post_id = res.json()["data"]["cards"][i]['mblog']['user']['id']
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
                        print(post_id)
                        add_tweet = tweeter(character_count = character_count, collect_count = collect_count, 
                                            hash = hash, pics = pics, origin_text = origin_text, post_id = post_id, retweet_count = retweet_count, text = text, theme = theme_, user = user)
                        add_tweet.save()
                else:
                    print("post_id =", post_id, "is already exists")
            time.sleep(10)
        except:
            print("request error")
            time.sleep(10)

# crawl_user("5593273852")

if __name__ == "__main__":
    path =  open('data/emb_json4.pickle','rb')
    post_list = []
    try:
        while True:
            post_list.append(pickle.load(path)['post_id'])
    except:
	    pass
    auto_search(post_list)

    theme_list = [
        {
            "id": 4288,
            "theme": "明星"
        },
        {
            "id": 4388,
            "theme": "搞笑"
        },
        {
            "id": 1988,
            "theme": "情感"
        },
        {
            "id": 4288,
            "theme": "明星"
        },
        {
            "id": 4188,
            "theme": "社会"
        },
        {
            "id": 5088,
            "theme": "数码"
        },
        {
            "id": 1388,
            "theme": "体育"
        },
        {
            "id": 5188,
            "theme": "汽车"
        },
        {
            "id": 3288,
            "theme": "电影"
        },
        {
            "id": 4888,
            "theme": "游戏"
        },
    ]
    # res = requests.get("https://m.weibo.cn/api/container/getIndex?containerid=102803_ctg1_4888_-_ctg1_4888&openApp=0")
    # print(res.json()["data"]["cards"][0]['mblog']['id'])
    # print(res.json()['data']['cards'][2]['mblog']['reposts_count'])
    #https://m.weibo.cn/api/container/getIndex?containerid=102803_ctg1_4288_-_ctg1_4288&openApp=0   明星
    #https://m.weibo.cn/api/container/getIndex?containerid=102803_ctg1_4388_-_ctg1_4388&openApp=0   搞笑
    #https://m.weibo.cn/api/container/getIndex?containerid=102803_ctg1_1988_-_ctg1_1988&openApp=0   情感
    #https://m.weibo.cn/api/container/getIndex?containerid=102803_ctg1_4288_-_ctg1_4288&openApp=0   明星
    #https://m.weibo.cn/api/container/getIndex?containerid=102803_ctg1_4188_-_ctg1_4188&openApp=0   社会
    #https://m.weibo.cn/api/container/getIndex?containerid=102803_ctg1_5088_-_ctg1_5088&openApp=0   数码
    #https://m.weibo.cn/api/container/getIndex?containerid=102803_ctg1_1388_-_ctg1_1388&openApp=0   体育
    #https://m.weibo.cn/api/container/getIndex?containerid=102803_ctg1_5188_-_ctg1_5188&openApp=0   汽车
    #https://m.weibo.cn/api/container/getIndex?containerid=102803_ctg1_3288_-_ctg1_3288&openApp=0   电影
    #https://m.weibo.cn/api/container/getIndex?containerid=102803_ctg1_4888_-_ctg1_4888&openApp=0   游戏
