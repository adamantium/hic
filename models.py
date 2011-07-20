import logging

from google.appengine.ext import db
from google.appengine.ext.db import polymodel

class Member(db.Model):
    user = db.UserProperty(required=True)
    name = db.StringProperty()
    nickname = db.StringProperty()
    age = db.IntegerProperty()
    language = db.StringProperty()
    pic = db.BlobProperty()
    intro = db.TextProperty()
    
    @classmethod
    def get_by_user(cls, user):
        query = cls.all()
        query.filter("user =", user)
        return query.get()
    
class Category(polymodel.PolyModel):
    name = db.StringProperty(required=True)
    code = db.StringProperty(required=True)
    description = db.StringProperty()
    count = db.IntegerProperty(default=0)
    total = db.IntegerProperty()
    
    @classmethod
    def get_by_code(cls, code):
        logging.getLogger().setLevel(logging.DEBUG)
        query = cls.all()
        query.filter("code =", code)
        results = query.fetch(limit=100)
        for p in results:
            logging.debug(p.name)
        return results[0]
        # return query.get()

class ForumCategory(Category):
    next = db.SelfReferenceProperty()

class PlaceCategory(Category):
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()

class Post(polymodel.PolyModel):
    idx = db.IntegerProperty(required=True) # Unique in a category
    author = db.ReferenceProperty(Member)
    title = db.StringProperty()
    content = db.TextProperty()
    creation = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)
    category = db.ReferenceProperty(Category)
    status = db.IntegerProperty(default=0) # 0: Normal, 1: Deleted by user, 2: Deleted by admin
    count = db.IntegerProperty(default=0)

    @classmethod
    def get_by_idx(cls, idx, category_obj):
        logging.getLogger().setLevel(logging.DEBUG)
        query = cls.all()
        query.filter("category =", category_obj)
        query.filter("idx =", idx)
        return query.get()
        
class ForumPost(Post):
    attached = db.BlobProperty()
    
class Comment(Post):
    parent_post = db.ReferenceProperty(Post)
