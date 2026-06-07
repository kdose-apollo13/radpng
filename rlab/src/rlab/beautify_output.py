"""
    beautify_unittest_output
    reformat default unittest result lines into grouped blocks
"""
import re


def beautify_unittest_output(raw):
    """
        raw
            : str
            : typical unittest -v output text

        returns
            > str
            > reformatted blocks with SCENARIO / Status lines
    """
    if not raw:
        return ''
    out_lines = []
    pat = re.compile(r'^(test_\w+).*?\.{2,}\s*(ok|FAIL|ERROR|skipped)(.*)$', re.I)
    for line in raw.splitlines():
        m = pat.match(line.strip())
        if m:
            name, status, extra = m.groups()
            out_lines.append(f'SCENARIO: {name}')
            out_lines.append(f'  Status: {status.upper()}')
            if extra and extra.strip():
                out_lines.append(f'  Detail: {extra.strip()}')
            out_lines.append('')
        elif line.strip():
            out_lines.append(line.rstrip())
    return '\n'.join(out_lines).rstrip() + '\n'


if __name__ == '__main__':
    print('=== beautify_unittest_output demo ===')
    raw = 'test_foo (TestBar) ... ok\ntest_bar (TestBar) ... FAIL\n'
    nice = beautify_unittest_output(raw)
    assert 'SCENARIO: test_foo' in nice
    assert 'Status: OK' in nice
    assert 'Status: FAIL' in nice
    print('beautify_unittest_output ok')
