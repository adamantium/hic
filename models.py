import logging

from google.appengine.ext import db
from google.appengine.ext.db import polymodel

from settings import *

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
        query = cls.all()
        query.filter("code =", code)
        return query.get()

class ForumCategory(Category):
    next = db.SelfReferenceProperty()

class PlaceCategory(Category):
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()

class Post(polymodel.PolyModel):
    idx = db.IntegerProperty() # Unique in a category
    author = db.ReferenceProperty(Member)
    title = db.StringProperty()
    content = db.TextProperty()
    creation = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)
    category = db.ReferenceProperty(Category)
    status = db.IntegerProperty(default=0) # 0: Normal, 1: Deleted by user, 2: Deleted by admin
    read_count = db.IntegerProperty(default=0)
    comment_count = db.IntegerProperty(default=0)

    @classmethod
    def get_by_category(cls, category_obj, page):
        query = cls.all()
        query.filter("category =", category_obj)
        return query.fetch(limit=POSTS_PER_PAGE, offset=(page-1)*POSTS_PER_PAGE)

class ForumPost(Post):
    attached = db.BlobProperty()
    
class Comment(Post):
    parent_post = db.ReferenceProperty(Post)
