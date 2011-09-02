 #!/usr/bin/env python

import os
import urllib
import logging

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

from models import ForumCategory, ForumTopic, ForumPost, Comment
from controllers.shortcuts import *
from settings import *

def check_permission(permission, target=None):
    user = users.get_current_user()
    if not user:
        return (0, None)
    else:
        member = Member.get_by_user(user)
        if not member:
            return (1, None)
        else:
            if target:
                if target.author == member:
                    return (3, member)
            return (2, member)

def validate_member(handler, target=None):
    (priv, member) = user_authority(handler, target)
    if not member:
        if priv == 0:
            handler.redirect(users.create_login_url(handler.request.url))
        elif priv == 1:
            handler.redirect(sc_create_error("Not Registerd User."))
    return (priv, member)

def validate_category_code(handler, category_code):
    category_obj = ForumCategory.get_by_code(category_code)
    if category_obj:
        return category_obj
    else:
        handler.redirect(sc_create_error("Unidentified Category Code."))

def validate_topic_id(handler, topic_id):
    topic = ForumTopic.get_by_id(topic_id)
    if topic:
        return topic
    else:
        handler.redirect(sc_create_error("Unidentified topic ID."))

def validate_post_id(handler, post_id):
    post = ForumPost.get_by_id(post_id)
    if post:
        return post
    else:
        handler.redirect(sc_create_error("Unidentified Post ID."))

def next_topic_idx(category_obj):
    def increment_counter(category_obj):
        category_obj.topic_count += 1
        category_obj.put()
    key = str(category_obj.key().id()) # Maybe need to enhance the complexity of key for the occasion of duplicated id value.
    idx = memcache.incr(key)
    if idx is None:
        idx = category_obj.post_count + 1
        memcache.add(key, idx, 3600)    
    db.run_in_transaction(increment_counter, category_obj)
    return idx
 
def next_post_idx(topic_obj):
    def increment_topic_counter(topic_obj):
        topic_obj.post_count += 1
        topic_obj.put()
    def increment_category_counter(category_obj):
        category_obj.post_count += 1
        category_obj.put()
    key = str(topic_obj.key().id()) # Maybe need to enhance the complexity of key for the occasion of duplicated id value.
    idx = memcache.incr(key)
    if idx is None:
        idx = topic_obj.post_count + 1
        memcache.add(key, idx, 3600)    
    db.run_in_transaction(increment_topic_counter, topic_obj)    
    category_obj = topic_obj.category
    db.run_in_transaction(increment_category_counter, category_obj)
    return idx

class CategoryListHandler(webapp.RequestHandler):
    def get(self):
        query = ForumCategory.all()
        results = query.fetch(MAX_FORUM_CATEGORIES)
        sc_render_and_response(self, "forum_category_list.html", {'categories': results})

class ListViewHandler(webapp.RequestHandler):
    def get(self, category_code):
        self.redirect("/forum/%s/page/1" % (category_code,))
        
class ListViewHandlerWithPage(webapp.RequestHandler):
    def get(self, category_code, page):
        (priv, member) = user_authority(self)
        page = int(page)
        category_obj = validate_category_code(self, category_code)
        topics = ForumTopic.get_by_category(category_obj, page)
        template_values = {
            "writable": priv >= 2,
            "category": category_obj,
            "topics": topics,
            "page": page
        }
        sc_render_and_response(self, "forum_topic_list.html", template_values)
        
class TopicViewHandler(webapp.RequestHandler):
    def get(self, topic_id, page):
        (priv, member) = validate_member(self)
        topic_id = int(topic_id)
        page = int(page)
        topic_obj = validate_topic_id(self, topic_id)
        posts = []
        cur = 0
        start_pos = (page - 1) * POSTS_PER_PAGE
        end_pos = start_pos + POSTS_PER_PAGE    
        next_post = topic_obj.head_post
        total_page = (topic_obj.post_count - 1) / POSTS_PER_PAGE + 1
        while next_post and cur < end_pos:
            if start_pos <= cur < end_pos and next_post.status == 0:
                posts.append(next_post)
            next_post = next_post.next_post
            cur = cur + 1
        if posts:
            template_values = {
                "writable": priv >= 2,
                "modifiable": prive == 3,
                "topic": topic_obj,
                "category": topic_obj.category,
                "posts": posts,
                "page": page,
                "total_page": range(1, total_page + 1)
            }
            sc_render_and_response(self, "forum_topic_view.html", template_values)
        else:
            self.redirect(sc_create_error("Wrong page."))

class NewTopicFormHandler(webapp.RequestHandler):
    def get(self, category_code):
        member = validate_member(self)
        if not member:
            return True
        category_obj = validate_category_code(self, category_code)
        sc_render_and_response(self, "forum_new_topic_form.html", {'category': category_obj, 'for_modify': False, 'page': 1})

class NewTopicHandler(webapp.RequestHandler):
    def post(self, category_code):
        member = validate_member(self)
        if not member:
            return True
        title = self.request.get('title')
        content = self.request.get('content')
        author = Member.get_by_user(users.get_current_user())
        category_obj = validate_category_code(self, category_code)
        new_topic = ForumTopic(idx=next_topic_idx(category_obj),
                            author=author,
                            category=category_obj)
        new_topic.put()
        new_post = ForumPost(idx=next_post_idx(new_topic),
                            title=title,
                            content=content,
                            author=author,
                            category=category_obj)
        new_post.put()
        new_topic.head_post = new_post
        new_topic.tail_post = new_post
        new_topic.put()
        self.redirect('/forum/' + str(new_topic.key().id()) + '/page/1')

class NewReplyFormHandler(webapp.RequestHandler):
    def get(self, topic_id):
        member = validate_member(self)
        if not member:
            return True
        topic_obj = validate_topic_id(self, int(topic_id))
        sc_render_and_response(self, "forum_new_reply_form.html", {'topic': topic_obj, 'for_modify': False, 'page': 1})

class NewReplyHandler(webapp.RequestHandler):
    def post(self, topic_id):
        member = validate_member(self)
        if not member: 
            return True
        title = self.request.get('title')
        content = self.request.get('content')
        topic_id = int(topic_id)
        author = Member.get_by_user(users.get_current_user())
        topic_obj = validate_topic_id(self, topic_id)
        new_post = ForumPost(idx=next_post_idx(topic_obj),
                            title=title,
                            content=content,
                            author=author,
                            category=topic_obj.category)
        new_post.put()
        tail_post = topic_obj.tail_post
        tail_post.next_post = new_post
        topic_obj.tail_post = new_post
        topic_obj.put()
        tail_post.put()
        last_page = topic_obj.post_count / POSTS_PER_PAGE + 1
        self.redirect('/forum/%i/page/%i' % (topic_obj.key().id(), last_page))

class PostModifyFormHandler(webapp.RequestHandler):
    def get(self, post_id):
        member = validate_member(self)
        if not member:
            return True
        post_id = int(post_id)
        result = validate_post_id(self, post_id)
        if member.has_authority(result, "modify"):
            template_values = {
                "category": result.category,
                "for_modify": True,
                "post": result
            }
            sc_render_and_response(self, "forum_write_form.html", template_values)
        else:
            sc_error_page(self, "You have no authority for the request.")
        
class PostModifyHandler(webapp.RequestHandler):
    def post(self, post_id):
        member = validate_member(self)
        if not member:
            return True
        post_id = int(post_id)
        title = self.request.get('title')
        content = self.request.get('content')
        result = validate_post_id(self, post_id)
        if member.has_authority(result, "modify"):
            result.title = title
            result.content = content
            result.put()
            self.redirect('/forum/%i/' %(post_id, ))
        else:
            sc_error_page(self, "You have no authority for the request.")
        
class PostDeleteHandler(webapp.RequestHandler):
    def get(self, post_id):
        member = validate_member(self)
        if not member:
            return True
        post_id = int(post_id)
        result = validate_post_id(self, post_id)
        if member.has_authority(result, "delete"):
            result.status = 1
            result.put()
            self.redirect('/forum/%s/' % (category_code, ))
        else:
            sc_error_page(self, "You have no authority for the request.")
	
def main():
    logging.getLogger().setLevel(logging.DEBUG)
    application = webapp.WSGIApplication([("/forum/", CategoryListHandler),
    									(r"/forum/([A-Za-z]+)/", ListViewHandler),
    									(r"/forum/([A-Za-z]+)/page/([0-9]+)", ListViewHandlerWithPage),
                                        (r"/forum/([A-Za-z]+)/new-topic-form", NewTopicFormHandler),
                                        (r"/forum/([A-za-z]+)/new-topic", NewTopicHandler),
                                        (r"/forum/([0-9]+)/page/([0-9]+)", TopicViewHandler),
                                        (r"/forum/([0-9]+)/new-reply-form", NewReplyFormHandler),
                                        (r"/forum/([0-9]+)/new-reply", NewReplyHandler),
                                        (r"/forum/([0-9]+)/modify-form", PostModifyFormHandler),
                                        (r"/forum/([0-9]+)/modify", PostModifyHandler),
                                        (r"/forum/([0-9]+)/delete", PostDeleteHandler)
                                        ],
                                        debug=True)
    util.run_wsgi_app(application)

if __name__ == "__main__":
    main()