import json
import requests
import jieba
from math import log10
import numpy as np
from numpy.linalg import norm
from scipy.stats import entropy

# load config file
with open('config.json', 'r') as f:
    config = json.load(f)

# read stopwords
stopwords = [line.strip() for line in open('stopwords.txt', encoding='UTF-8').readlines()]

# Preprocessing
def preprocess(texts):
    D = []
    for text in texts:
        # remove stopwords
        tokens = [token.strip() for token in (jieba.lcut_for_search(text)) if token not in stopwords]
        D.append(tokens)
    return D

# Filter documents without keywords that overlap with the original query
def remove_no_overlap(Q, D):
    q_tokens = set(preprocess(Q)[0])
    print('orig q_tokens:', q_tokens)
    useful_idxs = []
    for idx, d in enumerate(D):
        if any(token in d for token in q_tokens):
            useful_idxs.append(idx)
    return useful_idxs

def leave_useful_info(useful_idxs, D, lines):
    newD, post_ids, mbranks, uranks = [], [], [], []
    for idx in useful_idxs:
        newD.append(D[idx])
        post_ids.append(lines[idx]['post_id'])
        mbranks.append(lines[idx]['user']['mbrank'])
        uranks.append(lines[idx]['user']['urank'])
    return newD, post_ids, mbranks, uranks

##### Query Expansion #####
# info_type also can be 'snippet'
def query_expansion(Q, info_type='title', flag=True):
    if flag is False: return Q

    url = 'https://www.googleapis.com/customsearch/v1?key=' + config['GoogleAPIKey'] \
        + '&cx=' + config['GoogleCX'] \
        + '&alt=json&q=' + Q[0]
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}

    response = requests.get(url, headers=headers)
    r = json.loads(response.text)
    items = r['items']
    expanded = [item[info_type] for item in items]
    print('expanded:', expanded)

    newQ = [' '.join(Q + expanded)]
    return newQ

def get_topN_idxs(scores, topN):
    return np.array(scores.argsort()[-topN:][::-1])

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

