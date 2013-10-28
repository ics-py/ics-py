#!/usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import chain, islice
 
def window(iterable, size):
    if not size > 0 :
        raise ValueError("Window size must be greater than 0")

    iterator = iter(iterable)
    i = 0
    while True:
        l = list(islice(iterable, i, i+size))
        if len(l) < size and i > 0 or len(l) == 0:
            raise StopIteration()

        yield l
        i +=1
