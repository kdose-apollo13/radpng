"""
    Recorder
    simple call-time recorder for hotspot attribution.
    owns its stats dict. one (small) job.
"""

class Recorder:
    def __init__(self, base_measurer):
        self._base_measurer = base_measurer
        self._stats = {}
        self._default_name = __import__('rlab.default_name', fromlist=['default_name']).default_name

    def wrap(self, fn, name=None):
        label = self._default_name(fn, name)

        def _wrapped(*a, **k):
            dt = self._base_measurer(fn, *a, **k)  # the measurer is already (func,*a,**k)->float
            if label not in self._stats:
                self._stats[label] = {'calls': 0, 'time': 0.0}
            self._stats[label]['calls'] += 1
            self._stats[label]['time'] += dt
            return

        _wrapped.__name__ = f"wrapped({label})"
        return _wrapped

    def stats(self):
        return {k: v.copy() for k, v in self._stats.items()}

    def reset(self):
        self._stats.clear()
