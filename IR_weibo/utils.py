# -*- coding: utf-8 -*-

import sys, os
sys.path.append('..')

import random
import requests
import json
from math import log10
import numpy as np
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

from numpy.linalg import norm
from IR_weibo.inverted_index import InvertedIndex, TagIndex


# load config file
with open('../IR_weibo/config.json', 'r') as f:
    config = json.load(f)

# read stopwords
stopwords = [line.strip() for line in open('../IR_weibo/stopwords.txt', encoding='UTF-8').readlines()]

# Preprocess documents
def preprocess(texts, lcut_func):
    D = []
    for text in texts:
        # remove stopwords
        tokens = [token.strip() for token in (lcut_func(text)) if token not in stopwords and len(token.strip()) is not 0]
        if tokens == []: tokens = ['。'] # tokens cannot be empty
        D.append(tokens)
    return D

# Preprocess query
def preprocess_query(Q_str, lcut_func):
    return list(set(preprocess([Q_str], lcut_func)[0]))


# Find documents that overlaps with keywords of original query
# return [post_id]
def get_candidates(Q):
    invertedIndex = InvertedIndex()
    # return len(invertedIndex.inverted_index)
    return invertedIndex.search(Q)


def get_candidates_tag(Q):
    tagIndex = TagIndex()
    # return len(invertedIndex.inverted_index)
    return tagIndex.search(Q)

def extract_info(tweets, attr):
    try:
        return [tweet[attr] for tweet in tweets]
    except:
        return [tweet['user'][attr] for tweet in tweets]

flatten = lambda l: [item for sublist in l for item in sublist]

# Query Expansion
# info_type also can be 'snippet'
def query_expansion(Q_str, lcut_func, info_type='title', max_q_tokens_len=10):
    orig_Q = preprocess_query(Q_str, lcut_func)
    print('origQ:', orig_Q)
    if len(orig_Q) >= max_q_tokens_len: return orig_Q

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
    expanded_Q = list(set(flatten(preprocess(expanded, lcut_func))))

    len_to_expand = max_q_tokens_len - len(orig_Q)
    if len(expanded_Q) > len_to_expand:
        expanded_Q = random.sample(expanded_Q, len_to_expand)

    newQ = orig_Q + expanded_Q
    return newQ

def get_topN_idxs(scores, topN):
    scores = np.array(scores)
    # O(n)
    unordered_topN_idxs = np.argpartition(scores, -topN)[-topN:]
    # O(klogk), k=topN
    ordered_topN_idxs = unordered_topN_idxs[np.argsort(scores[unordered_topN_idxs])][::-1]
    return ordered_topN_idxs


# Compute overall score including popularity
def overall_score(scores, tweets, attrs=[], params=[]):
    for (attr, param) in zip(attrs, params):
        additional_scores = np.array(extract_info(tweets, attr), dtype=np.int64)
        normalized_scores = additional_scores / np.linalg.norm(additional_scores)
        print('normalized additional scores', normalized_scores)
        scores += param * normalized_scores
    return scores

# Feature Extraction - TFIDF
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


if __name__ == "__main__":
    print(get_candidates(["足睃"]))
