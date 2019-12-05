import json
import pickle
import requests
from math import log10
from scipy.stats import entropy
from numpy.linalg import norm
import jieba
import numpy as np

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
#    with open('tweets.json', encoding='utf8') as f:
#        lines = json.load(f)
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

#    print(OS(D[0], D[1]))
    topN = 10
    if len(D) <= topN:
        for d in D: print(d)
    else:
        tfidf = TFIDF(D)
        D_vectors = []
        for d in tfidf.fit(D):
            D_vectors.append([t[1] for t in d])

        Q_vector = [t[1] for t in (tfidf.fit(Q)[0])]

        scores = []
        for d_vector in D_vectors:
            scores.append(JSD(Q_vector, d_vector))

        scores = np.array(scores)
        print('scores:', scores)
        topN_idx = scores.argsort()[:topN]
        for idx in topN_idx:
            print(D[idx], scores[idx])
