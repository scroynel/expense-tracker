from django.core.cache import cache
from decimal import Decimal


def make_float(data: dict):
    """Converts all Decimal values in a dict to float"""
    new_data = {}

    for k, v in data.items():
        if isinstance(v, dict):
            new_data[k] = make_float(v)
        elif isinstance(v, Decimal):
            new_data[k] = float(v)
        else:
            new_data[k] = v

    return new_data


def get_user_version(user_id):
    version_key = f'stats:overview:user:{user_id}:version'
    version = cache.get(version_key)

    if version is None:
        version = 1
        cache.set(version_key, version, None)
    
    return version


def get_stats_overview_cache_key(user_id):
    version = get_user_version(user_id)
    return f'stats:overview:user:{user_id}:v{version}'


def bump_stats_overview_version(user_id):
    version_key = f'stats:overview:user:{user_id}:version'
    try:
        cache.incr(version_key)
    except ValueError:
        cache.set(version_key, 2, None)