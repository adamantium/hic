import logging

from google.appengine.api import users
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

    @classmethod
    def has_authority(cls, target, action):
        if users.is_current_user_admin():
            return True
        if isinstance(target, Post):
            if action == "delete" or action == "modify":
                if target.author == cls:
                    return True
                else:
                    return False
    
class Category(polymodel.PolyModel):
    name = db.StringProperty(required=True)
    code = db.StringProperty(required=True)
    description = db.StringProperty()
    
    @classmethod
    def get_by_code(cls, code):
        query = cls.all()
        query.filter("code =", code)
        return query.get()

class ForumCategory(Category):
    topic_count = db.IntegerProperty(default=0)
    post_count = db.IntegerProperty(default=0)
    next = db.SelfReferenceProperty()

class Post(polymodel.PolyModel):
    idx = db.IntegerProperty() # Unique in a category
    author = db.ReferenceProperty(Member)
    creation = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)
    category = db.ReferenceProperty(Category)
    status = db.IntegerProperty(default=0) # 0: Normal, 1: Deleted by user, 2: Deleted by admin

    @classmethod
    def get_by_category(cls, category_obj, page):
        query = cls.all()
        query.filter("category =", category_obj)
        return query.fetch(limit=POSTS_PER_PAGE, offset=(page-1)*POSTS_PER_PAGE)

class ForumPost(Post):
    title = db.StringProperty()
    content = db.TextProperty()
    attached = db.BlobProperty()
    next_post = db.SelfReferenceProperty(Post, collection_name="next_post_set")
    
class ForumTopic(Post):
    head_post = db.ReferenceProperty(Post, collection_name="head_post_set")
    tail_post = db.ReferenceProperty(Post, collection_name="tail_post_set")
    post_count = db.IntegerProperty(default=0)
    read_count = db.IntegerProperty(default=0)

class Comment(Post):
    parent_post = db.ReferenceProperty(Post)