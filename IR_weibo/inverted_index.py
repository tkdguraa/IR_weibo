# -*- coding: utf-8 -*-
import sys
sys.path.append('../')

import jieba
from jieba import analyse
import json, datetime
from IR_weibo.config import args
import numpy as np
import os


class InvertedIndex:

    def __init__(self, indexPath=args.inverted_index_path, newIndex = args.new_inverted_index):
        # load stopwords
        self.stopwords = [line.strip() for line in open('../IR_weibo/stopwords.txt', encoding='UTF-8').readlines()]
        self.inverted_index = dict()
        self.indexPath = indexPath

        try:
            if not newIndex:
                print('Load a old inverted index')
                if os.path.exists(indexPath):
                    with open(indexPath, 'r') as fin:
                        self.inverted_index = json.load(fin)
            else:
                print('Start a new inverted index')
        except Exception as e:
            self.inverted_index = dict()


    def save_index(self):
        with open(self.indexPath, 'w') as fout:
            json.dump(self.inverted_index, fout, ensure_ascii=False)


    def cut_words(self, D):

        forward_index = dict()
        for i in D:
            if args.extract_keywords:
                tmp = analyse.extract_tags(D[i], topK=20)
            else:
                tmp = jieba.lcut_for_search(D[i])
            forward_index.setdefault(i, [w.strip() for w in tmp if w not in self.stopwords and len(w.strip()) > 0])
        return forward_index


    def update_invert_index(self, D):
        forward_index = self.cut_words(D)
        for i in forward_index:
            for word in forward_index[i]:
                if word not in self.inverted_index:
                    self.inverted_index[word] = [i]
                elif i not in self.inverted_index[word]:
                    self.inverted_index[word].append(i)

        self.save_index()

    def search(self, Q):
        res = set()
        for q in Q:
            if q in self.inverted_index:
                res.update(self.inverted_index[q])
        res = list(res)
        res.sort(reverse=True)
        return res

    # def update(self):


class TagIndex:

    def __init__(self, indexPath=args.tag_index_path, newIndex = args.new_tag_index):
        self.tag_index = dict()
        self.indexPath = indexPath
        try:
            if not newIndex:
                print('Load a old tag index')
                if os.path.exists(indexPath):
                    with open(indexPath, 'r') as fin:
                        self.tag_index = json.load(fin)
            else:
                print('Start a new tag index')
        except Exception as e:
            self.tag_index = dict()

    def update_tag_index(self, D):
        for i in D:
            wordlist = D[i].split(',')
            for word in wordlist:
                if word.strip() == '':
                    continue
                if word not in self.tag_index:
                    self.tag_index[word] = [i]
                elif i not in self.tag_index[word]:
                    self.tag_index[word].append(i)

        self.save_index()

    def save_index(self):
        with open(self.indexPath, 'w') as fout:
            json.dump(self.tag_index, fout, ensure_ascii=False)

    def search(self, Q):
        res = set()
        for q in Q:
            if q in self.tag_index:
                res.update(self.tag_index[q])
        res = list(res)
        res.sort(reverse=True)
        return res



class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, datetime):
            return obj.__str__()
        else:
            return super(self).default(obj)


if __name__ == '__main__':
    # print(args.extract_keywords)
    invertedIndex = InvertedIndex(indexPath='indexfile/test_inverted.txt')
    tagIndex = TagIndex(indexPath='indexfile/test_tag.txt')
    D = dict()
    D.setdefault('0', '关晓彤吴刚同框# #关晓彤渐变抹胸裙# 第六届中国电视好演员年度盛典红毯，“国民好书记”@吴刚de微博 与“国民闺女”@关晓彤 同框啦~闺女今天这身裙子好漂亮[舔屏]')
    D.setdefault('1', '#新鲜事每日精选# 小鲜今日推荐新鲜事top3：\
德国总理默克尔在德国联邦议院上重申，反对将华为公司排除在5G网络建设范围之外，她赞成尽一切努力确保网络安全，华为不仅在德国，在欧洲其他国家都参与了第二、第三和第四代网络建设。中国力量加油[加油]\
1.@扬帆向北 新鲜事，《5G动态追踪》传送门➡http://t.cn/EbY47Yz\
2.@微博房产报道 新鲜事，《致敬时代力量2019微博房产影响力峰会圆满举行》传送门➡http://t.cn/AiDe1UK7\
3.@UXlab 新鲜事，《优秀UI设计都在这儿》传送门➡http://t.cn/Rm5iPWW')
    D.setdefault('2', '关晓彤， 哈时间的话卡死， hello, hahahha, 哈哈哈')
    invertedIndex.update_invert_index(D)

    D2=dict()
    D2.setdefault('0', '关晓彤,鹿晗,')
    D2.setdefault('1', '关晓彤,鹿晗')
    D2.setdefault('2', '')
    D2.setdefault('3', ',')
    tagIndex.update_tag_index(D2)
    print(invertedIndex.inverted_index)
    print(tagIndex.tag_index)
    print(invertedIndex.search(['关晓彤']))
    # vec = [121.212, 212.121,121.212]
    # vecstr = "/".join(map(str, vec))
    # print(vecstr)
    # vecRestore = list(map(float, vecstr.split('/')))
    # print(vecRestore)

