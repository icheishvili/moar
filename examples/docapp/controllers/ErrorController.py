from moar.http import Controller

class ErrorController(Controller):
    def __init__(self, request):
        super(ErrorController, self).__init__(request)
        self.code = 500

    def index(self, *args):
        return 'lol fail: %s' % args
