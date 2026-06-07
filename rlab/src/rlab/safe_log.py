"""
    safe_log
    math.log with guard for <=0 (returns 0.0).
    one job.
"""
import math


def safe_log(x):
    return math.log(x) if x > 0 else 0.0


if __name__ == '__main__':
    print('=== safe_log demo ===')
    assert safe_log(1) == 0.0
    assert safe_log(8) > 2.0
    assert safe_log(0) == 0.0
    print('safe_log ok')
