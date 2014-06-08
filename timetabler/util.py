def chunks(l, n):
    """Yields successive ``n``-sized chunks from ``l``"""
    for i in xrange(0, len(l), n):
        yield l[i:i + n]


def check_equal(iterable):
    """Check equivalency or all items in ``iterable``

    >>> check_equal(xrange(5))
    False
    >>> check_equal([1, 1, 1])
    True
    >>> check_equal([1, 2, 1])
    False
    """
    iterable = iter(iterable)
    first = next(iterable)
    return all(first == i for i in iterable)


def check_diff(iterable):
    """Returns true if any items in ``iterable`` differ

    >>> check_diff([1, 1])
    False
    >>> check_diff([1, 2])
    True
    >>> check_diff(xrange(5))
    True
    """
    iterable = iter(iterable)
    first = next(iterable)
    return any(first != i for i in iterable)


def all_unique(x):
    """Check if all items in ``x`` are unique"""
    seen = set()
    return not any(i in seen or seen.add(i) for i in x)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
