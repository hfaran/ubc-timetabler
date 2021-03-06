from __future__ import division

from math import sqrt


#############
# Constants #
#############

DAY_LIST = ["Mon", "Tue", "Wed", "Thu", "Fri"]

###########
# Helpers #
###########

# General

def chunks(l, n):
    """Yields successive ``n``-sized chunks from ``l``

    http://stackoverflow.com/a/312464/1798683
    """
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
    """Check if all items in ``x`` are unique

    http://stackoverflow.com/a/5281641/1798683
    """
    seen = set()
    return not any(i in seen or seen.add(i) for i in x)


def stddev(lst):
    """Calculate **population** (not sample) standard deviation of ``lst``

    :type  lst: list
    :param lst: List of numbers
    :returns: standard deviation of ``lst``
    :rtype: float

    >>> act = stddev([13,25,46,255,55])
    >>> exp = 89.34517334
    >>> abs(act - exp) < 1E-6
    True
    """
    points = len(lst)
    mean = sum(lst)/points
    variance = sum((i - mean)**2 for i in lst)/points
    return sqrt(variance)


def setup_root_logger(log_level='INFO'):
    import logging
    import sys

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level))

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)


# timetabler-specific helpers

def strtime2num(s):
    """Turns ``s`` like "09:00" to 9.5"""
    t = s.split(":")
    t = map(int, t)
    if t[1] == 30:
        return t[0] + 0.5
    else:
        return t[0]


def iter_time(start, end):
    """Returns an iterator that gives a range of half-hourly time
        from ``start`` (inclusive) to ``end`` (exclusive)

    >>> list(iter_time("09:00", "12:30"))
    ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00']
    """

    def time2tuple(t):
        return tuple(map(int, t.split(":")))

    def tuple2time(t):
        return ":".join([str(i).zfill(2) for i in t])

    current = start
    while current < end:
        # Put yield at the time because we do inclusive start, exclusive stop
        yield current
        _current = time2tuple(current)
        if _current[1] == 30:
            _current = (_current[0] + 1, 0)
        else:
            _current = (_current[0], 30)
        current = tuple2time(_current)



if __name__ == '__main__':
    import doctest
    doctest.testmod()
