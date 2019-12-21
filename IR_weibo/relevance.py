# -*- coding: utf-8 -*-
import sys
sys.path.append('../')

import math
import jieba
from collections import Counter
from scipy.spatial import distance
from bert_serving.client import BertClient

class BERT_embedding(object):
    def __init__(self):
        self.bc = BertClient(ip='166.111.80.50')

    """
    Feature Extraction
    convert document to vector
    """
    def encoder(self, D):
        D_vectors = self.bc.encode(D)
        return D_vectors

    """
    Compute cosine similarity
    The score ranges from 0 to 2. 2 means most similar
    """
    def cosine_similarity(self, D_vectors, Q_vector):
        return [2 - distance.cosine(d_vector, Q_vector) for d_vector in D_vectors]

    def score(self, doc_tokens, query_tokens):
        D = [' '.join(tokens) for tokens in doc_tokens]
        Q = [' '.join(query_tokens)]
        D_vectors = self.encoder(D)
        Q_vector = self.encoder(Q)
        return self.cosine_similarity(D_vectors, Q_vector)

def BERT_score(doc_tokens, query_tokens):
    bert = BERT_embedding()
    scores = bert.score(doc_tokens, query_tokens)
    return scores


class BM25(object):
    def __init__(self, docs):
        self.D = len(docs)
        self.avgdl = sum([len(doc) + 0.0 for doc in docs]) / self.D
        self.docs = docs
        self.f = list()  # 列表的每一个元素是一个dict，dict存储着一个文档中每个词的出现次数
        self.df = dict() # 存储每个词及出现了该词的文档数量
        self.idf = dict() # 存储每个词的idf值
        self.k1 = 1.5
        self.b = 0.75
        self.init()

    def init(self):
        for doc in self.docs:
            tmp = dict()
            for word in doc:
                tmp[word] = tmp.get(word, 0) + 1  # 存储每个文档中每个词的出现次数
            self.f.append(tmp)
            for k in tmp.keys():
                self.df[k] = self.df.get(k, 0) + 1 # 存储每个词在几篇文档中出现
        for k, v in self.df.items():
            self.idf[k] = math.log(self.D - v + 0.5) - math.log(v + 0.5)
        #print(self.f)
        #print(self.df)
        #print(self.idf)

    def sim(self, query, index):
        # 简化算法， (k2+1)*qfi/(k2+qfi)  qfi为查询词在query中的词频，
        score = 0
        for word in query:
            if word not in self.f[index]:
                continue
            d = len(self.docs[index])
            score += (self.idf[word] * self.f[index][word] * (self.k1 + 1)
                      / (self.f[index][word] + self.k1 * (1 - self.b + self.b * d
                                                      / self.avgdl)))
        return score

    # 总共有N篇文档，传来的doc为query，计算query与所有推文匹配
    # 后的得分score，总共有多少篇推文，scores列表就有多少项，
    # 每一项为推文与query的相似度得分
    def simall(self, query):
        scores = list()
        for i in range(self.D):
            score = self.sim(query, i)
            scores.append(score)
        return scores


def bm25(doc_tokens, query_tokens):
    bm = BM25(doc_tokens)
    scores = bm.simall(query_tokens)
    return scores



def precision_recall_f1(prediction, ground_truth):
    """
    This function calculates and returns the precision, recall and f1-score
    Args:
        prediction: prediction string or list to be matched，here it means the query
        ground_truth: golden string or list reference, here it means the doc
    Returns:
        floats of (p, r, f1)
    Raises:
        None
    """
    if not isinstance(prediction, list):
        prediction_tokens = prediction.split()
    else:
        prediction_tokens = prediction
    if not isinstance(ground_truth, list):
        ground_truth_tokens = ground_truth.split()
    else:
        ground_truth_tokens = ground_truth
    common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return 0, 0, 0
    p = 1.0 * num_same / len(prediction_tokens)
    r = 1.0 * num_same / len(ground_truth_tokens)
    f1 = (2 * p * r) / (p + r)
    return p, r, f1


def f1_score(doc_tokens, query_tokens):
    scores = list()
    if len(query_tokens) > 0:
        for dt in doc_tokens:
            related_score = precision_recall_f1(dt, query_tokens)[2]
            scores.append(related_score)
    return scores


def recall(doc_tokens, query_tokens):
    scores = list()
    if len(query_tokens) > 0:
        for dt in doc_tokens:
            related_score = precision_recall_f1(dt, query_tokens)[1]
            scores.append(related_score)
    return scores


def  similarity_score(D, Q, algorithm):
    func = None
    if algorithm == 'bert':
        func = BERT_score
    elif algorithm == 'bm25':
        func = bm25
    elif algorithm == 'f1':
        func = f1_score
    else:
        func = recall

    return func(D, Q)


if __name__ == "__main__":
    query = "关晓彤和吴刚是什么关系"
    D = dict()
    w1 = '关晓彤吴刚同框# #关晓彤渐变抹胸裙# 第六届中国电视好演员年度盛典红毯，“国民好书记”@吴刚de微博 与“国民闺女”@关晓彤 同框啦~闺女今天这身裙子好漂亮[舔屏]'
    w2 = '#新鲜事每日精选# 小鲜今日推荐新鲜事top3：\
    德国总理默克尔在德国联邦议院上重申，反对将华为公司排除在5G网络建设范围之外，她赞成尽一切努力确保网络安全，华为不仅在德国，在欧洲其他国家都参与了第二、第三和第四代网络建设。中国力量加油[加油]\
    1.@扬帆向北 新鲜事，《5G动态追踪》传送门➡http://t.cn/EbY47Yz\
    2.@微博房产报道 新鲜事，《致敬时代力量2019微博房产影响力峰会圆满举行》传送门➡http://t.cn/AiDe1UK7\
    3.@UXlab 新鲜事，《优秀UI设计都在这儿》传送门➡http://t.cn/Rm5iPWW'
    w3 = '吴刚哈时间的话卡死， hello, hahahha, 哈哈哈'
    query_tokens = jieba.lcut_for_search(query)
    # ['关键系'， 'sdfs']
    w1_tokens = jieba.lcut_for_search(w1)
    w2_tokens = jieba.lcut_for_search(w2)
    w3_tokens = jieba.lcut_for_search(w3)
    '''
    print(w1_tokens)
    print(w2_tokens)
    print(w3_tokens)
    '''

    doc_tokens = list()
    doc_tokens.append(w1_tokens)
    doc_tokens.append(w2_tokens)
    doc_tokens.append(w3_tokens)
    # [['fsdfs','sdfs'], []]
    # [121,42342]
    f1 = f1_score(doc_tokens, query_tokens)
    recall_score = recall(doc_tokens, query_tokens)
    bm25_score = bm25(doc_tokens, query_tokens)
    print(f1)
    print(recall_score)
    print(bm25_score)

