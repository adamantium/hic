#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import urllib
import logging

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

from models import *

# Constants
MEMBERS_PER_PAGE = 20
CATEGORIES_PER_PAGE = 10

def base_template(cls):
    user = users.get_current_user()
    user_detail = None
    if user:
        user_detail = UserDetail.get_by_user(user)

    q = UserDetail.all()
    results = q.fetch(30)
    
    base_template_values = {
        "page_title": "HIC",
        "login_url": users.create_login_url(cls.request.uri),
        "logout_url": users.create_logout_url(cls.request.uri),
        "profile_url": "/user/form?type=usermodify",
        "user": user,
        "user_detail": user_detail,
        "is_admin": users.is_current_user_admin()
    }

    return base_template_values

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.redirect('/admin/dashboard')

class DashboardHandler(webapp.RequestHandler):
    def get(self):
        q = UserDetail.all()
        results = q.fetch(30)
        
        base_template_values = base_template(self)
        
        template_values = {
            "users": results
        }

        path = os.path.join(os.path.dirname(__file__), 'admin.html')
        self.response.out.write(template.render(path, dict(base_template_values, **template_values)))

class MemberListHandler(webapp.RequestHandler):
    def get(self):
        page = self.request.get('page')
        if not page:
            page = 1
        else:
            page = int(page)

        base_template_values = base_template(self) 
        query = UserDetail.all()
        results = query.fetch(limit=MEMBERS_PER_PAGE, offset=(page-1)*MEMBERS_PER_PAGE)

        template_values = {
            "users": results
        }

        path = os.path.join(os.path.dirname(__file__), 'admin_member_list.html')
        self.response.out.write(template.render(path, dict(base_template_values, **template_values)))

class CategoryListHandler(webapp.RequestHandler):
    def get(self):
        page = self.request.get('page')
        if not page:
            page = 1
        else:
            page = int(page)

        base_template_values = base_template(self) 
        query = Category.all()
        query.filter('belong_to =', 'forum')
        results = query.fetch(limit=MEMBERS_PER_PAGE, offset=(page-1)*MEMBERS_PER_PAGE)

        template_values = {
            "categories": results
        }

        path = os.path.join(os.path.dirname(__file__), 'admin_category_list.html')
        self.response.out.write(template.render(path, dict(base_template_values, **template_values)))

class UserConfirmFormHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            path = os.path.join(os.path.dirname(__file__), 'userinfo_input.html')
            self.response.out.write(template.render(path, {"user": user}))
        else:
            self.redirect(users.create_login_url(self.request.uri))

class DoHandler(webapp.RequestHandler):
    def get(self):
        action_types = ['user', 'board', 'article']
        action_dict = {'user': ['confirm', 'unconfirm', 'ban', 'register', 'unregister'],
                        'board': ['create', 'remove'],
                        'article': ['write', 'delete', 'modify', 'block']}
        
        action_type = urllib.unquote(self.request.get('type'))
        action = urllib.unquote(self.request.get('action'))
        target = urllib.unquote(self.request.get('target'))

        if not action_type in action_types:
            response_error(self.response, logging, '%s is not proper type name for an action' % (action_type,))
        elif action_type == "user":
            useridx = int(target)
            user_detail = UserDetail.get_by_id(useridx)
            if not user_detail:
                response_error(self.response, logging, '%d is a unregistered user index.' % (useridx,))
            else:
                if action == "confirm":
                    user_detail.confirmed = True
                    user_detail.put()
                elif action == "unconfirm":
                    user_detail.confirmed = False
                    user_detail.put()
                elif action == "ban":
                    user_detail.banned = True
                    user_detail.put()
                elif action == "unban":
                    user_detail.banned = False
                    user_detail.put()
        elif action_type == "forum":
            if action == "addcategory":
                pass
        elif action_type == "article":
            pass

    def post(self):
        action_type = urllib.unquote(self.request.get('type'))
        action = urllib.unquote(self.request.get('action'))
        logging.debug(action_type + ', ' + action)
        if action_type == "user":
            pass
        elif action_type == "forum":
            if action == "addcategory":
                category_name = self.request.get('name')
                category_des = self.request.get('description')
                category = Category(name=category_name,
                                    description=category_des,
                                    order=1,
                                    belong_to='forum')
                category.put()
            elif action == "removecategory":
                category_name = self.request.get('name')
        self.redirect('forum/list')        
                
        #TODO: Fill in post method action
        
class UserDetailInputHandler(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        user_detail = find_user_detail(user)
        username = self.request.get('name')
        userage = self.request.get('age')
        user_detail.name = username
        user_detail.age = int(userage)
        user_detail.put()
        self.redirect('/')

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    application = webapp.WSGIApplication([('/admin/', MainHandler),
                                        ('/admin/dashboard', DashboardHandler),
                                        ('/admin/members/list', MemberListHandler),
                                        ('/admin/forum/list', CategoryListHandler),
                                        ('/admin/do', DoHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()