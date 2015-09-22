#!/usr/bin/python3 -S
# -*- coding: utf-8 -*-
"""

  `Stats Tools` - drop-in functions when neither numpy or statistics can be
    imported
--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--
  Credit: http://stackoverflow.com/a/27758326
  Credit: http://stackoverflow.com/a/24101534

"""


class np(object):
    pass


def mean(data):
    """Return the sample arithmetic mean of data."""
    #: http://stackoverflow.com/a/27758326
    n = len(data)
    if n < 1:
        raise ValueError('mean requires at least one data point')
    return sum(data)/n  # in Python 2 use sum(data)/float(n)


def _ss(data):
    """Return sum of square deviations of sequence data."""
    #: http://stackoverflow.com/a/27758326
    c = mean(data)
    ss = sum((x-c)**2 for x in data)
    return ss


def pstdev(data):
    """Calculates the population standard deviation."""
    #: http://stackoverflow.com/a/27758326
    n = len(data)
    if n < 2:
        raise ValueError('variance requires at least two data points')
    ss = _ss(data)
    pvar = ss/n  # the population variance
    return pvar**0.5


def median(lst):
    """ Calcuates the median value in a @lst """
    #: http://stackoverflow.com/a/24101534
    sortedLst = sorted(lst)
    lstLen = len(lst)
    index = (lstLen - 1) // 2
    if (lstLen % 2):
        return sortedLst[index]
    else:
        return (sortedLst[index] + sortedLst[index + 1])/2.0
