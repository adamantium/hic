import os
import logging

from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.webapp import template

from models import Member, Category, ForumCategory

#
# Security Related Functions
#


    

#
# Template Related Functions
#

def sc_base_template_values(handler):
    user = users.get_current_user()
    member = None
    if user:
        member = Member.get_by_user(user)
    base_template_values = {
        "page_title": "HIC",
        "login_url": users.create_login_url(handler.request.uri),
        "logout_url": users.create_logout_url(handler.request.uri),
        "profile_url": "/user/profile",
        "user": user,
        "member": member,
        "is_admin": users.is_current_user_admin()
    }
    return base_template_values

def sc_render_template(handler, filename, template_values):
    path = os.path.join(os.path.dirname(__file__), '../views/' + filename)
    return template.render(path, dict(sc_base_template_values(handler), **template_values))
    
def sc_render_and_response(handler, filename, template_values):
    handler.response.out.write(sc_render_template(handler, filename, template_values))
    
def sc_error_page(handler, msg):
    handler.response.out.write("<h2>%s</h2>" % (msg,))


#
# Forum Related Functions
#

def sc_count(category_obj):
    # TODO: NEED TO BE FIXED. use memcache instead of category_obj.
    def increment_counter(category_obj):
        category_obj.count += 1
        category_obj.put()
    logging.getLogger().setLevel(logging.DEBUG)
    key = category_obj.code
    count = category_obj.count        
    logging.debug("current count(from db): " + str(count))
    if memcache.incr(key, initial_value=count):
        db.run_in_transaction(increment_counter, category_obj)
        return count + 1
    
def sc_validate_category(category_code, kind=None):
    logging.getLogger().setLevel(logging.DEBUG)
    query = None
    if kind == None:
        logging.debug("all")
        query = Category.all()
    elif kind == "forum":
        logging.debug("forum")
        query = ForumCategory.all()
        logging.debug(query)
	if query != None:
	    logging.debug("code is about to found")
	    query.filter('code =', category_code)
	    result = query.get()
	    return result
	else:
	    logging.debug("hello!")
	    
def sc_has_authority(user, post):
    category_auth = False # TODO: Fill in when category specific admin function is available
    post_auth = (post.author.user == user)
    admin_auth = users.is_current_user_admin()
    return (category_auth or post_auth or admin_auth)

def sc_error(self):
    return "ERROR"