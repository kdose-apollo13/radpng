"""
    name_of
    best-effort human name for a subject (str, __name__, or fallback).
    one job, one function. pure stdlib.
"""

def name_of(obj, fallback='subject'):
    """
        obj
            : anything (usually a callable or str label)
        fallback
            : str

        returns
            > str
            > the string itself, obj.__name__, or the fallback
    """
    if isinstance(obj, str):
        return obj
    return getattr(obj, '__name__', fallback)


if __name__ == '__main__':
    print('=== name_of demo ===')
    assert name_of('foo') == 'foo'
    def bar(): pass
    assert name_of(bar) == 'bar'
    assert name_of(123, fallback='unknown') == 'unknown'
    print('name_of ok')
