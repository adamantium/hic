import os

from google.appengine.api import users
from google.appengine.ext.webapp import template

from models import Member

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
    
def sc_error(self):
    return "ERROR"