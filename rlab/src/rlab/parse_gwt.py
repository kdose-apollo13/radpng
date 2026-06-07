"""
    parse_gwt
    split a docstring into given / when / then lines
"""


def parse_gwt(doc):
    """
        doc
            : str | None
            : test method docstring (GWT scenario text)

        returns
            > tuple
            > (given, when, then) stripped strings; '' if absent

        tolerates
            Given foo / When: bar / Then baz
            multi-line continuations until next keyword
    """
    if not doc:
        return '', '', ''
    text = doc.strip()
    if not text:
        return '', '', ''

    lines = text.splitlines()
    given_parts = []
    when_parts = []
    then_parts = []
    current = None

    for raw in lines:
        ln = raw.strip()
        low = ln.lower()
        if low.startswith('given'):
            current = 'given'
            rest = ln[5:].lstrip(':').strip()
            if rest:
                given_parts.append(rest)
            continue
        elif low.startswith('when'):
            current = 'when'
            rest = ln[4:].lstrip(':').strip()
            if rest:
                when_parts.append(rest)
            continue
        elif low.startswith('then'):
            current = 'then'
            rest = ln[4:].lstrip(':').strip()
            if rest:
                then_parts.append(rest)
            continue
        elif current == 'given' and ln:
            given_parts.append(ln)
        elif current == 'when' and ln:
            when_parts.append(ln)
        elif current == 'then' and ln:
            then_parts.append(ln)

    return (
        ' '.join(given_parts).strip(),
        ' '.join(when_parts).strip(),
        ' '.join(then_parts).strip(),
    )


if __name__ == '__main__':
    print('=== parse_gwt demo ===')
    doc = """Given foo bar
    When: do thing
    Then expect good
    and more
    """
    g, w, t = parse_gwt(doc)
    assert 'foo bar' in g
    assert 'do thing' in w
    assert 'expect good' in t
    assert parse_gwt('') == ('', '', '')
    print('parse_gwt ok')
