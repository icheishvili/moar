from moar.http import Controller

class IndexController(Controller):
    def __init__(self, request):
        super(IndexController, self).__init__(request)

    def index(self):
        self.view['a_var'] = 'asdf'
        return self.render('index', 'html')
