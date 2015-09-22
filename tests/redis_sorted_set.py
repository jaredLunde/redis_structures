#!/usr/bin/python3 -S
# -*- coding: utf-8 -*-
"""
   `Redis Sorted Set Tests`
--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--
   2015 Jared Lunde © The MIT License (MIT)
   http://github.com/jaredlunde

"""
import datetime
import time
import pickle
import unittest
from collections import OrderedDict

from vital.debug import RandData, gen_rand_str
from redis_structures import StrictRedis, RedisSortedSet


class TestJSONRedisSortedSet(unittest.TestCase):
    set = RedisSortedSet("json_sset", prefix="rs:unit_tests:", serialize=True)
    is_str = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addCleanup(self.set.clear)

    def cast(self, obj):
        return str(obj) if self.is_str else obj

    def reset(self, count=10, type=int):
        self.set.clear()
        self.data = OrderedDict([
            (k, v) for k, v in RandData(type).dict(count).items()])
        self.data_count = count
        self.set.update(self.data)

    def test_prefix(self):
        self.assertEqual(self.set.prefix, 'rs:unit_tests')
        self.assertEqual(self.set.name, 'json_sset')
        self.assertEqual(self.set.key_prefix, 'rs:unit_tests:json_sset')

    def test_add(self):
        self.reset(0)
        self.set.add(1.0, "hello")
        self.assertIn("hello", self.set)
        self.assertEqual(self.set['hello'], 1.0)

    def test_update(self):
        self.reset(0)
        data = {
            "hello": 1.0,
            "world": 2.0}
        self.set.update(data)
        self.assertDictEqual(dict(self.set.all), data)

    def test_count(self):
        self.reset(0)
        data = {
            "hello": 1.0,
            "world": 2.0,
            "hello2": 10.0,
            "hello3": 14.0}
        self.set.update(data)
        self.assertEqual(self.set.count(8, 10), 1)
        self.assertEqual(self.set.count(0, 10), 3)

    def test_incr_decr(self):
        self.reset(0)
        self.set.incr("hello")
        self.assertEqual(self.set["hello"], 1)
        self.set.incr("hello", 5)
        self.assertEqual(self.set["hello"], 6)
        self.set.decr("hello", 3)
        self.assertEqual(self.set["hello"], 3)
        self.set.decr("hello")
        self.assertEqual(self.set["hello"], 2)

    def test_cast(self):
        self.reset()
        self.set.incr("hello")
        self.assertIsInstance(self.set["hello"], self.set.cast)
        for x in self.set.values():
            self.assertIsInstance(x, self.set.cast)
        for k, x in self.set.itemsbyscore():
            self.assertIsInstance(x, self.set.cast)

    def test_index(self):
        self.reset(10)
        self.set.incr("hello")
        self.assertEqual(self.set.index('hello'), 0)
        self.set.incr("hello", 99999393933939939393993)
        self.assertEqual(self.set.index('hello'), 10)

    def test_keys(self):
        self.reset(0)
        data = OrderedDict([
            ('hello', 1.0),
            ('world', 2.0),
            ('hello2', 3.0),
            ('world2', 4.0),
            ('hello3', 5.0),
            ('world3', 6.0),
        ])
        self.set.update(data)
        self.assertListEqual(
            list(self.set.keys()), list(map(self.cast, data.keys())))

    def test_values(self):
        self.reset(0)
        data = OrderedDict([
            ('hello', 1.0),
            ('world', 2.0),
            ('hello2', 3.0),
            ('world2', 4.0),
            ('hello3', 5.0),
            ('world3', 6.0),
        ])
        self.set.update(data)
        self.assertListEqual(
            list(self.set.values()), list(data.values()))

    def test_slice(self):
        self.reset(0)
        data = OrderedDict([
            ('hello', 1.0),
            ('world', 2.0),
            ('hello2', 3.0),
            ('world2', 4.0),
            ('hello3', 5.0),
            ('world3', 6.0),
            ('hello4', 7.0),
            ('world4', 8.0),
            ('hello5', 9.0),
            ('world5', 10.0),
            (5, 11.0)
        ])
        self.set.update(data)
        keys = list(map(self.cast, data.keys()))
        self.assertListEqual(self.set[2:8], keys[2:8])
        self.assertListEqual(self.set[:-1], keys[:-1])
        self.assertListEqual(self.set[-4:-1], keys[-4:-1])
        self.assertEqual(self.set['hello2'], data['hello2'])
        self.assertEqual(self.set['world4'], data['world4'])
        self.assertEqual(self.set[5], data[5])

    def test_scan(self):
        self.reset()
        new_keys = []
        cursor = '0'
        while cursor:
            cursor, keys = self.set.scan(count=1, cursor=int(cursor))
            if keys:
                for key, val in keys:
                    self.assertIn(key, self.data)
                    self.assertIsInstance(val, self.set.cast)

    def test_iterscan(self):
        self.reset()
        new_keys = []
        for key, val in self.set.iterscan():
            self.assertIn(key, self.data)
            self.assertIsInstance(val, self.set.cast)

    def test_iterbyscore(self):
        self.reset()
        new_keys = []
        for key in self.set.iterbyscore():
            self.assertIn(key, self.data)

    def test_itemsbyscore(self):
        self.reset()
        new_keys = []
        for key, val in self.set.itemsbyscore():
            self.assertIn(key, self.data)
            self.assertIsInstance(val, self.set.cast)

    def test_getsetdel(self):
        self.reset(0)
        self.set['hello'] = 1.0
        self.assertIn('hello', self.set)
        self.assertEqual(self.set['hello'], self.set.cast(1.0))
        del self.set['hello']
        self.assertNotIn('hello', self.set)

    def test_remove(self):
        self.reset(0)
        self.set['hello'] = 1.0
        self.assertIn('hello', self.set)
        self.set.remove('hello')
        self.assertNotIn('hello', self.set)

    def test_len(self):
        self.reset()
        self.assertEqual(len(self.set), len(self.data))

    def test_rank(self):
        self.reset(0)
        data = OrderedDict([
            ('hello', 1.0),
            ('world', 2.0),
            ('hello2', 3.0),
            ('world2', 4.0),
            ('hello3', 5.0),
            ('world3', 6.0),
            ('hello4', 7.0),
            ('world4', 8.0),
            ('hello5', 9.0),
            ('world5', 10.0),
            (5, 11.0)
        ])
        self.set.update(data)
        self.assertEqual(self.set.rank('hello2'), 2)
        self.assertEqual(self.set.revrank('hello4'), 4)

    def test_pttl(self):
        self.reset()
        self.set.set_pttl(1000)
        self.assertGreater(self.set.pttl(), 300)
        time.sleep(1)
        self.assertEqual(len(self.set), 0)

    def test_ttl(self):
        self.reset()
        self.set.set_ttl(1)
        self.assertGreater(self.set.ttl(), 0.30)
        time.sleep(1)
        self.assertEqual(len(self.set), 0)

    def test_ttl(self):
        self.reset()
        self.set.set_ttl(1)
        self.assertGreater(self.set.ttl(), 0.30)
        time.sleep(1)
        self.assertEqual(len(self.set), 0)

    def test_expire_at(self):
        self.reset()
        expire_at = datetime.datetime.now() + datetime.timedelta(seconds=1)
        self.set.expire_at(expire_at.timestamp())
        self.assertGreater(self.set.ttl(), 0.30)
        time.sleep(2)
        self.assertEqual(len(self.set), 0)

    def test_pexpire_at(self):
        self.reset()
        expire_at = datetime.datetime.now() + datetime.timedelta(seconds=1)
        self.set.pexpire_at(expire_at.timestamp() * 1000)
        self.assertGreater(self.set.pttl(), 300)
        time.sleep(2)
        self.assertEqual(len(self.set), 0)
        

class TestPickledRedisSortedSet(TestJSONRedisSortedSet):
    set = RedisSortedSet(
        "pickled_sset", prefix="rs:unit_tests:", serializer=pickle)

    def test_prefix(self):
        self.assertEqual(self.set.prefix, 'rs:unit_tests')
        self.assertEqual(self.set.name, 'pickled_sset')
        self.assertEqual(self.set.key_prefix, 'rs:unit_tests:pickled_sset')


class TestUnserializedRedisSortedSet(TestJSONRedisSortedSet):
    set = RedisSortedSet("unserialized_sset", prefix="rs:unit_tests:")
    is_str = True

    def test_prefix(self):
        self.assertEqual(self.set.prefix, 'rs:unit_tests')
        self.assertEqual(self.set.name, 'unserialized_sset')
        self.assertEqual(
            self.set.key_prefix, 'rs:unit_tests:unserialized_sset')


class TestJSONRedisSortedSetInt(TestJSONRedisSortedSet):
    set = RedisSortedSet(
        "json_sset", cast=int, prefix="rs:unit_tests:", serializer=pickle)

    def test_prefix(self):
        self.assertEqual(self.set.prefix, 'rs:unit_tests')
        self.assertEqual(self.set.name, 'json_sset')
        self.assertEqual(self.set.key_prefix, 'rs:unit_tests:json_sset')


class TestPickledRedisSortedSetInt(TestJSONRedisSortedSet):
    set = RedisSortedSet(
        "pickled_sset", cast=int, prefix="rs:unit_tests:", serializer=pickle)

    def test_prefix(self):
        self.assertEqual(self.set.prefix, 'rs:unit_tests')
        self.assertEqual(self.set.name, 'pickled_sset')
        self.assertEqual(self.set.key_prefix, 'rs:unit_tests:pickled_sset')


class TestUnserializedRedisSortedSetInt(TestJSONRedisSortedSet):
    set = RedisSortedSet(
        "unserialized_sset", cast=int, prefix="rs:unit_tests:")
    is_str = True

    def test_prefix(self):
        self.assertEqual(self.set.prefix, 'rs:unit_tests')
        self.assertEqual(self.set.name, 'unserialized_sset')
        self.assertEqual(
            self.set.key_prefix, 'rs:unit_tests:unserialized_sset')


class TestJSONRedisSortedSetReversed(TestJSONRedisSortedSet):
    set = RedisSortedSet(
        "json_sset", reversed=True, prefix="rs:unit_tests:", serializer=pickle)

    def test_prefix(self):
        self.assertEqual(self.set.prefix, 'rs:unit_tests')
        self.assertEqual(self.set.name, 'json_sset')
        self.assertEqual(self.set.key_prefix, 'rs:unit_tests:json_sset')

    def test_index(self):
        self.reset(10)
        self.set.incr("hello")
        self.assertEqual(self.set.index('hello'), 10)
        self.set.incr("hello", 99999393933939939393993)
        self.assertEqual(self.set.index('hello'), 0)

    def test_keys(self):
        self.reset(0)
        data = OrderedDict([
            ('hello', 1.0),
            ('world', 2.0),
            ('hello2', 3.0),
            ('world2', 4.0),
            ('hello3', 5.0),
            ('world3', 6.0),
        ])
        self.set.update(data)
        self.assertListEqual(
            list(self.set.keys()), list(map(self.cast, reversed(data.keys()))))

    def test_values(self):
        self.reset(0)
        data = OrderedDict([
            ('hello', 1.0),
            ('world', 2.0),
            ('hello2', 3.0),
            ('world2', 4.0),
            ('hello3', 5.0),
            ('world3', 6.0),
        ])
        self.set.update(data)
        self.assertListEqual(
            list(self.set.values()), list(reversed(data.values())))

    def test_slice(self):
        self.reset(0)
        data = OrderedDict([
            ('hello', 1.0),
            ('world', 2.0),
            ('hello2', 3.0),
            ('world2', 4.0),
            ('hello3', 5.0),
            ('world3', 6.0),
            ('hello4', 7.0),
            ('world4', 8.0),
            ('hello5', 9.0),
            ('world5', 10.0),
            (5, 11.0)
        ])
        self.set.update(data)
        keys = list(map(self.cast, reversed(data.keys())))
        self.assertListEqual(self.set[2:8], keys[2:8])
        self.assertListEqual(self.set[:-1], keys[:-1])
        self.assertListEqual(self.set[-4:-1], keys[-4:-1])
        self.assertEqual(self.set['hello2'], data['hello2'])
        self.assertEqual(self.set['world4'], data['world4'])
        self.assertEqual(self.set[5], data[5])

    def test_rank(self):
        self.reset(0)
        data = OrderedDict([
            ('hello', 1.0),
            ('world', 2.0),
            ('hello2', 3.0),
            ('world2', 4.0),
            ('hello3', 5.0),
            ('world3', 6.0),
            ('hello4', 7.0),
            ('world4', 8.0),
            ('hello5', 9.0),
            ('world5', 10.0),
            (5, 11.0)
        ])
        self.set.update(data)
        self.assertEqual(self.set.rank('hello2'), 8)
        self.assertEqual(self.set.revrank('hello4'), 6)


class TestPickledRedisSortedSetReversed(TestJSONRedisSortedSetReversed):
    set = RedisSortedSet(
        "pickled_sset", reversed=True, prefix="rs:unit_tests:",
        serializer=pickle)

    def test_prefix(self):
        self.assertEqual(self.set.prefix, 'rs:unit_tests')
        self.assertEqual(self.set.name, 'pickled_sset')
        self.assertEqual(self.set.key_prefix, 'rs:unit_tests:pickled_sset')


class TestUnserializedRedisSortedSetReversed(TestJSONRedisSortedSetReversed):
    set = RedisSortedSet(
        "unserialized_sset", reversed=True, prefix="rs:unit_tests:")
    is_str = True

    def test_prefix(self):
        self.assertEqual(self.set.prefix, 'rs:unit_tests')
        self.assertEqual(self.set.name, 'unserialized_sset')
        self.assertEqual(
            self.set.key_prefix, 'rs:unit_tests:unserialized_sset')


if __name__ == '__main__':
    unittest.main()
