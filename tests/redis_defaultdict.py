#!/usr/bin/python3 -S
# -*- coding: utf-8 -*-
"""
   `Redis DefaultDict Tests`
--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--
   2015 Jared Lunde © The MIT License (MIT)
   http://github.com/jaredlunde

"""
import datetime
import time
import pickle
import unittest

from redis_structures.debug import RandData, gen_rand_str
from redis_structures import StrictRedis, RedisDefaultDict


class TestJSONRedisDefaultDict(unittest.TestCase):
    dict = RedisDefaultDict("json_dict", prefix="rs:unit_tests:", serialize=True)
    is_str = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addCleanup(self.dict.clear)

    def cast(self, obj):
        return str(obj) if self.is_str else obj

    def reset(self, count=10, type=int):
        self.dict.clear()
        self.data = RandData(type).dict(count, 1)
        self.data_len = len(self.data)
        self.dict.update(self.data)

    def test_prefix(self):
        self.assertEqual(self.dict.prefix, 'rs:unit_tests')
        self.assertEqual(self.dict.name, 'json_dict')
        self.assertEqual(self.dict.key_prefix, 'rs:unit_tests:json_dict')

    def test_incr_decr(self):
        self.reset()
        self.dict.incr('views', 1)
        self.assertEqual(self.dict['views'], self.cast(1))
        self.dict.incr('views', 3)
        self.assertEqual(self.dict['views'], self.cast(4))
        self.dict.decr('views', 1)
        self.assertEqual(self.dict['views'], self.cast(3))

    def test_get(self):
        self.reset()
        self.dict["hello"] = "world"
        self.assertEqual(self.dict.get("hello"), 'world')
        self.assertEqual(self.dict.get('world', 'hello'), 'hello')
        self.assertEqual(self.dict['world'], {})

    def test_get_key(self):
        self.assertEqual(
            self.dict.get_key('views'),
            "{}:{}:{}".format(self.dict.prefix, self.dict.name, 'views'))

    def test_items(self):
        self.reset()
        self.assertDictEqual(
            {k: v for k, v in self.dict.items()},
            {k: self.cast(v) for k, v in self.data.items()})

    def test_values(self):
        self.reset()
        self.assertSetEqual(
            set(self.dict.values()),
            set(map(self.cast, self.data.values())))

    def test_iter(self):
        self.reset()
        self.assertSetEqual(
            set(k for k in self.dict.iter()),
            set(self.cast(k) for k in self.data.keys()))

    def test_iter_match(self):
        self.reset(count=10)
        self.assertSetEqual(
            set(k for k in self.dict.iter("a*")),
            set(self.cast(k) for k in self.data.keys() if k.startswith('a')))

    def test_mget(self):
        self.reset(0)
        self.dict.update({
            'test1': 1,
            'test2': 2,
            'test3': 3,
            'test4': 4,
            'test5': 5})
        self.assertListEqual(
            self.dict.mget('test2', 'test3', 'test4'),
            [self.cast(2), self.cast(3), self.cast(4)])

    def test_pop(self):
        self.reset()
        self.dict['hello'] = 'world'
        self.assertEqual(self.dict.pop('hello'), 'world')
        self.assertNotIn('hello', self.dict)

    def test_delete(self):
        self.reset()
        self.dict['hello'] = 'world'
        self.assertEqual(self.dict['hello'], 'world')
        del self.dict['hello']
        self.assertNotIn('hello', self.dict)

    def test_scan(self):
        self.reset()
        new_keys = []
        cursor = '0'
        while cursor:
            cursor, keys = self.dict.scan(count=1, cursor=int(cursor))
            if keys:
                new_keys.extend(keys)
        self.assertSetEqual(
            set(self.dict.get_key(k) for k in self.data.keys()), set(new_keys))

    def test_set(self):
        self.reset()
        self.dict.set("hello", "world")
        self.assertIn("hello", self.dict)

    def test_len(self):
        self.reset(100)
        self.assertEqual(len(self.dict), self.data_len)
        self.reset(1000)
        self.assertEqual(len(self.dict), self.data_len)
        rem = [k for k in list(self.dict)[:250]]
        self.dict.remove(*rem)
        self.assertEqual(len(self.dict), self.data_len - len(rem))


class TestPickledRedisDefaultDict(TestJSONRedisDefaultDict):
    dict = RedisDefaultDict("pickled_dict", prefix="rs:unit_tests:", serializer=pickle)

    def test_prefix(self):
        self.assertEqual(self.dict.prefix, 'rs:unit_tests')
        self.assertEqual(self.dict.name, 'pickled_dict')
        self.assertEqual(self.dict.key_prefix, 'rs:unit_tests:pickled_dict')

    def test_incr_decr(self):
        self.reset()
        self.dict.incr('views', 1)
        self.assertEqual(self.dict['views'], str(1))
        self.dict.incr('views', 3)
        self.assertEqual(self.dict['views'], str(4))
        self.dict.decr('views', 1)
        self.assertEqual(self.dict['views'], str(3))


class TestUnserializedRedisDefaultDict(TestJSONRedisDefaultDict):
    dict = RedisDefaultDict("unserialized_dict", prefix="rs:unit_tests:")
    is_str = True

    def test_prefix(self):
        self.assertEqual(self.dict.prefix, 'rs:unit_tests')
        self.assertEqual(self.dict.name, 'unserialized_dict')
        self.assertEqual(
            self.dict.key_prefix, 'rs:unit_tests:unserialized_dict')


if __name__ == '__main__':
    unittest.main()
