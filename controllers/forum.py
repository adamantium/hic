 #!/usr/bin/env python

import os
import urllib
import logging

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

from models import ForumCategory, ForumPost, Comment
from controllers.shortcuts import *
from settings import *

def validate_category_code(handler, category_code):
    category_obj = ForumCategory.get_by_code(category_code)
    if category_obj:
        return category_obj
    else:
        handler.redirect(sc_create_error("Unidentified Category Code."))

def validate_post_id(handler, post_id):
    post = ForumPost.get_by_id(post_id)
    if post:
        return post
    else:
        handler.redirect(sc_create_error("Unidentified Post ID."))

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
        page = int(page)
        category_obj = validate_category_code(self, category_code)
        posts = ForumPost.get_by_category(category_obj, page)
        template_values = {
            'category': category_obj,
            'posts': posts,
            'page': page
        }
        sc_render_and_response(self, "forum_post_list.html", template_values)
        
class PostViewHandler(webapp.RequestHandler):
    def get(self, post_id):
        post_id = int(post_id)
        page = self.request.get("page")
        if page is None:
            page = 1
        else:
            page = int(page)
        result = validate_post_id(self, post_id)
        sc_render_and_response(self, "forum_post_view.html", {'category': category_obj, 'post': result, 'page': page})

class PostWriteFormHandler(webapp.RequestHandler):
    def get(self, category_code):
        category_obj = validate_category_code(self, category_code)
        sc_render_and_response(self, "forum_write_form.html", {'category': category_obj, 'for_modify': False, 'page': 1})

class PostWriteHandler(webapp.RequestHandler):
    def post(self, category_code):
        title = self.request.get('title')
        content = self.request.get('content')
        author = Member.get_by_user(users.get_current_user())
        category_obj = validate_category_code(self, category_code)
        new_post = ForumPost(idx=sc_count(category_obj),
                            title=title,
                            content=content,
                            author=author,
                            category=category_obj)
        new_post.put()
        self.redirect('/forum/' + category_code + '/')
        
class PostModifyFormHandler(webapp.RequestHandler):
    def get(self, post_id):
        post_id = int(post_id)
        result = validate_post_id(self, post_id)
        if sc_has_authority_for_post(users.get_current_user(), result):
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
        post_id = int(post_id)
        title = self.request.get('title')
        content = self.request.get('content')
        
        result = validate_post_id(self, post_id)
        if sc_has_authority_for_post(users.get_current_user(), result):
            result.title = title
            result.content = content
            result.put()
            self.redirect('/forum/%s/' % (category_code, ))
        else:
            sc_error_page(self, "You have no authority for the request.")
        
class PostDeleteHandler(webapp.RequestHandler):
    def get(self, post_id):
        post_id = int(post_id)
        if sc_has_authority(users.get_current_user(), result):
            result = validate_post_id(self, post_id)
            result.status = 1
            result.put()
            self.redirect('/forum/%s/' % (category_code, ))
        else:
            sc_error_page(self, "You have no authority for the request.")

class CommentWriteHandler(webapp.RequestHandler):
    def post(self, post_id):
        content = self.request.get('content')
        post_id = int(post_id)
        author = Member.get_by_user(users.get_current_user())
        parent_post = validate_post_id(self, post_id)
        new_comment = Comment(content=content,
                            author=author,
                            category=category_obj,
                            parent_post=parent_post)
        new_post.put()
        self.redirect('/forum/' + str(post_id))
	
def main():
    logging.getLogger().setLevel(logging.DEBUG)
    application = webapp.WSGIApplication([('/forum/', CategoryListHandler),
    									(r'/forum/([A-Za-z]+)/', ListViewHandler),
    									(r'/forum/([A-Za-z]+)/page/([0-9]+)', ListViewHandlerWithPage),
    									(r'/forum/([0-9]+)', PostViewHandler),
                                        (r'/forum/([A-Za-z]+)/write-form', PostWriteFormHandler),
                                        (r'/forum/([A-Za-z]+)/write', PostWriteHandler),
                                        (r'/forum/([0-9]+)/modify-form', PostModifyFormHandler),
                                        (r'/forum/([0-9]+)/modify', PostModifyHandler),
                                        (r'/forum/([0-9]+)/delete', PostDeleteHandler),
                                        (r'/forum/([A-Za-z]+)/([0-9]+)/comment/write', CommentWriteHandler)
                                        #(r'/forum/([A-Za-z]+)/([0-9]+)/comment/modify-form', CommentModifyFormHandler),
                                        #(r'/forum/([A-Za-z]+)/([0-9]+)/comment/modify', CommentModifyHandler),
                                        #(r'/forum/([A-Za-z]+)/([0-9]+)/comment/delete', CommentDeleteHandler)
                                        ],
                                        debug=True)
    util.run_wsgi_app(application)

if __name__ == "__main__":
    main()