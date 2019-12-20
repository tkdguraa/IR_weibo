# -*- coding: utf-8 -*-
import json
import pickle
import requests
from math import log10
from scipy.stats import entropy
from numpy.linalg import norm
import jieba
import numpy as np
from gensim.models.doc2vec import TaggedDocument
from gensim.models import Doc2Vec

##### Preprocessing #####
def preprocess(D):
    # remove stopwords
    stopwords = [line.strip() for line in open('stopwords.txt', encoding='UTF-8').readlines()]

    newD = []
    for d in D:
        new_tokens = [token.strip() for token in (jieba.cut(d)) if token not in stopwords]
        new_d = ' '.join(new_tokens)
        newD.append(new_d)
    return newD

##### Feature Extraction #####
# t is token
# d is document (tokens)
# D is documents
class TFIDF():
    def __init__(self, D):
        self.tokenized_D = [d.split() for d in D]
        self.all_tokens = set([t for d in self.tokenized_D for t in d])

    def fit(self, D):
        tokenized_D = [d.split() for d in D]
        results = []
        for d in tokenized_D:
            results.append([(t, self.tfidf(t, d, self.tokenized_D)) for t in self.all_tokens])

        return results

    @staticmethod
    def f(t, d):
        return d.count(t)

    # normalized
    @staticmethod
    def tf(t, d):
        return 0.5 + 0.5 * TFIDF.f(t, d) / max([TFIDF.f(w, d) for w in d])

    # with smoothing
    @staticmethod
    def idf(t, D):
        return log10(len(D) / (1 + len([True for d in D if t in d])))

    @staticmethod
    def tfidf(t, d, D):
        tfidf = TFIDF.tf(t, d) * TFIDF.idf(t, D)
        return tfidf if tfidf > 0 else 0

# Jensen-Shannon Divergence
def JSD(d, q):
    d = d / norm(d, ord=1)
    q = q / norm(q, ord=1)
    m = 0.5 * (d + q)
    return 0.5 * (entropy(d, m) + entropy(q, m))

# Overlap Similarity
def OS(d, q):
    set_d = set(d)
    set_q = set(q)

    overlap = set_d & set_q

    return float(len(overlap) / len(d))

##### Redundancy Detection #####
# resD is documents that have already been selected for the search
# RD is redundancy degree
gamma = 0.3
theta = 0.5
def is_redundant(resD, d):
    cnt = 0
    for res_d in resD:
        if JSD(res_d, d) < gamma:
            cnt += 1

    RD = cnt / len(resD)
    print(RD)
    return RD > theta

##### Query Expansion #####
def query_expansion(Q):
    url = 'https://www.googleapis.com/customsearch/v1?key=AIzaSyAOHDjhrr2Nw_MjGjVc6cXrEQvloAoheQ8&cx=001973889481213002304:fyj4dfwhre9&alt=json&q=' + Q[0]
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    response = requests.get(url, headers=headers)
    r = json.loads(response.text)
    items = r['items']
    snippets = [item['snippet'] for item in items]
    print('snippets:', snippets)

    newQ = Q + snippets
    newQ = set(preprocess(newQ)[0].split())
    newQ = [' '.join(newQ)]
    return newQ

def remove_no_overlap(Q, D):
    q_tokens = set(preprocess(Q)[0].split())
    print('orig q_tokens:', q_tokens)
    newD = []
    for d in D:
        if any(token in d[0] for token in q_tokens):
            newD.append(d)
    return newD

def doc2vec_corpus(path):
    documents = []
    with open(path, 'rb') as f:
        idx = 0
        while True:
            try:
                line = pickle.load(f)
                documents.append(TaggedDocument( \
                    words = preprocess([line['text']])[0].split(), \
                    tags = [idx]))
                idx += 1
            except:
                break
    return documents

def doc2vec_corpus_json(path):
    documents = []
    with open(path, encoding='utf8') as f:
        lines = json.load(f)
        for idx, line in enumerate(lines):
            documents.append(TaggedDocument( \
                words = preprocess([line['text']])[0].split(), \
                tags = [idx]))
    return documents

if __name__ == '__main__':
    orig_corpus = doc2vec_corpus('tweets.pickle')
#    orig_corpus = doc2vec_corpus_json('tweets.json')
    orig_Q = ['机器人']
    corpus = remove_no_overlap(orig_Q, orig_corpus)
    print(len(orig_corpus))
    print(len(corpus))
    Q = preprocess(orig_Q)[0].split()
    model = Doc2Vec(corpus, min_count=1, epochs=30)
    vector = model.infer_vector(Q, epochs=20)
    similar_docs = model.docvecs.most_similar([vector])
    print('similar_docs:', similar_docs)
    for doc in similar_docs:
        print(doc[0])
        doc = orig_corpus[doc[0]]
        print(doc)
