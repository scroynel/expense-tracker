from rest_framework.throttling import UserRateThrottle, SimpleRateThrottle


class StatsThrottling(UserRateThrottle):
    scope = 'stats'
