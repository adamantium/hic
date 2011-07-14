#!/usr/bin/env python

import os
import urllib
import logging

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

from models import *
from controllers.shortcuts import *

# Constants
POSTS_PER_PAGE = 20

class CategoryListHandler(webapp.RequestHandler):
    def get(self):
        query = ForumCategory.all()
        results = query.fetch(100)
        sc_render_and_response(self, "forum_category_list.html", {'categories': results})

class ListViewHandler(webapp.RequestHandler):
    def get(self, category):
        logging.debug('Requested category code: ' + category)
        category_obj = sc_validate_category(category, kind='forum')
        if category_obj:
            query = ForumPost.all()
            query.filter('category =', category_obj)
            results = query.fetch(limit=POSTS_PER_PAGE, offset=0)
            for p in results:
                logging.debug('requested posts ' + p.title)
            template_values = {
                'category': category_obj,
                'posts': results,
                'page': 1
            }
            sc_render_and_response(self, "forum_post_list.html", template_values)
        else:
            sc_error_page(self, "Category not found")
        
class ListViewHandlerWithPage(webapp.RequestHandler):
    def get(self, category, page):
        page = int(page)
        category_obj = sc_validate_category(category, kind='forum')
        if category_obj:
            query = ForumPost.all()
            query.filter('category =', category_obj)
            results = query.fetch(limit=POSTS_PER_PAGE, offset=(page-1)*POSTS_PER_PAGE)
            template_values = {
                'category': category_obj,
                'posts': results,
                'page': page
            }
            sc_render_and_response(self, "forum_post_list.html", template_values)
        else:
            sc_error_page(self, "Category not found")
        
class PostViewHandler(webapp.RequestHandler):
    def get(self, category, post_idx):
        category_obj = sc_validate_category(category, kind='forum')
        if category_obj:
            result = ForumPost.get_by_idx(int(post_idx), category_obj)       
            sc_render_and_response(self, "forum_post_view.html", {'category': category, 'post': result, 'page': 1})
        else:
            sc_error_page(self, "Unategory")

class PostViewHandlerWithPage(webapp.RequestHandler):    
    def get(self, category, page, post_idx):
        page = int(page)
        category_obj = sc_validate_category(category, kind='forum')
        if category_obj:
            result = ForumPost.get_by_idx(int(post_idx), category_obj)
            sc_render_and_response(self, "forum_post_view.html", {'category': category, 'post': result, 'page': page})
        else:
            sc_error_page(self, "Category not found")

class PostWriteFormHandler(webapp.RequestHandler):
    def get(self, category):
        category_obj = sc_validate_category(category, kind='forum')
        if category_obj:     
            sc_render_and_response(self, "forum_write_form.html", {'category': category_obj, 'for_modify': False, 'page': 1})
        else:
            sc_error_page(self, "Category not found")

class PostWriteHandler(webapp.RequestHandler):
    def post(self, category):
        title = self.request.get('title')
        content = self.request.get('content')
        author = Member.get_by_user(users.get_current_user())
        category_obj = sc_validate_category(category, kind='forum')
        if category_obj:
            new_post = ForumPost(idx=sc_count(category_obj),
                                title=title,
                                content=content,
                                author=author,
                                category=category_obj)
            new_post.put()
            self.redirect('/forum/%s/' % (category, ))
        else:
            sc_error_page(self, "Category not found")
        
class PostModifyFormHandler(webapp.RequestHandler):
    def get(self, category_code, post_idx):
        category_obj = sc_validate_category(category_code, kind='forum')
        post_idx = int(post_idx)
        if category_obj:
            result = ForumPost.get_by_idx(post_idx, category_obj)
            if result:
                if sc_has_authority(users.get_current_user(), result):
                    template_values = {
                        "category": category_obj,
                        "for_modify": True,
                        "post": result
                    }
                    sc_render_and_response(self, "forum_write_form.html", template_values)
                else:
                    sc_error_page(self, "You have no authority for the request.")
            else:
                sc_error_page(self, "Post Index is not available")
        else:
            sc_error_page(self, "Undifined Category")
        
class PostModifyHandler(webapp.RequestHandler):
    def post(self, category_code, post_idx):
        title = self.request.get('title')
        content = self.request.get('content')
        category_obj = sc_validate_category(category_code, kind='forum')
        if category_obj:
            result = ForumPost.get_by_idx(int(post_idx), category_obj)
            if result:
                if sc_has_authority(users.get_current_user(), result):
                    result.title = title
                    result.content = content
                    result.put()
                    self.redirect('/forum/%s/' % (category_code, ))
                else:
                    sc_error_page(self, "You have no authority for the request.")
            else:
                sc_error_page(self, "Post Index is available")
        else:
            sc_error_page(self, "Undifined Category")
        
class PostDeleteHandler(webapp.RequestHandler):
    def get(self, category_code, post_idx):
        category_obj = sc_validate_category(category_code, kind='forum')
        if category_obj:
            result = ForumPost.get_by_idx(int(post_idx), category_obj)
            if result:
                if sc_has_authority(users.get_current_user(), result):
                    result.status = 1
                    result.put()
                    self.redirect('/forum/%s/' % (category_code, ))
                else:
                    sc_error_page(self, "You have no authority for the request.")
            else:
                sc_error_page(self, "Post Index is available")
        else:
            sc_error_page(self, "Undifined Category")
	
def main():
    logging.getLogger().setLevel(logging.DEBUG)
    application = webapp.WSGIApplication([('/forum/', CategoryListHandler),
    									(r'/forum/([A-Za-z]+)/', ListViewHandler),
    									(r'/forum/([A-Za-z]+)/page/([0-9]+)', ListViewHandlerWithPage),
    									(r'/forum/([A-Za-z]+)/([0-9]+)', PostViewHandler),
                                        (r'/forum/([A-Za-z]+)/page/([0-9]+)/([0-9]+)', PostViewHandlerWithPage),
                                        (r'/forum/([A-Za-z]+)/write-form', PostWriteFormHandler),
                                        (r'/forum/([A-Za-z]+)/write', PostWriteHandler),
                                        (r'/forum/([A-Za-z]+)/([0-9]+)/modify-form', PostModifyFormHandler),
                                        (r'/forum/([A-Za-z]+)/([0-9]+)/modify', PostModifyHandler),
                                        (r'/forum/([A-Za-z]+)/([0-9]+)/delete', PostDeleteHandler)
                                        ],
                                        debug=True)
    util.run_wsgi_app(application)

if __name__ == "__main__":
    main()