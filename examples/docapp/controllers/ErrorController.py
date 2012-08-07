from moar.http import Controller

class ErrorController(Controller):
    def __init__(self, config, request):
        super(ErrorController, self).__init__(config, request)
        self.code = 500

    def index(self, *args):
        return 'lol fail: %s' % args
