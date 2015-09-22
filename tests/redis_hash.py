#!/usr/bin/python3 -S
# -*- coding: utf-8 -*-
"""
   `Redis Hash Tests`
--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--
   2015 Jared Lunde © The MIT License (MIT)
   http://github.com/jaredlunde

"""
import datetime
import time
import pickle
import unittest

from vital.debug import RandData, gen_rand_str
from redis_structures import StrictRedis, RedisHash


class TestJSONRedisHash(unittest.TestCase):
    hash = RedisHash("json_hash", prefix="rs:unit_tests:", serialize=True)
    is_str = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addCleanup(self.hash.clear)

    def cast(self, obj):
        return str(obj) if self.is_str else obj

    def reset(self, count=10, type=int):
        self.hash.clear()
        self.data = RandData(type).dict(count, 1)
        self.data_len = len(self.data)
        self.hash.update(self.data)

    def test_prefix(self):
        self.assertEqual(self.hash.prefix, 'rs:unit_tests')
        self.assertEqual(self.hash.name, 'json_hash')
        self.assertEqual(self.hash.key_prefix, 'rs:unit_tests:json_hash')

    def test_incr_decr(self):
        self.reset()
        self.hash.incr('views', 1)
        self.assertEqual(self.hash['views'], self.cast(1))
        self.hash.incr('views', 3)
        self.assertEqual(self.hash['views'], self.cast(4))
        self.hash.decr('views', 1)
        self.assertEqual(self.hash['views'], self.cast(3))

    def test_get(self):
        self.reset()
        self.hash["hello"] = "world"
        self.assertEqual(self.hash.get("hello"), 'world')
        self.assertEqual(self.hash.get('world', 'hello'), 'hello')

    def test_items(self):
        self.reset()
        self.assertDictEqual(
            {k: v for k, v in self.hash.items()},
            {k: self.cast(v) for k, v in self.data.items()})

    def test_values(self):
        self.reset()
        self.assertSetEqual(
            set(self.hash.values()),
            set(map(self.cast, self.data.values())))

    def test_iter(self):
        self.reset()
        self.assertSetEqual(
            set(k for k in self.hash.iter()),
            set(self.cast(k) for k in self.data.keys()))

    def test_iter_match(self):
        self.reset(count=10)
        self.assertSetEqual(
            set(k for k in self.hash.iter("a*")),
            set(self.cast(k) for k in self.data.keys() if k.startswith('a')))

    def test_mget(self):
        self.reset(0)
        self.hash.update({
            'test1': 1,
            'test2': 2,
            'test3': 3,
            'test4': 4,
            'test5': 5})
        self.assertListEqual(
            self.hash.mget('test2', 'test3', 'test4'),
            [self.cast(2), self.cast(3), self.cast(4)])

    def test_pop(self):
        self.reset()
        self.hash['hello'] = 'world'
        self.assertEqual(self.hash.pop('hello'), 'world')
        self.assertNotIn('hello', self.hash)

    def test_delete(self):
        self.reset()
        self.hash['hello'] = 'world'
        self.assertEqual(self.hash['hello'], 'world')
        del self.hash['hello']
        self.assertNotIn('hello', self.hash)

    def test_scan(self):
        self.reset()
        new_keys = []
        cursor = '0'
        while cursor:
            cursor, keys = self.hash.scan(count=1, cursor=int(cursor))
            if keys:
                new_keys.extend(keys)
        self.assertSetEqual(
            set(k for k in self.data.keys()), set(new_keys))

    def test_set(self):
        self.reset()
        self.hash.set("hello", "world")
        self.assertIn("hello", self.hash)

    def test_len(self):
        self.reset(100)
        self.assertEqual(len(self.hash), self.data_len)
        self.reset(1000)
        self.assertEqual(len(self.hash), self.data_len)
        rem = [k for k in list(self.hash)[:250]]
        self.hash.remove(*rem)
        self.assertEqual(len(self.hash), self.data_len - len(rem))

    def test_pttl(self):
        self.reset()
        self.hash.set_pttl(1000)
        self.assertGreater(self.hash.pttl(), 300)
        time.sleep(1)
        self.assertEqual(len(self.hash), 0)

    def test_ttl(self):
        self.reset()
        self.hash.set_ttl(1)
        self.assertGreater(self.hash.ttl(), 0.30)
        time.sleep(1)
        self.assertEqual(len(self.hash), 0)

    def test_ttl(self):
        self.reset()
        self.hash.set_ttl(1)
        self.assertGreater(self.hash.ttl(), 0.30)
        time.sleep(1)
        self.assertEqual(len(self.hash), 0)

    def test_expire_at(self):
        self.reset()
        expire_at = datetime.datetime.now() + datetime.timedelta(seconds=1)
        self.hash.expire_at(expire_at.timestamp())
        self.assertGreater(self.hash.ttl(), 0.30)
        time.sleep(2)
        self.assertEqual(len(self.hash), 0)

    def test_pexpire_at(self):
        self.reset()
        expire_at = datetime.datetime.now() + datetime.timedelta(seconds=1)
        self.hash.pexpire_at(expire_at.timestamp() * 1000)
        self.assertGreater(self.hash.pttl(), 300)
        time.sleep(2)
        self.assertEqual(len(self.hash), 0)


class TestPickledRedisHash(TestJSONRedisHash):
    hash = RedisHash("pickled_hash", prefix="rs:unit_tests:", serializer=pickle)

    def test_prefix(self):
        self.assertEqual(self.hash.prefix, 'rs:unit_tests')
        self.assertEqual(self.hash.name, 'pickled_hash')
        self.assertEqual(self.hash.key_prefix, 'rs:unit_tests:pickled_hash')

    def test_incr_decr(self):
        self.reset()
        self.hash.incr('views', 1)
        self.assertEqual(self.hash['views'], str(1))
        self.hash.incr('views', 3)
        self.assertEqual(self.hash['views'], str(4))
        self.hash.decr('views', 1)
        self.assertEqual(self.hash['views'], str(3))


class TestUnserializedRedisHash(TestJSONRedisHash):
    hash = RedisHash("unserialized_hash", prefix="rs:unit_tests:")
    is_str = True

    def test_prefix(self):
        self.assertEqual(self.hash.prefix, 'rs:unit_tests')
        self.assertEqual(self.hash.name, 'unserialized_hash')
        self.assertEqual(
            self.hash.key_prefix, 'rs:unit_tests:unserialized_hash')


if __name__ == '__main__':
    unittest.main()
