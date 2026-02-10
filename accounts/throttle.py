from rest_framework.throttling import SimpleRateThrottle


class LoginRegisterThrottling(SimpleRateThrottle):


    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        email = request.data.get('email')
        if email and email is not None:
            email = email.lower().strip()
            return f'{self.scope}:{ident}:{email}'
        return f'{self.scope}:{ident}'


class LoginThrottling(LoginRegisterThrottling):
    scope = 'login'


class LoginDailyThrottling(LoginRegisterThrottling):
    scope = 'login_daily'


class RegisterThrottling(LoginRegisterThrottling):
    scope = 'register'
    

class RegisterDailyThrottling(LoginRegisterThrottling):
    scope = 'register_daily'