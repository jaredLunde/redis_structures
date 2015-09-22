#!/usr/bin/python3 -S
# -*- coding: utf-8 -*-
"""
   `Redis List Tests`
--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--
   2015 Jared Lunde © The MIT License (MIT)
   http://github.com/jaredlunde

"""
import datetime
import time
import pickle
import unittest

from vital.debug import RandData, gen_rand_str
from redis_structures import StrictRedis, RedisList


class TestJSONRedisList(unittest.TestCase):
    list = RedisList("json_list", prefix="rs:unit_tests:", serialize=True)
    is_str = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addCleanup(self.list.clear)

    def cast(self, obj):
        return str(obj) if self.is_str else obj

    def test_prefix(self):
        self.assertEqual(self.list.prefix, 'rs:unit_tests')
        self.assertEqual(self.list.name, 'json_list')
        self.assertEqual(self.list.key_prefix, 'rs:unit_tests:json_list')

    def test_append(self):
        self.list.clear()
        self.list.append(1)
        self.assertIn(self.cast(1), self.list)
        self.assertEqual(len(self.list), 1)

    def test_extend(self):
        self.list.clear()
        data = RandData(str).list(10)
        self.list.extend(data)
        self.assertEqual(len(self.list), 10)
        for x in data:
            self.assertIn(x, self.list)

    def test_count(self):
        self.list.clear()
        data = [1, 2, 3, 3, 3, 4, 5, 6, 7, 7, 8, 9, 10]
        self.list.extend(data)
        self.assertEqual(self.list.count(self.cast(3)), 3)
        self.assertEqual(self.list.count(self.cast(7)), 2)
        self.assertEqual(self.list.count(self.cast(1)), 1)

    def test_index(self):
        self.list.clear()
        data = [1, 2, 3, 4]
        self.list.extend(data)
        self.assertEqual(self.list.index(self.cast(3)), 2)
        self.assertEqual(self.list.index(self.cast(4)), 3)
        self.assertEqual(self.list.index(self.cast(1)), 0)

    def test_clear(self):
        self.list.clear()
        data = [1, 2, 3, 4]
        self.list.extend(data)
        self.assertEqual(len(self.list), 4)
        self.list.clear()
        self.assertEqual(len(self.list), 0)

    def test_insert(self):
        self.list.clear()
        data = [1, 2, 3, 4]
        self.list.extend(data)
        self.list.insert(0, 5)
        self.assertEqual(self.list.index(self.cast(5)), 0)
        self.list.insert(4, 4)
        self.assertEqual(self.list.index(self.cast(4)), 4)

    def test_iter(self):
        self.list.clear()
        data = RandData(str).list(30)
        self.list.extend(data)
        checker = []
        add_check = checker.append
        for x in self.list.iter(0, 10):
            self.assertIn(x, data)
            add_check(x)
        self.assertListEqual(self.list.all, checker)

    def test_all(self):
        self.list.clear()
        data = RandData(str).list(10)
        self.list.extend(data)
        self.assertListEqual(self.list.all, data)

    def test_pop(self):
        self.list.clear()
        data = RandData(str).list(10)
        self.list.extend(data)
        self.assertEqual(self.list.pop(9), data[9])
        self.assertNotIn(data[9], self.list)

    def test_push(self):
        self.list.clear()
        data = RandData(str).list(10)
        self.list.extend(data)
        self.list.push(10)
        self.assertEqual(self.list[0], self.cast(10))

    def test_push(self):
        self.list.clear()
        self.list.extend([0, 1, 2, 3 , 4])
        self.assertIn(self.cast(4), self.list)
        self.list.remove(4)
        self.assertNotIn(self.cast(4), self.list)

    def test_reverse(self):
        self.list.clear()
        data = RandData(str).list(10)
        self.list.extend(data)
        self.list.reverse()
        self.assertListEqual(self.list.all, [x for x in reversed(data)])

    def test_reverse_iter(self):
        self.list.clear()
        data = RandData(str).list(10)
        self.list.extend(data)
        self.assertListEqual(
            [x for x in self.list.reverse_iter()], [x for x in reversed(data)])

    def test_reversed(self):
        self.list.clear()
        data = RandData(str).list(10)
        self.list.extend(data)
        self.assertListEqual(
            [x for x in reversed(self.list)], [x for x in reversed(data)])

    def test_trim(self):
        self.list.clear()
        data = RandData(str).list(10)
        self.list.extend(data)
        self.list.trim(2, 7)
        self.assertListEqual(self.list.all, data[2:8])

    def test_slice(self):
        self.list.clear()
        data = RandData(str).list(10)
        self.list.extend(data)
        self.assertListEqual(self.list[2:8], data[2:8])
        self.assertListEqual(self.list[:-1], data[:-1])
        self.assertListEqual(self.list[-4:-1], data[-4:-1])
        self.assertEqual(self.list[-3], data[-3])
        self.assertEqual(self.list[2], data[2])

    def test_getsetitem(self):
        self.list.clear()
        data = RandData(str).list(10)
        self.list.extend(data)
        test_str = gen_rand_str()
        self.list[2] = test_str
        self.assertEqual(self.list[2], test_str)

    def test_delitem(self):
        self.list.clear()
        data = RandData(str).list(10)
        self.list.extend(data)
        item = self.list[2]
        del self.list[2]
        self.assertNotIn(item, self.list)

    def test_pttl(self):
        self.list.clear()
        data = RandData(str).list(10)
        self.list.extend(data)
        self.list.set_pttl(1000)
        self.assertGreater(self.list.pttl(), 300)
        time.sleep(1)
        self.assertEqual(len(self.list), 0)

    def test_ttl(self):
        self.list.clear()
        data = RandData(str).list(10)
        self.list.extend(data)
        self.list.set_ttl(1)
        self.assertGreater(self.list.ttl(), 0.30)
        time.sleep(1)
        self.assertEqual(len(self.list), 0)

    def test_ttl(self):
        self.list.clear()
        data = RandData(str).list(10)
        self.list.extend(data)
        self.list.set_ttl(1)
        self.assertGreater(self.list.ttl(), 0.30)
        time.sleep(1)
        self.assertEqual(len(self.list), 0)

    def test_expire_at(self):
        self.list.clear()
        data = RandData(str).list(10)
        self.list.extend(data)
        expire_at = datetime.datetime.now() + datetime.timedelta(seconds=1)
        self.list.expire_at(expire_at.timestamp())
        self.assertGreater(self.list.ttl(), 0.30)
        time.sleep(2)
        self.assertEqual(len(self.list), 0)

    def test_pexpire_at(self):
        self.list.clear()
        data = RandData(str).list(10)
        self.list.extend(data)
        expire_at = datetime.datetime.now() + datetime.timedelta(seconds=1)
        self.list.pexpire_at(expire_at.timestamp() * 1000)
        self.assertGreater(self.list.pttl(), 300)
        time.sleep(2)
        self.assertEqual(len(self.list), 0)


class TestPickledRedisList(TestJSONRedisList):
    list = RedisList("pickled_list", prefix="rs:unit_tests:", serializer=pickle)

    def test_prefix(self):
        self.assertEqual(self.list.prefix, 'rs:unit_tests')
        self.assertEqual(self.list.name, 'pickled_list')
        self.assertEqual(self.list.key_prefix, 'rs:unit_tests:pickled_list')


class TestUnserializedRedisList(TestJSONRedisList):
    list = RedisList("unserialized_list", prefix="rs:unit_tests:")
    is_str = True

    def test_prefix(self):
        self.assertEqual(self.list.prefix, 'rs:unit_tests')
        self.assertEqual(self.list.name, 'unserialized_list')
        self.assertEqual(
            self.list.key_prefix, 'rs:unit_tests:unserialized_list')


if __name__ == '__main__':
    unittest.main()
