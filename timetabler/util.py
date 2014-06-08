def chunks(l, n):
    """Yields successive ``n``-sized chunks from ``l``"""
    for i in xrange(0, len(l), n):
        yield l[i:i + n]


def check_equal(lst):
    """Check equivalency or all items in ``lst``

    http://stackoverflow.com/q/3844948/
    """
    # This works by counting the number of occurrences
    #   of the first element of the list and checking
    #   if that count is equal to the length of the
    #   list
    return not lst or lst.count(lst[0]) == len(lst)
