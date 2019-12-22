# IR_weibo
Implement a search engine for Chinese social network service Weibo(<a href="https://weibo.com">微博</a>).<br>
We use BERT embedding with cosine similarity to calculate similarity in the meaning between texts. The implementation used <a href="https://github.com/hanxiao/bert-as-service">bert-as-service</a>.

## Install
#### 1. Install requirements
```bash
pip install -r requirements.txt
```
#### 2. Download a Pre-trained Chinese BERT Model: <a href="https://storage.googleapis.com/bert_models/2018_11_03/chinese_L-12_H-768_A-12.zip">BERT-Base, Chinese</a>
#### 3. Download MongoDB
<a href="https://www.mongodb.com/download-center">MongoDB</a>
Note that the server MUST be running on Python >= 3.5 with Tensorflow >= 1.10 (one-point-ten). Again, the server does not support Python 2!

## Getting started
#### 1. Start the BERT service
```bash
bert-serving-start -model_dir ./chinese_L-12_H-768_A-12/ -num_worker=1 -max_seq_len 100
```
#### 2. Run the Django server
```bash
cd SOUWEIBO & python manage.py runserver
```
#### 3. Visit the url https://127.0.0.1:8080

## Reference
<a href="https://github.com/hanxiao/bert-as-service">bert-as-service</a><br>
<a href="https://developers.google.com/custom-search/v1/overview">Google Custom Search API</a>
