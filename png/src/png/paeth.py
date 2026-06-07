"""
    paeth_predictor
    the paeth predictor (filter type 4)
"""


def paeth_predictor(a, b, c):
    """
        a, b, c
            : int (0-255)
            : left / up / upper-left byte

        returns
            > int
            > paeth predictor result (0-255)
    """
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    elif pb <= pc:
        return b
    else:
        return c


if __name__ == '__main__':
    print('=== paeth demo ===')
    # p=a+b-c ; choose closest
    assert paeth_predictor(10, 20, 5) == 20
    assert paeth_predictor(5, 20, 10) == 20
    assert paeth_predictor(10, 5, 20) == 5
    assert paeth_predictor(0, 0, 0) == 0
    print('edge + known cases ok')
