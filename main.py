import functions_framework
from app import app


@functions_framework.http
def smartlearn_app(request):
    """HTTP Cloud Function for SmartLearn Flask app"""
    with app.request_context(request.environ):
        return app.full_dispatch_request()
