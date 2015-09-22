#!/usr/bin/python3 -S
# -*- coding: utf-8 -*-
"""
   `Redis Set Tests`
--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--
   2015 Jared Lunde © The MIT License (MIT)
   http://github.com/jaredlunde

"""
import datetime
import time
import pickle
import unittest

from vital.debug import RandData, gen_rand_str
from redis_structures import StrictRedis, RedisSet


class TestJSONRedisSet(unittest.TestCase):
    set = RedisSet("json_set", prefix="rs:unit_tests:", serialize=True)
    set_2 = RedisSet("json_set_2", prefix="rs:unit_tests:", serialize=True)
    set_3 = RedisSet("json_set_3", prefix="rs:unit_tests:", serialize=True)
    is_str = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addCleanup(self.set.clear)
        self.addCleanup(self.set_2.clear)
        self.addCleanup(self.set_3.clear)

    def cast(self, obj):
        return str(obj) if self.is_str else obj

    def reset(self, count=10, type=int):
        self.set.clear()
        self.set_2.clear()
        self.set_3.clear()
        self.data = RandData(type).set(count)
        self.data_count = count
        self.set.update(self.data)
        self.set_2.update(self.data)

    def test_prefix(self):
        self.assertEqual(self.set.prefix, 'rs:unit_tests')
        self.assertEqual(self.set.name, 'json_set')
        self.assertEqual(self.set.key_prefix, 'rs:unit_tests:json_set')

    def test_add(self):
        self.reset(0)
        self.set.add("hello")
        self.assertIn("hello", self.set)

    def test_update(self):
        self.reset(0)
        data = {"it's", "great", "to", "be", "here"}
        self.set.update(data)
        self.assertSetEqual(self.set.all, data)

    def test_update_with_redis_set(self):
        self.reset(0)
        data = {"it's", "great", "to", "be", "here"}
        self.set_2.update(data)
        self.set.update(self.set_2)
        self.assertSetEqual(self.set.all, data)

    #: DIFF
    def test_difference(self):
        self.reset()
        data = {"it's", "great", "to", "be", "here"}
        self.set_2.update(data)
        self.assertSetEqual(self.set_2.difference(self.set.key_prefix), data)

    def test_difference_with_redis_set(self):
        self.reset()
        data = {"it's", "great", "to", "be", "here"}
        self.set_2.update(data)
        self.assertSetEqual(self.set_2.difference(self.set), data)

    def test_difference_op_with_redis_set(self):
        self.reset()
        data = {"it's", "great", "to", "be", "here"}
        self.set_2.update(data)
        self.assertSetEqual(
            (self.set_2 - self.set),
            set(map(self.cast, data)))

    def test_difference_iter(self):
        self.reset()
        data = {"it's", "great", "to", "be", "here"}
        self.set_2.update(data)
        self.assertSetEqual(set(self.set_2.diffiter(self.set.key_prefix)), data)

    def test_difference_iter_with_redis_set(self):
        self.reset()
        data = {"it's", "great", "to", "be", "here"}
        self.set_2.update(data)
        self.assertSetEqual(set(self.set_2.diffiter(self.set)), data)

    def test_difference_store(self):
        self.reset()
        data = {"it's", "great", "to", "be", "here"}
        self.set_2.update(data)
        self.set_2.diffstore(
            self.set_3, self.set.key_prefix)
        self.assertSetEqual(self.set_3.all, data)

    def test_difference_store_with_redis_set(self):
        self.reset()
        data = {"it's", "great", "to", "be", "here"}
        self.set_2.update(data)
        self.set_2.diffstore(self.set_3, self.set)
        self.assertSetEqual(self.set_3.all, data)

    #: INTER
    def test_intersection(self):
        self.reset()
        self.assertSetEqual(
            self.set_2.intersection(self.set.key_prefix),
            set(map(self.cast, self.data)))

    def test_intersection_op_with_redis_set(self):
        self.reset()
        self.assertSetEqual(
            (self.set_2 & self.set),
            set(map(self.cast, self.data)))

    def test_intersection_with_redis_set(self):
        self.reset()
        self.assertSetEqual(
            self.set_2.intersection(self.set),
            set(map(self.cast, self.data)))

    def test_intersection_iter(self):
        self.reset()
        self.assertSetEqual(set(
            self.set_2.interiter(self.set.key_prefix)),
            set(map(self.cast, self.data)))

    def test_intersection_iter_with_redis_set(self):
        self.reset()
        self.assertSetEqual(
            set(self.set_2.interiter(self.set)),
            set(map(self.cast, self.data)))

    def test_intersection_store(self):
        self.reset()
        self.set_2.interstore(self.set_3, self.set.key_prefix)
        self.assertSetEqual(
            self.set_3.all,
            set(map(self.cast, self.data)))

    def test_intersection_store_with_redis_set(self):
        self.reset()
        self.set_2.interstore(self.set_3, self.set)
        self.assertSetEqual(
            self.set_3.all,
            set(map(self.cast, self.data)))

    #: UNION
    def test_union(self):
        self.reset()
        self.set.update({"hello", "world"})
        self.assertSetEqual(
            self.set_2.union(self.set.key_prefix),
            self.set.all)

    def test_union_with_redis_set(self):
        self.reset()
        self.set.update({"hello", "world"})
        self.assertSetEqual(
            self.set_2.union(self.set),
            self.set.all)

    def test_union_op_with_redis_set(self):
        self.reset()
        self.set.update({"hello", "world"})
        self.assertSetEqual(
            (self.set_2 | self.set),
            self.set.all)

    def test_union_iter(self):
        self.reset()
        self.set.update({"hello", "world"})
        self.assertSetEqual(
            set(self.set_2.unioniter(self.set.key_prefix)),
            self.set.all)

    def test_union_iter_with_redis_set(self):
        self.reset()
        self.set.update({"hello", "world"})
        self.assertSetEqual(
            set(self.set_2.unioniter(self.set)),
            self.set.all)

    def test_union_store(self):
        self.reset()
        self.set.update({"hello", "world"})
        self.set_2.unionstore(self.set_3, self.set.key_prefix)
        self.assertSetEqual(
            self.set_3.all,
            self.set.all)

    def test_union_store_with_redis_set(self):
        self.reset()
        self.set.update({"hello", "world"})
        self.set_2.unionstore(self.set_3, self.set)
        self.assertSetEqual(
            self.set_3.all,
            self.set.all)

    def test_move(self):
        self.reset()
        self.set.add("hello")
        self.assertIn("hello", self.set)
        self.set.move("hello", self.set_2)
        self.assertNotIn("hello", self.set)
        self.assertIn("hello", self.set_2)

    def test_pop(self):
        self.reset()
        self.assertIsNotNone(self.set.pop())

    def test_remove(self):
        self.reset()
        self.set.add("hello")
        self.assertIn("hello", self.set)
        self.set.remove("hello")
        self.assertNotIn("hello", self.set)

    def test_scan(self):
        self.reset()
        new_keys = []
        cursor = '0'
        while cursor:
            cursor, keys = self.set.scan(count=1, cursor=int(cursor))
            if keys:
                new_keys.extend(keys)
        self.assertSetEqual(
            set(map(self.cast, self.data)), set(new_keys))

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


class TestPickledRedisSet(TestJSONRedisSet):
    set = RedisSet("pickled_set", prefix="rs:unit_tests:", serializer=pickle)
    set_2 = RedisSet(
        "pickled_set_2", prefix="rs:unit_tests:", serializer=pickle)
    set_3 = RedisSet(
        "pickled_set_3", prefix="rs:unit_tests:", serializer=pickle)

    def test_prefix(self):
        self.assertEqual(self.set.prefix, 'rs:unit_tests')
        self.assertEqual(self.set.name, 'pickled_set')
        self.assertEqual(self.set.key_prefix, 'rs:unit_tests:pickled_set')


class TestUnserializedRedisSet(TestJSONRedisSet):
    set = RedisSet("unserialized_set", prefix="rs:unit_tests:")
    set_2 = RedisSet("unserialized_set_2", prefix="rs:unit_tests:")
    set_3 = RedisSet("unserialized_set_3", prefix="rs:unit_tests:")
    is_str = True

    def test_prefix(self):
        self.assertEqual(self.set.prefix, 'rs:unit_tests')
        self.assertEqual(self.set.name, 'unserialized_set')
        self.assertEqual(
            self.set.key_prefix, 'rs:unit_tests:unserialized_set')


if __name__ == '__main__':
    unittest.main()
