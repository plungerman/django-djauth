from django.contrib import auth
from django.contrib.auth.middleware import MiddlewareMixin
from django.http import HttpResponseForbidden


class AutomaticUserLoginMiddleware(MiddlewareMixin):

    #def process_request(self, request):
    def process_view(self, request, view_func, view_args, view_kwargs):
        #if not AutomaticUserLoginMiddleware._is_user_authenticated(request):
        if not request.user.is_authenticated:
            user = auth.authenticate(request)
            if user is None:
                return HttpResponseForbidden()

            request.user = user
            auth.login(request, user)
        return request

    @staticmethod
    def _is_user_authenticated(request):
        user = request.user
        #return user and user.is_authenticated
        return user.is_authenticated

