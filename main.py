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

# BERT Embedding client
bc = BertClient()

# read stopwords
stopwords = [line.strip() for line in open('stopwords.txt', encoding='UTF-8').readlines()]

##### Preprocessing #####
def preprocess(D):
    newD = []
    for d in D:
        # remove stopwords
        new_tokens = [token.strip() for token in (jieba.cut(d)) if token not in stopwords]
        new_d = ' '.join(new_tokens)
        newD.append(new_d)
    return newD

# every element has (document, mbrank, urank)
def preprocess_triple(D):
    newD, new_mbranks, new_uranks = [], [], []
    for d, mbrank, urank in D:
        # remove stopwords
        new_tokens = [token.strip() for token in (jieba.cut(d)) if token not in stopwords]
        new_d = ' '.join(new_tokens)
        newD.append(new_d)
        new_mbranks.append(mbrank)
        new_uranks.append(urank)
    return newD, new_mbranks, new_uranks

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

##### Feature Extraction - BERT #####
def BERT_encoder(D):
    D_vectors = bc.encode(D)
    return D_vectors

##### Compute similarity - cosine similarity #####
# The score ranges from 0 to 2. 2 means most similar
def similarity_score(D_vectors, Q_vector):
    return np.array([2 - distance.cosine(d_vector, Q_vector) for d_vector in D_vectors])

##### Compute overall score including popularity #####
alpha = 0.01
beta  = 0.001
def overall_score(scores, mbranks, uranks):
    return np.array([score + alpha*mbrank + beta*urank \
            for score, mbrank, urank in zip(scores, mbranks, uranks)])

##### Feature Extraction - TFIDF #####
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

# Filter documents without keywords that overlap with query
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
    D = [(line['text'], line['user']['mbrank'], line['user']['urank']) for line in lines]
    D, mbranks, uranks = preprocess_triple(D)

    # preprocess query
    orig_Q = ['男女爱情剧']
    Q = query_expansion(orig_Q)
    Q = orig_Q
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
        scores = similarity_score(D_vectors, Q_vector)
        overall_scores = overall_score(scores, mbranks, uranks)

        # sort
        topN_idx = overall_scores.argsort()[-topN:][::-1]
        for idx in topN_idx:
            print(D[idx], overall_scores[idx])
        results = [D[idx] for idx in topN_idx]
