# __init__.py

try:
    from timeout_decorator import timeout, TimeoutError
    SKIP_TIMED = False
except ImportError:
    SKIP_TIMED = True
    TimeoutError = None
    def timeout(x):
        # decorator that does nothing
        def wrap(f):
            def wrapped_f(*args, **kwargs):
                return f(*args, **kwargs)
            return wrapped_f
        return wrap
