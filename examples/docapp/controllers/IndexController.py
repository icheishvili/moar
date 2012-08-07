from moar.http import Controller

class IndexController(Controller):
    def index(self):
        self.view['a_var'] = 'asdf'
        return self.render('index', 'html')
