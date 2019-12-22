from django.db import models

# Create your models here.
import mongoengine

class tweeter(mongoengine.Document):
    character_count = mongoengine.IntField()
    collect_count = mongoengine.StringField()
    hash = mongoengine.StringField()
    origin_text = mongoengine.StringField()
    post_id = mongoengine.StringField()
    retweet_count = mongoengine.StringField()
    text = mongoengine.StringField()
    theme = mongoengine.StringField()
    user = mongoengine.DictField()
    pics = mongoengine.ListField()
    vec = mongoengine.ListField()
