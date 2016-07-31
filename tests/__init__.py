# __init__.py

try:
    from timeout_decorator import timeout, TimeoutError
    SKIP_TIMED = False
except ImportError:
    SKIP_TIMED = True
    TimeoutError = None
    def timeout(_unused):
        # decorator that does nothing
        def wrap(func):
            def wrapped_f(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapped_f
        return wrap
