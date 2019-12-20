# -*- coding: utf-8 -*-
import json
import pickle
import requests
import jieba
from math import log10
import numpy as np
from numpy.linalg import norm
from scipy.stats import entropy
from scipy.spatial import distance
from bert_serving.client import BertClient

# load config file
with open('config.json', 'r') as f:
    config = json.load(f)

bc = BertClient()


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

##### Feature Extraction - BERT #####
def BERT_encoder(D):
    D_vectors = bc.encode(D)
    return D_vectors

##### Compute similarity - cosine similarity #####
def similarity_score(v1, v2):
    return distance.cosine(v1, v2)

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
    url = 'https://www.googleapis.com/customsearch/v1?key=' + config['GoogleAPIKey'] \
        + '&cx=' + config['GoogleCX'] \
        + '&alt=json&q=' + Q[0]
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
        if any(token in d for token in q_tokens):
            newD.append(d)
    return newD

if __name__ == '__main__':
    with open('tweets.pickle', 'rb') as f:
        lines = []
        while True:
            try:
                line = pickle.load(f)
            except EOFError:
                break
            lines.append(line)
    print(len(lines))

    # preprocess documents
    D = [line['text'] for line in lines]
    D = preprocess(D)

    # preprocess query
    orig_Q = ['男女爱情剧']
    Q = query_expansion(orig_Q)
    print('Q:', Q)

    D = remove_no_overlap(orig_Q, D)
    print('len(D):', len(D))

    topN = 10    # num of documents to return
    results = [] # the array of search results to return
    # number of candidate documents is smaller than output documents number
    if len(D) <= topN:
        for d in D: print(d)
        results = [d for d in D]
    else:
        # Feature extraction: convert document to vector
        D_vectors = BERT_encoder(D)
        Q_vector = BERT_encoder(Q)

        # Estimate the degree of similarity between query and documents
        scores = np.array([similarity_score(d_vector, Q_vector) for d_vector in D_vectors])
        print('scores:', scores)

        # sort
        topN_idx = scores.argsort()[:topN]
        for idx in topN_idx:
            print(D[idx], scores[idx])
        results = [D[idx] for idx in topN_idx]
