"""
Module that holds things related to moar's controller.
"""

from urlparse import parse_qs
from Cookie import SimpleCookie
from jinja2 import Environment, FileSystemLoader


def parse_params(query_string):
    """
    Helper for parsing params. Implements the spec correctly.
    """
    params = parse_qs(query_string)
    for name in params:
        value = params[name]
        if len(value) == 1:
            params[name] = value[0]
    return params


class Controller(object):
    """
    Moar's Controller class. Aims to be useful. Extend this for your own
    controllers. Any class that implements the get_response_start()
    method can be used in place of this one.
    """

    def __init__(self, request):
        """
        Set up basics and defaults, like status codes and headers.
        """
        self.request = request
        self.code = 200
        self.headers = []
        self.view = {}
        self.cookie = None
        self.user = None
        self.parse_cookie()

    def parse_cookie(self):
        """
        Helper for parsing cookie data.
        """
        self.cookie = SimpleCookie()
        if 'HTTP_COOKIE' in self.request:
            self.cookie.load(self.request['HTTP_COOKIE'])

    def get_body_params(self):
        """
        Helper function for parsing body params. Body params are only
        used if the right Content-Type header
        (application/x-www-form-urlencoded) is set.
        """
        if 'CONTENT_TYPE' not in self.request:
            return {}
        if self.request['CONTENT_TYPE'] != 'application/x-www-form-urlencoded':
            return {}
        content_length = int(self.request.get('CONTENT_LENGTH', 0))
        return parse_params(self.request['wsgi.input'].read(content_length))

    def get_params(self):
        """
        Parse all parameters and return them.
        """
        params = parse_params(self.request['QUERY_STRING'])
        params.update(self.get_body_params())
        return params

    def get_response_start(self):
        """
        Build a status code string and headers to send.
        """
        send_headers = list(self.headers)
        for morsel in self.cookie.values():
            send_headers.append(
                ('Set-Cookie', morsel.output(header='').strip()))
        return self.code, send_headers

    def get_template_path(self, method, ext=None):
        """
        Build a path to where the templates for this class/method live.
        Can pass an optional file extension.
        """
        if not ext:
            ext = 'tpl'
        obj_name = self.__class__.__name__.lower().replace('controller', '')
        return '%s/%s.%s' % (obj_name, method, ext)

    def render_raw(self, data, method, ext=None):
        """
        Render a template for the current class and given method. Can
        pass an optional file extension.
        """
        request = Environment(loader=FileSystemLoader('templates'))

        template_path = self.get_template_path(method, ext)
        template = request.get_template(template_path)

        view_vars = dict(data)
        view_vars['user'] = self.user

        return template.render(**view_vars)

    def render(self, method, ext=None):
        """
        Render a template for the current class and given method. Use
        the object's view member variable as a data provider. Can pass
        an optional file extension.
        """
        return str(self.render_raw(self.view, method, ext))
