"""
    default_name
    choose a label for a function (explicit or __qualname__/__name__ or str).
    one job, one function.
"""

def default_name(fn, explicit=None):
    """
        fn
            : callable or other
        explicit
            : optional str to force

        returns
            > str
    """
    if explicit:
        return explicit
    return getattr(fn, '__qualname__', getattr(fn, '__name__', str(fn)))


if __name__ == '__main__':
    print('=== default_name demo ===')
    assert default_name(lambda x: x) == '<lambda>'
    def foo(): pass
    assert default_name(foo) == 'foo'
    assert default_name(foo, explicit='bar') == 'bar'
    print('default_name ok')
