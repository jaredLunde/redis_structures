#!/usr/bin/python3 -S
# -*- coding: utf-8 -*-
"""
   `Redis Structures Unit Tests`
--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--
   2015 Jared Lunde © The MIT License (MIT)
   http://github.com/jaredlunde

"""
from redis_defaultdict import *
from redis_defaulthash import *
from redis_dict import *
from redis_hash import *
from redis_list import *
from redis_map import *
from redis_set import *
from redis_sorted_set import *


if __name__ == '__main__':
    #: python3 ~/git/redis_structures/tests/all.py -v
    unittest.main()
