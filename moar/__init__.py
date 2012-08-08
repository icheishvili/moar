"""
The core of the moar framework. Simple, clear, fast.
"""

import re
import httplib
import traceback


def route(config, request):
    """
    Given the config (which has routes defined in it) and the request
    dictionary from WSGI, figure out where to send the given request.
    """
    path = request['PATH_INFO']
    method = request['REQUEST_METHOD']
    for c_route in config['routes']:
        methods = c_route.get('methods', [method])
        if re.search(c_route['regex'], path) and method in methods:
            return c_route['class'], c_route['method']
    return 'NotFoundController', 'index'


def invoke(config, request, klass, method, *args):
    """
    Used to call controllers that the user provides.
    """
    module = __import__(
        '%s.controllers.%s' % (config['module'], klass),
        globals(), locals(), [klass])
    if config.get('dev'):
        reload(module)
    controller = getattr(module, klass)(config, request)
    body = getattr(controller, method)(*args)
    code, headers = controller.get_response_start()
    if not body:
        body = ''
        headers.append(('Content-Length', 0))
    return code, headers, body


def dispatch(config, request, klass, method):
    """
    Given a class and a method, import the class from the controllers
    namespace and try to run the given method. If that fails, handle
    the failure.
    """
    try:
        try:
            code, headers, body = invoke(config, request, klass, method)
        except Exception, ex1:
            ex1_traceback = traceback.format_exc()
            code, headers, body = invoke(
                config, request, 'ErrorController', 'index', ex1)
    except Exception, ex2:
        code = 500
        headers = [('Content-Type', 'text/html')]
        body = '''
        <h1>%s</h1>\n<pre>%s</pre>
        Also, you do not have an ErrorController: %s
        ''' % (repr(ex1), ex1_traceback, repr(ex2))

    full_code = '%s %s' % (code, httplib.responses.get(code, 'Unknown'))
    return full_code, headers, body


def moar(config, request, start_response):
    """
    Convenience for running the moar framework.
    """
    klass, method = route(config, request)
    code, headers, body = dispatch(config, request, klass, method)
    start_response(code, headers)
    return body
