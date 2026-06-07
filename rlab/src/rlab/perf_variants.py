"""
    perf_variants
    context manager for temporarily swapping callables of equal signature/return
    during OPTIMIZE phase. Explicit dotted keys. Always restores. No magic.
    Pure stdlib. rlab never imports png (layering invariant).
"""
import importlib
from contextlib import contextmanager
import inspect


@contextmanager
def using_impls(replacements):
    """
        replacements
            : dict[str, callable]
            : keys are dotted paths 'module.attr' or 'pkg.sub.attr'
            : values are replacement callables with (intended) identical signature

        yields
            > None (context active for the block)

        effect
            : on entry the target module attrs are replaced
            : on any exit (normal, exception, return) originals are restored

        raises
            ! ValueError for malformed key or module/attr not found at setup
    """
    restores = {}
    try:
        for dotted, new_func in replacements.items():
            if not isinstance(dotted, str) or '.' not in dotted:
                raise ValueError(f"replacement key must be 'module.attr' or 'pkg.mod.attr', got {dotted!r}")
            *mod_parts, attr = dotted.rsplit('.', 1)
            mod_name = '.'.join(mod_parts)
            mod = importlib.import_module(mod_name)
            if not hasattr(mod, attr):
                raise ValueError(f"target {dotted} does not exist on module {mod_name}")
            old = getattr(mod, attr)
            restores[dotted] = (mod, attr, old)
            setattr(mod, attr, new_func)
        yield
    finally:
        for dotted, (mod, attr, old) in restores.items():
            setattr(mod, attr, old)


def check_signature_compat(old, new, name='func'):
    """
        old, new
            : callable
        name
            : str for error messages

        returns
            > bool
            > True if basic parameter count matches or new accepts *args/**kwargs
              (advisory only; caller guarantees full semantic + return contract)

        note
            : radical style: equal sigs/returns is the OPTIMIZE contract, not enforced here
    """
    try:
        s_old = inspect.signature(old)
        s_new = inspect.signature(new)
        if len(s_old.parameters) == len(s_new.parameters):
            return True
        # new is more general
        for p in s_new.parameters.values():
            if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
                return True
        return False
    except (ValueError, TypeError):
        # builtins, C funcs etc: cannot introspect, trust the caller
        return True


if __name__ == '__main__':
    print('=== perf_variants demo ===')

    # local dummies with identical sig for self-contained demo (no external modules needed)
    def _target(a, b, c):
        return a + b + c

    def _alt(a, b, c):
        # same (a,b,c)->int contract, different body
        return (a + b + c) * 10

    key = __name__ + '._target'

    # capture original behavior
    before = _target(1, 2, 3)
    assert before == 6

    with using_impls({key: _alt}):
        # during the with, attribute lookup on the module sees _alt
        mod = importlib.import_module(__name__)
        during = getattr(mod, '_target')(1, 2, 3)
        assert during == 60, f"swap did not take effect, got {during}"

    # restored
    after = _target(1, 2, 3)
    assert after == 6, 'restore failed'
    assert _target is not _alt

    # check_signature_compat is advisory
    assert check_signature_compat(_target, _alt)

    # bad key is caught early
    try:
        with using_impls({'no_dots': lambda x: x}):
            pass
    except ValueError as e:
        assert 'dotted' in str(e).lower() or 'module.attr' in str(e).lower()

    print('perf_variants ok')
