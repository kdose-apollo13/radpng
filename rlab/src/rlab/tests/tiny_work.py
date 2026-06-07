"""
    tiny_work
    canonical tiny deterministic work function for perf test demos.
    TEST-ONLY helper (stays in tests per zen). One job.
    Used by multiple 2nd-order perf tests to reduce duplication while
    keeping each test file an independent GWT atom.
"""

def tiny_work(n):
    """Simple O(n) work that allocates a little and does arithmetic."""
    s = 0
    lst = [0] * int(n)
    for i in range(int(n)):
        s = (s + (i * 17)) & 0xff
    return s + len(lst)
