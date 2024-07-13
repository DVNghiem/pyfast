

class Middleware:

    def __init__(self, app):
        self.app = app

    def before_request(self, request):
        pass

    def after_request(self, request, response):
        return response