

def is_bytes(value):
    # hurray for ducktyping
    try:
        data = value.decode()
        return True
    except AttributeError:
        return False
