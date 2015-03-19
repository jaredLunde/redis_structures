#!/usr/bin/python3 -S
# -*- coding: utf-8 -*-
"""

  `Redis Structures`
   Redis data structures wrapped with Python
--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--
   2015 Jared Lunde © The MIT License (MIT)
   http://github.com/jaredlunde/redis_structures

"""
from redis import StrictRedis

try:
    from ujson import dumps
    from ujson import loads
except:
    from json import dumps
    from json import loads
    print(RuntimeWarning("`ujson` not found, using `json` instead"))

import hashlib
import functools

from collections import UserDict
from collections import OrderedDict
from collections import UserList

from vital.debug.debug2 import *


__all__ = (
 'BaseRedisStructure',
 'RedisMap',
 'RedisDict',
 'RedisDefaultDict',
 'RedisHash',
 'RedisDefaultHash',
 'RedisSet',
 'RedisList',
 'RedisSortedSet',
)

class BaseRedisStructure:
    __slots__ = (
        'name', 'prefix', '_key', '_loads', '_dumps',
        '_serialized', '_conn', '_default')

    def __init__(self, name="members", serializer=None, serialize=False,
      connection=None, prefix=None, config={}):
        self.name = name
        self.prefix = prefix
        self._key = "{}:{}".format(prefix.strip(":"), name).strip(":")
        self._loads = serializer.loads if serializer else loads
        self._dumps = serializer.dumps if serializer else dumps
        self._serialized = (serializer or False) or serialize
        self._conn = connection or StrictRedis(**config)
        self._default = None

    def __iter__(self): return iter(self.iter())

    def _redis_key(self, key):
        return "{}:{}".format(self._key, key)

    def get(self, key, default=None):
        try: return self[key]
        except KeyError:
            return default or self._default

    def clear(self):
        return self._conn.delete(self._key)

    def pttl(self): return self._conn.pttl(self._key)
    def ttl(self): return self._conn.ttl(self._key)
    def set_ttl(self, ttl): return self._conn.expire(self._key, ttl)
    def set_pttl(self, ttl=300): return self._conn.pexpire(self._key, ttl)
    def expire_at(self, _time):
        return self._conn.expireat(self._key, round(_time))

    def loads(self, val):
        if not self._serialized:
            return val
        try:
            return self._loads(val)
        except (ValueError, TypeError):
            return val

    def dumps(self, val):
        if not self._serialized:
            return val
        try:
            return self._dumps(val)
        except (ValueError, TypeError):
            return val


class RedisMap(BaseRedisStructure):
    """ Memory-persistent key/value-backed mapping
        For performance reasons it is recommended that if you
        need iter() methods like keys() you should use RedisHash
        and not RedisMap. The only advantage to RedisMap is a
        simple {key: value} get, set interface. The size of the
        map is unmonitored. """
    __slots__ = (
        "name", "prefix", "_key", "_loads", "_dumps", "_conn",
        "_default", "_serialized")

    def __init__(self, name="members", data={}, prefix="rs:datatype:map",
      **kwargs):
        super().__init__( name=name, prefix=prefix, **kwargs)
        self.update(data)

    @prepr(('name', 'cyan'), '_key', '_serialized', _doc=True)
    def __repr__(self): return

    def __setitem__(self, key, value):
        return self._conn.set(self._redis_key(key), self.dumps(value))

    def __getitem__(self, key):
        try:
            result = self.loads(self._conn.get(self._redis_key(key)))
            assert result
            return result
        except (AssertionError, TypeError):
            raise KeyError('Key `{}` not in `{}`'.format(key, self._key))

    def __delitem__(self, key):
        return self._conn.delete(self._redis_key(key))

    def __contains__(self, key):
        return self._conn.exists(self._redis_key(key))

    def __len__(self):
        raise AttributeError("`RedisMap` structures have no len property")

    def set(self, key, value):
        self[key] = value
    def setex(self, key, value, ttl=0):
        return self._conn.setex(self._redis_key(key),
            ttl, self.dumps(value))

    def incr(self, key, by):
        return self._conn.incrby(self._redis_key(key), 1)

    def decr(self, key, by):
        return self._conn.decrby(self._redis_key(key), 1)

    def mget(self, *keys):
        keys = map(self._redis_key, keys)
        return list(map(self.loads, self._conn.mget(*keys)))

    def update(self, data):
        if not data:
            return
        _rk, _dumps = self._redis_key, self.dumps
        data = self._conn.mset({
            _rk(key): _dumps(value)
            for key, value in data.items() })
        return data

    def pttl(self, key): return self._conn.pttl(self._redis_key(key))
    def ttl(self, key): return self._conn.ttl(self._redis_key(key))

    def set_ttl(self, key, ttl):
        return self._conn.expire(self._redis_key(key), ttl)

    def set_pttl(self, key, ttl):
        return self._conn.pexpire(self._redis_key(key), ttl)

    def expire_at(self, key, _time):
        return self._conn.expireat(self._redis_key(key), round(_time))

    def remove(self, *keys):
        return self._conn.delete(*keys)

    def scan(self, match="*", count=10000, cursor=0):
        return self._conn.scan(cursor=cursor, match="{}:{}".format(
            self._key, match), count=count)

    def iter(self, match="*", count=10000):
        replace_this = self._key+":"
        for key in self._conn.scan_iter(match="{}:{}".format(
          self._key, match), count=count):
            yield key.replace(replace_this, "", 1)

    keys = iter
    def values(self):
        for key, val in self.items():
            yield val

    def items(self):
        cursor = '0'
        _loads = self.loads
        _mget = self._conn.mget
        while cursor != 0:
            cursor, keys = self.scan(cursor=cursor)
            if keys:
                vals = _mget(*keys)
                for i, key in enumerate(keys):
                    yield (
                        key.replace(self._key+":", "", 1),
                        _loads(vals[i]))

    def clear(self, match="*", count=10000):
        cursor = '0'
        while cursor != 0:
            cursor, keys = self.scan(cursor=cursor, match=match, count=count)
            if keys:
                self.remove(*keys)
        return True


class RedisDict(BaseRedisStructure):
    """ Memory-persistent key/value-backed dictionaries
        For performance reasons it is recommended that if you
        need iter() methods like keys() you should use RedisHash
        and not RedisDict. The only advantage to RedisDict is a
        simple {key: value} get, set interface with the ability to
        call a len() on a given group of key/value pairs. """
    __slots__ = (
        "name", "prefix", "_key", "_size_mod", "_loads",
        "_dumps", "_conn", "_default", "_serialized")

    def __init__(self, name="members", data={}, prefix="rs:datatype:dict",
      size_mod=5, **kwargs):
        super().__init__(name=name, prefix=prefix, **kwargs)
        self._size_mod = size_mod #: 10**_size_mod is for estimated
                                  #  number of dicts within a given
                                  #  @prefix. It's purpose is to
                                  #  properly distribute the dict_size
                                  #  hash buckets. If your dict length
                                  #  starts to go over the bucket sizes,
                                  #  some memory optimization is lost
                                  #  in storing the key lengths.
                                  #: Default: 5 = 100,000 dicts
        self.update(data)

    @prepr(
        ('name', 'cyan'), '_key', '_bucket_key', '_serialized',
        ('num_keys', 'purple'), _doc=True)
    def __repr__(self): return
    def __str__(self): return self.__repr__()

    def __setitem__(self, key, value):
        pipe = self._conn.pipeline(transaction=False)
        pipe.set(self._redis_key(key), self.dumps(value))
        if key not in self: pipe.hincrby(self._bucket_key, self._key, 1)
        result = pipe.execute()
        return result[0]

    def __getitem__(self, key):
        try:
            result = self.loads(self._conn.get(self._redis_key(key)))
            assert result
            return result
        except (AssertionError, TypeError):
            raise KeyError('Key `{}` not in `{}`'.format(key, self._key))

    def __delitem__(self, key):
        pipe = self._conn.pipeline(transaction=False)
        pipe.delete(self._redis_key(key))
        if key in self: pipe.hincrby(self._bucket_key, self._key, -1)
        result = pipe.execute()
        return result[0]

    def __len__(self): return self.num_keys

    def __contains__(self, key):
        return self._conn.exists(self._redis_key(key))

    def __reversed__(self):
        raise RuntimeError('RedisDict does not support `reversed`')

    @property
    def num_keys(self):
        return int(self._conn.hget(self._bucket_key, self._key) or 0)

    @property
    def _bucket_key(self):
        """ Returns hash bucket key for the redis key """
        return "{}.size.{}".format(
            self.prefix, (self._hashed_key//1000)
            if self._hashed_key > 1000 else self._hashed_key)
    @property
    def _hashed_key(self):
        """ Returns 16-digit numeric hash of the redis key """
        return abs(int(hashlib.md5(
            self._key.encode('utf8')).hexdigest(), 16)) \
            % (10 ** self._size_mod)

    def pttl(self, key):
        raise AttributeError("RedisDict does not support `pttl`")
    def ttl(self, key):
        raise AttributeError("RedisDict does not support `ttl`")
    def set_ttl(self, key, ttl):
        raise AttributeError("RedisDict does not support `set_ttl`")
    def set_pttl(self, key, ttl):
        raise AttributeError("RedisDict does not support `set_pttl`")
    def expire_at(self, key, _time):
        raise AttributeError("RedisDict does not support `expire_at`")
    def setex(self, key, value, ttl=0):
        raise AttributeError("RedisDict does not support `setex`")

    def set(self, key, value):
        self[key] = value

    def mget(self, *keys):
        keys = map(self._redis_key, keys)
        return list(map(self.loads, self._conn.mget(*keys)))

    def incr(self, key, by):
        pipe = self._conn.pipeline(transaction=False)
        pipe.incrby(self._redis_key(key), 1)
        if key not in self: pipe.hincrby(self._bucket_key, self._key, 1)
        result = pipe.execute()
        return result[0]

    def decr(self, key, by):
        return self._conn.decrby(self._redis_key(key), 1)

    def iter(self, match="*", count=10000):
        replace_this = self._key+":"
        for key in self._conn.scan_iter(match="{}:{}".format(
          self._key, match), count=count):
            yield key.replace(replace_this, "", 1)

    keys = iter
    def values(self):
        for key, val in self.items():
            yield val

    def remove(self, *keys):
        for key in keys:
            try: del self[key]
            except KeyError:
                pass

    def pop(self, key):
        r = self[key]
        self.remove(key)
        return r

    def items(self):
        cursor = '0'
        while cursor != 0:
            cursor, keys = self.scan(cursor=cursor)
            if keys:
                vals = self._conn.mget(*keys)
                for i, key in enumerate(keys):
                    yield (
                        key.replace(self._key+":", "", 1),
                        self.loads(vals[i]))

    def update(self, data):
        result = None
        if data:
            pipe = self._conn.pipeline(transaction=False)
            _exists = pipe.exists
            for k in data.keys():
                _exists(k)
            exists = pipe.execute().count(True)
            print(exists)
            _rk, _dumps = self._redis_key, self.dumps
            data = {
                _rk(key): _dumps(value)
                for key, value in data.items() }
            pipe.mset(data)
            pipe.hincrby(self._bucket_key, self._key, len(data)-exists)
            result = pipe.execute()[0]
        return result

    def scan(self, match="*", count=10000, cursor=0):
        return self._conn.scan(cursor=cursor, match="{}:{}".format(
            self._key, match), count=count)

    def clear(self, match="*", count=10000):
        cursor = '0'
        while cursor != 0:
            cursor, keys = self.scan(cursor=cursor, match=match, count=count)
            if keys:
                pipe = self._conn.pipeline(transaction=False)
                pipe.delete(*keys)
                pipe.hincrby(self._bucket_key, self._key, len(keys)*-1)
                pipe.execute()
        self._conn.hdel(self._bucket_key, self._key)
        return True


class RedisDefaultDict(RedisDict):
    """ Memory-persistent key/value-backed dictionaries """
    __slots__ = (
        "name", "prefix", "_key", "_loads", "_dumps",
        "_conn", "_serialized")

    def __init__(self, name="members", data={}, default={},
      prefix="rs:datatype:dict", **kwargs):
        super().__init__(name=name, prefix=prefix, **kwargs)
        self._size_key = self._key+".size"
        self._default = default
        self.update(data)

    @prepr(
        ('name', 'cyan'), '_key', '_bucket_key', '_default', '_serialized',
        ('num_keys', 'purple'), _doc=True)
    def __repr__(self): return

    def __getitem__(self, key):
        try:
            result = self.loads(self._conn.get(self._redis_key(key)))
            assert result
            return result
        except (AssertionError, TypeError):
            return self._default


class RedisHash(BaseRedisStructure):
    """ Memory-persistent hashes, differs from dict because it uses the
        Redis Hash methods as opposed to simple set/get. In cases when the
        size is fewer than ziplist max entries(512 by defualt) and the value
        sizes are less than the defined ziplist max size(64 bytes), there are
        significant memory advantages to using RedisHash rather than
        RedisDict.

        Every RedisHash method is faster than RedisDict with the exception of
        get() and len(). All iter() methods are MUCH faster than
        RedisDict and iter() functions are safe here.

        It almost always makes sense to use this over RedisDict. """
    __slots__ = (
        "name", "prefix", "_key", "_loads", "_dumps", "_conn",
        "_default")

    def __init__(self, name="members", data={}, prefix="rs:datatype:hash",
      **kwargs):
        super().__init__(name=name, prefix=prefix, **kwargs)
        self.update(data)

    @prepr(
        ('name', 'cyan'), '_key', '_serialized', ('num_fields', 'purple'),
        _doc=True)
    def __repr__(self): return
    def __str__(self): return self.__repr__()

    def __setitem__(self, field, value):
        return self._conn.hset(self._key, field, self.dumps(value))

    def __getitem__(self, field):
        try:
            result = self.loads(self._conn.hget(self._key, field))
            assert result
            return result
        except (AssertionError, TypeError):
            raise KeyError('Key `{}` not in `{}`'.format(field, self._key))

    def __delitem__(self, field):
        return self._conn.hdel(self._key, field)

    def __len__(self): return self.num_fields

    def __contains__(self, field):
        return self._conn.hexists(self._key, field)

    def __reversed__(self):
        raise RuntimeError('RedisHash does not support `reversed`')

    @property
    def num_fields(self):
        return int(self._conn.hlen(self._key) or 0)

    def incr(self, field, by=1):
        return self._conn.hincrby(self._key, field, by)

    def decr(self, field, by=1):
        return self._conn.hdecrby(self._key, field, by)

    def iter(self, match="*", count=10000):
        for field, value in self._conn.hscan_iter(
          self._key, match=match, count=count):
            yield field

    def keys(self):
        for field in self._conn.hkeys(self._key):
            yield field

    def fields(self): return iter(self.keys())
    def values(self):
        for key, val in self.items():
            yield val

    def items(self, match="*", count=10000):
        for field, value in self._conn.hscan_iter(
          self._key, match=match, count=count):
            yield field, value

    def remove(self, *keys):
        return self._conn.hdel(self._key, *keys)

    def pop(self, key):
        r = self[key]
        self.remove(key)
        return r

    def update(self, data):
        result = None
        if data:
            _rk, _dumps = self._redis_key, self.dumps
            data = {
                _rk(key): _dumps(value)
                for key, value in data.items() }
            result = self._conn.hmset(self._key, data)
        return result

    def scan(self, match="*", count=10000, cursor=0):
        return self._conn.hscan(self._key, cursor=cursor,
            match=match, count=count)


class RedisDefaultHash(RedisHash):
    """ Memory-persistent key/value-backed dictionaries """
    __slots__ = ("name", "prefix", "_key", "_default", "_loads",
        "_dumps", "_conn", "_serialized")
    def __init__(self, name="members", data={}, default={},
      prefix="rs:datatype:dict", **kwargs):
        super().__init__(name=name, prefix=prefix, **kwargs)
        self._size_key = self._key+".size"
        self._default = default
        self.update(data)

    @prepr(
        ('name', 'cyan'), '_key', '_default', '_serialized',
        ('num_fields', 'purple'), _doc=True)
    def __repr__(self): return

    def __getitem__(self, field):
        try:
            result = self.loads(self._conn.hget(self._redis_key(key)))
            assert result
            return result
        except (AssertionError, TypeError):
            return self._default


class RedisList(BaseRedisStructure):
    """ Memory-persistent lists
        Because this is not a linked list, it isn't recommend that you
        utilize certain methods available on long lists.  For instance,
        checking whether or not a value is contained within the list does
        not perform well as there is no native function within Redis to do
        so. """
    __slots__ = (
        "name", "prefix", "_key", "_loads", "_dumps", "_conn",
        "_default", "_serialized")

    def __init__(self, name="items", data=[], prefix="rs:datatype:list",
      **kwargs):
        super().__init__(name=name, prefix=prefix, **kwargs)
        self.extend(data)

    @prepr(
        ('name', 'cyan'), '_key', '_serialized', ('size', 'purple'),
        _doc=True)
    def __repr__(self): return
    def __str__(self): return self.__repr__()

    def __len__(self): return self.size

    def __contains__(self, item):
        """ Not recommended for use on large lists due to time
            complexity, but it works"""
        for x in self.iter():
            if x == self.dumps(item):
                return True
        return False

    def __getitem__(self, index):
        #: LINDEX
        start = (index.start or 0) if isinstance(index, slice) else None
        stop = (index.stop or 0)-1 if isinstance(index, slice) else None
        if start is not None or stop is not None:
            if self._serialized:
                return list(map(self.loads,
                    self._conn.lrange(self._key, start, stop)))
            else:
                return self._conn.lrange(self._key, start, stop)
        else:
            return self.loads(self._conn.lindex(self._key, index))

    def __setitem__(self, index, value):
        #: LSET
        return self._conn.lset(self._key, index, self.dumps(value))

    def __delitem__(self):
        raise RuntimeError("Delete at index operations not allowed"+
            " in RedisList.")

    def __reversed__(self):
        """ Not recommended for use on large lists due to time
            complexity, but it works"""
        cursor = '0'
        start = -501
        stop = -1
        limit = 500
        _loads = self.loads
        while cursor:
            cursor = self._conn.lrange(self._key, start, stop)
            for x in reversed(cursor or []):
                yield _loads(x)
            start-=limit
            stop-=limit

    @property
    def size(self): return self._conn.llen(self._key)

    def pop(self, index=None):
        #LPOP, RPOP, LINDEX+DEL
        if index is None:
            return self.loads(self._conn.rpop(self._key))
        elif index == 0:
            return self.loads(self._conn.lpop(self._key))
        else:
            uuid = hash(self._key+str(index))
            r = self[index]
            self[index] = uuid
            self.remove(uuid)
            return r

    def extend(self, items):
        if items:
            if self._serialized:
                items = (self.dumps(item) for item in items)
            self._conn.rpush(self._key, *items)

    def append(self, *items):
        #: LRPUSH
        if self._serialized:
            items = map(self.dumps, items)
        self._conn.rpush(self._key, *items)

    def push(self, *items):
        #: LPUSH
        if self._serialized:
            items = (self.dumps(item) for item in items)
        self._conn.lpush(self._key, *items)

    def index(self, item):
        """ Not recommended for use on large lists due to time
            complexity, but it works"""
        _dumps = self.dumps
        for i, x in enumerate(self.iter()):
            if x == _dumps(item):
                return i
        return None

    def insert(self, where, refvalue, value):
        #LINSERT
        # @where "BEFORE" or "AFTER"
        # @refvalue "Your Item"
        # @value "Your item to insert"
        self._conn.linsert(self._key, where, refvalue, self.dumps(value))

    def remove(self, item, count=0):
        #LREM
        self._conn.lrem(self._key, count, self.dumps(item))

    def sort(self, start=None, num=None, by=None, get=None, desc=False,
      alpha=False, store=None, reverse=False):
        #: https://redis-py.readthedocs.org/en/latest/#redis.StrictRedis.sort
        return self._conn.sort(
            self._key, start=start, num=num, by=by, get=get,
            desc=(desc or reverse), alpha=alpha, store=store)

    def iter(self, start=0, stop=2000, count=2000):
        cursor = '0'
        _loads = self.loads
        while cursor:
            cursor = self._conn.lrange(self._key, start, stop)
            for x in cursor or []:
                yield _loads(x)
            start+=count
            stop+=count

    def trim(self, start, stop):
        #LTRIM
        return self._conn.ltrim(self._key, start, stop)


class RedisSet(BaseRedisStructure):
    """ Memory-persistent Sets
        This structure behaves nearly the same way that a Python set()
        does. All methods are production-ready. """
    __slots__ = (
        "name", "prefix", "_key", "_loads", "_dumps", "_conn",
        "_default", "_serialized")

    def __init__(self, name="members", data=set(), prefix="rs:datatype:set",
      **kwargs):
        super().__init__(name=name, prefix=prefix, **kwargs)
        self.update(data)

    @prepr(
        ('name', 'cyan'), '_key', '_serialized', ('members_size', 'purple'),
        _doc=True)
    def __repr__(self): return
    def __str__(self): return self.__repr__()

    def __len__(self): return self.members_size
    def __contains__(self, member):
        return self._conn.sismember(self._key, self.dumps(member))
    def __or__(self, other): return self.union(other)
    def __and__(self, other): return self.intersection(other)
    def __sub__(self, other): return self.diff(other)

    def _typesafe_others(self, others):
        _typesafe = self._typesafe
        return (_typesafe(other) for other in others)

    def _typesafe(self, other):
        return other._key if isinstance(other, RedisSet) \
            else other

    def _typesafe_members(self, members):
        return members.members if isinstance(members, RedisSet) \
            else members

    @property
    def members_size(self):
        return self._conn.scard(self._key)

    def add(self, member):
        #: SADD - Only adds single member
        member = self.dumps(member)
        return self._conn.sadd(self._key, member)

    def update(self, members):
        #: SADD - Adds multiple members
        members = self._typesafe_members(members)
        if self._serialized:
            members = map(self.dumps, members)
        if members:
            return self._conn.sadd(self._key, *members)

    def union(self, *others):
        #: SUNION
        others = self._typesafe_others(others)
        new_set = set()
        add_new = new_set.add
        for other in self._conn.sunion(self._key, *others):
            try:
                add_new(self.loads(other))
            except ValueError:
                add_new(other)
        return new_set

    def unionstore(self, destination, *others):
        #: SUNIONSTORE
        others = self._typesafe_others(others)
        destination = self._typesafe(destination)
        return self._conn.sunionstore(destination, self._key, *others)

    def intersection(self, *others):
        #: SINTER
        others = self._typesafe_others(others)
        new_set = set()
        add_new = new_set.add
        for other in self._conn.sinter(self._key, *others):
            try:
                add_new(self.loads(other))
            except ValueError:
                add_new(other)
        return new_set

    def interstore(self, destination, *others):
        #: SINTERSTORE
        others = self._typesafe_others(others)
        destination = self._typesafe(destination)
        return self._conn.interstore(destination, self._key, *others)

    def difference(self, *others):
        #: SDIFF
        others = self._typesafe_others(others)
        new_set = set()
        add_new = new_set.add
        for other in self._conn.sdiff(self._key, *others):
            try:
                add_new(self.loads(other))
            except ValueError:
                add_new(other)
        return new_set

    def diffstore(self, destination, *others):
        destination = self._typesafe(destination)
        return self._conn.sdiffstore(destination, self._key, *others)

    def move(self, destination, member):
        #: SMOVE
        destination = self._typesafe(destination)
        return self._conn.smove(self._key, destination, member)

    def get(self, count=1):
        return self.rand(count=count)

    def rand(self, count=1):
        #: SRANDMEMBER
        result = self._conn.srandmember(self._key, count)
        return {self.loads(r) for r in result} if count > 1 \
            else self.loads(result[0])

    def remove(self, *members):
        if self._serialized:
            members = map(self.dumps, members)
        return self._conn.srem(self._key, *members)

    @property
    def members(self):
        #: SMEMBERS
        if self._serialized:
            return set(map(self.loads, self._conn.smembers(self._key)))
        else:
            return self._conn.smembers(self._key)

    def pop(self):
        #: SPOP
        return self.loads(self._conn.spop(self._key))

    def scan(self, match="*", count=10000, cursor=0):
        #: SSCAN
        return self._conn.sscan(
            self._key, cursor=cursor, match=match, count=count)

    def iter(self, match="*", count=10000):
        _loads = self.loads
        for m in self._conn.sscan_iter(self._key, match="*", count=count):
            yield _loads(m)


class RedisSortedSet(BaseRedisStructure):
    """ An interesting, sort of hybrid dict/list structure.  You can get
        members from the sorted set by their index (rank) and  you can
        retrieve their associated values by their member names.
        You can iter() the set normally or in reverse.
        It is not possible to serialize the values of this structure,
        but you may serialize the member names. """
    __slots__ = (
        "name", "prefix", "_key", "_cast", "_loads", "_dumps",
        "_conn", "_default", "_serialized")

    def __init__(self, name="members", data={}, prefix="rs:datatype:set",
      cast=float, **kwargs):
        #: @data = [(key, value), (key, value)] like OrderedDict
        super().__init__(name=name, prefix=prefix, **kwargs)
        self._cast = cast
        if isinstance(data, (dict, UserDict, OrderedDict)):
            self.add(**data)
        else:
            self.add(*data)

    @prepr(
        ('name', 'cyan'), '_key', '_serialized', ('member_size', 'purple'),
        '_cast', _doc=True)
    def __repr__(self): return
    def __str__(self): return self.__repr__()

    def __setitem__(self, member, value):
        return self.add(value, member)

    def __getitem__(self, member):
        if isinstance(member, slice):
            #: Get by range
            start = member.start if member.start else 0
            stop = member.stop-1 if member.stop else -1
            return list(self.iter(start=start, stop=stop))
        elif isinstance(member, int):
            #: Get by index
            return list(self.iter(start=member, stop=member))[0]
        else:
            #: Get by member name
            try:
                return self._conn.zscore(self._key, self.dumps(member))
            except TypeError:
                raise KeyError('Member `{}` not in `{}`'.format(
                    field, self._key))

    def __delitem__(self, member):
        return self._conn.zrem(self._key, self.dumps(member))

    def __len__(self): return self.member_size

    def __contains__(self, member):
        return self._conn.zcard(self._key, self.dumps(member))

    def __reversed__(self): return self.iter(reverse=True)

    @property
    def member_size(self): return int(self._conn.zcard(self._key) or 0)

    def incr(self, member, by=1):
        return self._conn.zincrby(self._key, self.dumps(member), by)
    def decr(self, member, by=1):
        return self._conn.zdecrby(self._key, self.dumps(member), by)

    def add(self, *args, **kwargs):
        if args or kwargs:
            _dumps = self.dumps
            zargs = list(args)
            if args and self._serialized:
                # args format: value, key, value, key...
                zargs=[_dumps(x) if i % 2 == 1 else x
                    for i, x in enumerate(args)]
            if kwargs:
                # kwargs format: key=value, key=value
                zargs+=[
                    _dumps(x) if (i == 1 and self._serialized) else x
                    for y in kwargs.items() for i, x in enumerate(reversed(y)) ]
            return self._conn.zadd(self._key, *zargs)

    def remove(self, *members):
        self._conn.zrem(self._key, *members)

    def rank(self, member):
        return self._conn.zrank(self._key, self.dumps(member))

    def index(self, member):
        return self.rank(member)

    def count(self, min, max):
        return self._conn.zcount(self._key, min, max)

    def iter(self, start=0, stop=-1, withscores=False, reverse=False):
        """ By index
            ZRANGE """
        _loads = self.loads
        for member in self._conn.zrange(
          self._key, start=start, end=stop, withscores=withscores, desc=reverse,
          score_cast_func=self._cast):
            try:
                assert isinstance(member, tuple)
                yield (_loads(member[0]), member[1])
            except AssertionError:
                yield _loads(member)

    keys = iter
    def values(self, reverse=False):
        for member, value in self.items(reverse=reverse):
            yield value

    def items(self, reverse=False):
        """ By index, with scores """
        for member in self.iter(withscores=True, reverse=reverse):
            yield member

    def iterbyscore(self, min, max, start=None, num=None,
      withscores=False, reverse=False):
        zfunc = self._conn.zrangebyscore if not reverse \
            else self._conn.zrevrangebyscore
        _loads = self.loads
        for member in zfunc(
          self._key, min=min, max=max, start=start, num=num,
          withscores=withscores, score_cast_func=self._cast):
            try:
                assert isinstance(member, tuple)
                yield (_loads(member[0]), member[1])
            except AssertionError:
                yield _loads(member)

    def itemsbyscore(self, min, max, start=None, num=None, reverse=False):
        for member in self.iterbyscore(
          min, max, start, num, withscores=True, reverse=reverse):
            yield member

    def iterscan(self, match="*", count=10000):
        """ Much slower than iter(), but much more memory efficient if
            k/v's retrieved are one-offs """
        if self._serialized:
            _loads = lambda x: (self.loads[0], x[1])
            return map(_loads,
                self._conn.zscan_iter(self._key, match=match, count=count))
        else:
            return iter(self._conn.zscan_iter(
                self._key, match=match, count=count))

    def scan(self, match="*", count=10000, cursor=0):
        #: SSCAN
        if self._serialized:
            _loads = lambda x: (self.loads[0], x[1])
            return map(_loads, self._conn.zscan(
                self._key, cursor=cursor, match=match, count=count))
        else:
            return self._conn.zscan(
                self._key, cursor=cursor, match=match, count=count)
