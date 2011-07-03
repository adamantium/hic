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
from shortcuts import *

class UserSignupFormHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write(sc_render_template(self, "user_signup_form.html", {}))

class UserModifyFormHandelr(webapp.RequestHandler):
    def get(self):
        self.response.out.write(sc_render_template(self, "user_signup_form.html", {}))

class UserSignupHandler(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        
        # Gather post data
        name = self.request.get("name")
        nickname = self.request.get("nickname")
        age = self.request.get("age")
        language = self.request.get("language")
        pic = self.request.get("pic")
        intro = self.request.get("intro")
        is_modify = self.request.get("modify")
        is_ajax = self.request.get("ia")
        
        # Validate post data
        validated = False
        if age.isdigit():
            age = int(age)
            validated = True
        else:
            sc_error(self)
        
        # Create new member object
        if validated:
            if is_modify:
                query = Member.all()
                query.filter("user =", user)
                member = query.get()
                if member:
                    member.name = name
                    member.nickname = nickname
                    member.age = age
                    member.language = language
                    member.pic = db.Blob(pic)
                    member.intro = intro
                    member.put()
                else:
                    sc_error(self)
            else:            
                member = Member(user=user,
                                name=name,
                                nickname=nickname,
                                language=language,
                                age=age,
                                pic=db.Blob(pic),
                                intro=intro)
                member.put()
        # Return job status
        if is_ajax:
            self.response.out.write("{'s':1}")
        else:
            self.redirect('/')
            
class UserProfileHandler(webapp.RequestHandler):
    def get(self):
        member_id = self.request.get("id")
        if member_id:
            member = Member.get_by_id(member_id)
        else:
            member = Member.get_by_user(users.get_current_user())
        template_values = {"member": member}
        self.response.out.write(sc_render_template(self, "user_profile.html", template_values))
        
class UserPictureHandler(webapp.RequestHandler):
    def get(self):
        member = db.get(self.request.get("key"))
        if member.pic:
            self.response.headers['Content-Type'] = "image/jpeg"
            self.response.out.write(member.pic)
        else:
            self.response.out.write("No Image")
            
def main():
    logging.getLogger().setLevel(logging.DEBUG) 
    application = webapp.WSGIApplication([("/user/signup-form", UserSignupFormHandler),
                                        ("/user/signup", UserSignupHandler),
                                        ("/user/profile", UserProfileHandler),
                                        ("/user/pic", UserPictureHandler)
                                        ],
                                         debug=True)
    util.run_wsgi_app(application)
    
if __name__ == '__main__':
    main()