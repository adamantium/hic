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
        result = query.get()
        if result:
            return result
        else:
            return None  
    
class Category(polymodel.PolyModel):
    name = db.StringProperty(required=True)
    code = db.StringProperty(required=True)
    description = db.StringProperty()
    count = db.IntegerProperty(default=0)
    total = db.IntegerProperty()

class ForumCategory(Category):
    next = db.SelfReferenceProperty()

class Post(polymodel.PolyModel):
    idx = db.IntegerProperty(required=True) # Unique in a category
    title = db.StringProperty()
    author = db.ReferenceProperty(Member)
    creation = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)
    category = db.ReferenceProperty(Category)
    status = db.IntegerProperty(default=0) # 0: Normal, 1: Deleted by user, 2: Deleted by admin

    @classmethod
    def get_by_idx(cls, idx, category_obj):
        logging.getLogger().setLevel(logging.DEBUG)
        query = cls.all()
        query.filter("category =", category_obj)
        query.filter("idx =", idx)
        return query.get()
        
class ForumPost(Post):
    content = db.TextProperty()
    attached = db.BlobProperty()
    
class Comment(Post):
    post = db.ReferenceProperty(Post)
    content = db.TextProperty()
