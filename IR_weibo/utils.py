# -*- coding: utf-8 -*-
import sys, os
sys.path.append('..')

import random
import requests
import jieba, json
from math import log10
import numpy as np

from numpy.linalg import norm
from IR_weibo.inverted_index import InvertedIndex, TagIndex



# load config file
with open('../IR_weibo/config.json', 'r') as f:
    config = json.load(f)

# read stopwords
stopwords = [line.strip() for line in open('../IR_weibo/stopwords.txt', encoding='UTF-8').readlines()]

# Preprocessing
def preprocess(texts):
    D = []
    for text in texts:
        # remove stopwords
        tokens = [token.strip() for token in (jieba.lcut_for_search(text)) if token not in stopwords and len(token.strip()) is not 0]
        if tokens == []: tokens = ['。'] # tokens cannot be empty
        D.append(tokens)
    return D

# Find documents that overlaps with keywords of original query
# return [post_id]
def get_candidates(Q):
    invertedIndex = InvertedIndex()
    return invertedIndex.search(Q)

def extract_info(tweets, attr):
    try:
        return [tweet[attr] for tweet in tweets]
    except:
        return [tweet['user'][attr] for tweet in tweets]

def get_corpus(post_ids, D, lines):
    newD, mbranks, uranks = [], [], []
    for post_id in post_ids:
        idx = post_ids.index(post_id)
        if len(D[idx]) > 0:
            newD.append(D[idx])
            mbranks.append(lines[idx]['user']['mbrank'])
            uranks.append(lines[idx]['user']['urank'])
    return newD, mbranks, uranks

flatten = lambda l: [item for sublist in l for item in sublist]

# Query Expansion
# info_type also can be 'snippet'
def query_expansion(Q_str, info_type='title', flag=True, max_q_len=20):
    if flag is False: return set(preprocess([Q_str])[0])

    Q = set(preprocess([Q_str])[0])
    if len(Q) >= max_q_len: return Q

    url = 'https://www.googleapis.com/customsearch/v1?key=' + config['GoogleAPIKey'] \
        + '&cx=' + config['GoogleCX'] \
        + '&alt=json&q=' + Q_str
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    proxies = {
        'http': 'socks5://127.0.0.1:1080',
        'https': 'socks5://127.0.0.1:1080'
    }
    s = requests.Session()
    s.mount(url,  DESAdapter())
    # s.adapters.DEFAULT_RETRIES = 10
    s.keep_alive = False
    response = s.get(url, headers=headers, proxies=proxies)
    r = json.loads(response.text)
    items = r['items']
    expanded = [item[info_type] for item in items]
    expanded_Q = set(flatten(preprocess(expanded)))

    len_to_expand = max_q_len - len(Q)
    if len(expanded_Q) > len_to_expand:
        expanded_Q = random.sample(expanded_Q, len_to_expand)

    print('expanded_Q:', expanded_Q)
    newQ = Q.union(expanded_Q)
    return newQ

def get_topN_idxs(scores, topN):
    return np.array(scores).argsort()[-topN:][::-1]

# Compute overall score including popularity
alpha = 0.1
def overall_score(scores, tweets, attrs=[]):
    for attr in attrs:
        additional_scores = extract_info(tweets, attr)
        normalized_scores = additional_scores / np.linalg.norm(additional_scores)
        scores += alpha * normalized_scores
    return scores

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

'''
CIPHERS = (
    'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+HIGH:'
    'DH+HIGH:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+HIGH:RSA+3DES:!aNULL:'
    '!eNULL:!MD5'
)


class DESAdapter(HTTPAdapter):
    """
    A TransportAdapter that re-enables 3DES support in Requests.
    """
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=CIPHERS)
        kwargs['ssl_context'] = context
        return super(DESAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=CIPHERS)
        kwargs['ssl_context'] = context
        return super(DESAdapter, self).proxy_manager_for(*args, **kwargs)
'''