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

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

from models import *
from controllers.shortcuts import *

class MainHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user and not Member.get_by_user(user):
            self.redirect("/user/signup-form")
        else:
            self.response.out.write(sc_render_template(self, "base.html", {}))
            
class ClearMemcacheHandler(webapp.RequestHandler):
    def get(self):
        if memcache.flush_all():
            self.response.out.write("memcache is flushed")
        else:
            self.response.out.write("memcache flushing failed")

class ErrorPageHandler(webapp.RequestHandler):
    def get(self, error_key):
        error = memcache.get(error_key)
        msg = "Unidentified Error."
        if error is not None:
            ts = error[0]
            if ts + abs(hash(error[1])) == int(error_key):
                msg = error[1]
        self.error(500)
        self.response.out.write(msg)
        
def main():
    logging.getLogger().setLevel(logging.DEBUG) 
    application = webapp.WSGIApplication([('/', MainHandler),
                                        ('/cmc', ClearMemcacheHandler),
                                        (r'/error/([0-9]*)', ErrorPageHandler)
                                        ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()