"""
    check_signature
    validates the 8-byte png signature
"""
from signature import PNG_SIGNATURE


def check_signature(f):
    """
        f
            : file-like (binary, readable)
            : positioned at start of file

        raises
            ! ValueError if the 8-byte signature does not match PNG_SIGNATURE
    """
    sig = f.read(8)
    if sig != PNG_SIGNATURE:
        raise ValueError(f'bad PNG signature: got {sig.hex()}, expected {PNG_SIGNATURE.hex()}')


if __name__ == '__main__':
    print('=== check_signature demo ===')
    import io

    good = PNG_SIGNATURE + b'\0' * 10
    with io.BytesIO(good) as f:
        check_signature(f)
        print('good sig: ok')

    bad = b'NOTAPNG!' + b'\0' * 10
    with io.BytesIO(bad) as f:
        try:
            check_signature(f)
        except ValueError as e:
            print('bad sig raised:', 'signature' in str(e).lower())

