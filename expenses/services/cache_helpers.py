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