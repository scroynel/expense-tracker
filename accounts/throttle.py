from rest_framework.throttling import SimpleRateThrottle


class LoginThrottling(SimpleRateThrottle):
    scope = 'login'


    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        print('ident', ident)
        print('request data', request.data)
        email = request.data.get('email')
        if email:
            return f'login:{ident}:{email}'
        return f'login:{ident}'