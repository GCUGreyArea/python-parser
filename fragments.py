def decode_fragment(value):
    if value.isnumeric():
        return int(value)
    try:
        return float(value)
    except:
        return value
