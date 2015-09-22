#!/usr/bin/python3 -S
# -*- coding: utf-8 -*-
"""
   `Redis Map Tests`
--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--
   2015 Jared Lunde © The MIT License (MIT)
   http://github.com/jaredlunde

"""
import datetime
import time
import pickle
import unittest

from vital.debug import RandData, gen_rand_str
from redis_structures import StrictRedis, RedisMap


class TestJSONRedisMap(unittest.TestCase):
    map = RedisMap("json_map", prefix="rs:unit_tests:", serialize=True)
    is_str = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addCleanup(self.map.clear)

    def cast(self, obj):
        return str(obj) if self.is_str else obj

    def reset(self, count=10, type=int):
        self.map.clear()
        self.data = RandData(type).dict(count, 1)
        self.data_count = count
        self.map.update(self.data)

    def test_prefix(self):
        self.assertEqual(self.map.prefix, 'rs:unit_tests')
        self.assertEqual(self.map.name, 'json_map')
        self.assertEqual(self.map.key_prefix, 'rs:unit_tests:json_map')

    def test_incr_decr(self):
        self.reset()
        self.map.incr('views', 1)
        self.assertEqual(self.map['views'], self.cast(1))
        self.map.incr('views', 3)
        self.assertEqual(self.map['views'], self.cast(4))
        self.map.decr('views', 1)
        self.assertEqual(self.map['views'], self.cast(3))

    def test_get(self):
        self.reset()
        self.map["hello"] = "world"
        self.assertEqual(self.map.get("hello"), 'world')
        self.assertEqual(self.map.get('world', 'hello'), 'hello')

    def test_get_key(self):
        self.assertEqual(
            self.map.get_key('views'),
            "{}:{}:{}".format(self.map.prefix, self.map.name, 'views'))

    def test_items(self):
        self.reset()
        self.assertDictEqual(
            {k: v for k, v in self.map.items()},
            {k: self.cast(v) for k, v in self.data.items()})

    def test_values(self):
        self.reset()
        self.assertSetEqual(
            set(self.map.values()),
            set(map(self.cast, self.data.values())))

    def test_iter(self):
        self.reset()
        self.assertSetEqual(
            set(k for k in self.map.iter()),
            set(self.cast(k) for k in self.data.keys()))

    def test_iter_match(self):
        self.reset(count=10)
        self.assertSetEqual(
            set(k for k in self.map.iter("a*")),
            set(self.cast(k) for k in self.data.keys() if k.startswith('a')))

    def test_mget(self):
        self.reset(0)
        self.map.update({
            'test1': 1,
            'test2': 2,
            'test3': 3,
            'test4': 4,
            'test5': 5})
        self.assertListEqual(
            self.map.mget('test2', 'test3', 'test4'),
            [self.cast(2), self.cast(3), self.cast(4)])

    def test_pop(self):
        self.reset()
        self.map['hello'] = 'world'
        self.assertEqual(self.map.pop('hello'), 'world')
        self.assertNotIn('hello', self.map)

    def test_delete(self):
        self.reset()
        self.map['hello'] = 'world'
        self.assertEqual(self.map['hello'], 'world')
        del self.map['hello']
        self.assertNotIn('hello', self.map)

    def test_scan(self):
        self.reset()
        new_keys = []
        cursor = '0'
        while cursor:
            cursor, keys = self.map.scan(count=1, cursor=int(cursor))
            if keys:
                new_keys.extend(keys)
        self.assertSetEqual(
            set(self.map.get_key(k) for k in self.data.keys()), set(new_keys))

    def test_set(self):
        self.reset()
        self.map.set("hello", "world")
        self.assertIn("hello", self.map)

    def test_setex(self):
        self.reset()
        self.map.setex("hello", "world", 1)
        self.assertIn("hello", self.map)
        time.sleep(1.25)
        self.assertNotIn("hello", self.map)
        self.map.psetex("hello", "world", 1000)
        self.assertIn("hello", self.map)
        time.sleep(1.25)
        self.assertNotIn("hello", self.map)


class TestPickledRedisMap(TestJSONRedisMap):
    map = RedisMap("pickled_map", prefix="rs:unit_tests:", serializer=pickle)

    def test_prefix(self):
        self.assertEqual(self.map.prefix, 'rs:unit_tests')
        self.assertEqual(self.map.name, 'pickled_map')
        self.assertEqual(self.map.key_prefix, 'rs:unit_tests:pickled_map')

    def test_incr_decr(self):
        self.reset()
        self.map.incr('views', 1)
        self.assertEqual(self.map['views'], str(1))
        self.map.incr('views', 3)
        self.assertEqual(self.map['views'], str(4))
        self.map.decr('views', 1)
        self.assertEqual(self.map['views'], str(3))


class TestUnserializedRedisMap(TestJSONRedisMap):
    map = RedisMap("unserialized_map", prefix="rs:unit_tests:")
    is_str = True

    def test_prefix(self):
        self.assertEqual(self.map.prefix, 'rs:unit_tests')
        self.assertEqual(self.map.name, 'unserialized_map')
        self.assertEqual(
            self.map.key_prefix, 'rs:unit_tests:unserialized_map')


if __name__ == '__main__':
    unittest.main()
