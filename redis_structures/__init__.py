#!/usr/bin/python3 -S
# -*- coding: utf-8 -*-
"""

  `Redis Structures`

   :build-status:https://travis-ci.org/jaredlunde/redis_structures
--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--
   ```Redis data structures wrapped with Python.```

   ``Benefits``
   * |Auto-serialization| using the serializer of your choice
   * |Auto response decoding| using the encoding of your choice
   * |Namespace maintanability| via prefix and name class properties
   * |Pythonic interface| provides nearly all of the same methods available to
     builtin Python structures, so there is a minimal learning curve
   * |Persistent| dictionaries, lists and sets which perhaps won't fit in the
     local memory, or that you merely wish to save

   ``Table of contents``
   * ``:class:RedisMap`` behaves similarly to #dict and is a wrapper for
     simple GET/SET Redis operations
   * ``:class:RedisDict`` behaves similarly to #dict and is a wrapper for
     simple GET/SET Redis operations
   * ``:class:RedisDefaultDict`` behaves similarly to
     :class:collections.defaultdict and is a wrapper for simple GET/SET
     Redis operations
   * ``:class:RedisHash`` behaves similarly to #dict and is a wrapper for
     Redis HASH operations
   * ``:class:RedisDefaultHash`` behaves similarly to
     :class:collections.defaultdict and is a wrapper for Redis HASH operations
   * ``:class:RedisSet`` behaves similarly to #set and is a wrapper for Redis
     SET operations
   * ``:class:RedisList`` behaves nearly identitical to #list and is a
     wrapper for Redis LIST operations
   * ``:class:RedisSortedSet`` behaves like a #list and #dict hybrid and is a
     wrapper for Redis Sorted Set operations

   ``Installation``
   - |pip install redis_structures|
   ```or```
   - |git clone https://github.com/jaredlunde/redis_structures.git|
     |python ./redis_structures/setup.py install|

   ``Package Requirements``
   * |redis-py| https://github.com/andymccurdy/redis-py

   ``System Requirements``
   * |Python 3.3+|

   ``Unit tests available``
   * https://github.com/jaredlunde/redis_structures/tree/master/tests

--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--·--
   2015 Jared Lunde © The MIT License (MIT)
   http://github.com/jaredlunde/redis_structures

"""
try:
    import ujson as json
except:
    import json

import pickle
import hashlib
import functools
from random import randint
from collections import UserDict, OrderedDict, UserList

from redis import StrictRedis, Redis
from redis_structures.debug import *


__version__ = "0.1.2"
__encoding__ = "utf8"
__license__ = 'MIT'
__author__ = "Jared Lunde"


__all__ = (
    'Redis',
    'StrictRedis',
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


class BaseRedisStructure(object):
    __slots__ = (
        'name', 'prefix', 'serializer', 'serialized', '_client', '_default',
        'encoding', 'decode_responses')

    def __init__(self, name, client=None, prefix='rs:data',
                 serializer=None, serialize=False, decode_responses=True,
                 encoding=None, **config):
        """ @name: unique name of the specific to the structure within @prefix,
                this gets appended to the eventual full redis key,
                i.e. |prefix:name:specific_key| for most structures
            @prefix: the prefix to use for your redis keys.
            @client: an instance of :class:redis.StrictRedis or
                :class:redis.Redis
            @serializer: optional serializer to use for your data before
                posting to your redis database. Must have a dumps and loads
                callable. :module:json is the default serializer
            @serialize: #bool True if you wish to serialize your data. This
                doesn't have to be set if @serializer is passed as an argument.
            @decode_responses: #bool whether or not to decode response
                keys and values from #bytes to #str
            @encoding: #str encoding to @decode_responses with
            @**config: keyword arguments to pass to :class:redis.StrictRedis
                if no @client is passed
        """
        self.name = name
        self.prefix = prefix.rstrip(":")
        self.serialized = (True if serializer is not None else False) or \
            serialize
        if serializer:
            self.serializer = serializer
        else:
            self.serializer = None if not self.serialized else json
        self._client = client or StrictRedis(**config)
        self._default = None
        if not encoding:
            conn = self._client.connection_pool.get_connection("")
            encoding = conn.encoding
            self._client.connection_pool.release(conn)
        self.encoding = encoding
        self.decode_responses = decode_responses

    def __iter__(self):
        return iter(self.iter())

    @property
    def key_prefix(self):
        """ The full redis key prefix with :prop:name included
            -> :prop:key_prefix 'self.prefix:self.name' ..
                from redis_structures import RedisMap

                rm = RedisMap("sessions", prefix="cool_app")
                rm.key_prefix
                # cool_app:sessions
            ..
        """
        return "{}:{}".format(self.prefix.rstrip(":"), self.name).rstrip(":")

    @property
    def _hashed_key(self):
        """ Returns 16-digit numeric hash of the redis key """
        return abs(int(hashlib.md5(
            self.key_prefix.encode('utf8')
        ).hexdigest(), 16)) % (10 ** (
            self._size_mod if hasattr(self, '_size_mod') else 5))

    def clear(self):
        """ Deletes :prop:key_prefix from the redis client """
        return self._client.delete(self.key_prefix)

    def ttl(self):
        """ Gets the time to live in seconds of :prop:key_prefix from the redis
            client
            -> #float time to live in seconds
        """
        return self._client.ttl(self.key_prefix)

    def pttl(self):
        """ Gets the time to live in ms of :prop:key_prefix from the redis
            client
            -> #float time to live in milliseconds
        """
        return self._client.pttl(self.key_prefix)

    def set_ttl(self, ttl):
        """ Sets the time to live in seconds of :prop:key_prefix from the redis
            client
            @ttl: time to live in seconds
        """
        return self._client.expire(self.key_prefix, ttl)

    def set_pttl(self, ttl):
        """ Sets the time to live in ms of :prop:key_prefix from the redis
            client
            @ttl: time to live in milliseconds
        """
        return self._client.pexpire(self.key_prefix, ttl)

    def expire_at(self, _time):
        """ Sets the expiration time of :prop:key_prefix to @_time
            @_time: absolute Unix timestamp (seconds since January 1, 1970)
        """
        return self._client.expireat(self.key_prefix, round(_time))

    def pexpire_at(self, _time):
        """ Sets the expiration time of :prop:key_prefix to @_time
            @_time: absolute Unix timestamp (milliseconds
                since January 1, 1970)
        """
        return self._client.pexpireat(self.key_prefix, round(_time))

    def _decode(self, obj):
        """ Decodes @obj using :prop:encoding if :prop:decode_responses """
        if self.decode_responses and isinstance(obj, bytes):
            try:
                return obj.decode(self.encoding)
            except UnicodeDecodeError:
                return obj
        return obj

    def _loads(self, string):
        """ If :prop:serialized is True, @string will be unserialized
            using :prop:serializer
        """
        if not self.serialized:
            return self._decode(string)
        if string is not None:
            try:
                return self.serializer.loads(string)
            except TypeError:
                #: catches bytes errors with the builtin json library
                return self.serializer.loads(self._decode(string))
            except pickle.UnpicklingError as e:
                #: incr and decr methods create issues when pickle serialized
                #  It's a terrible idea for a serialized instance
                #  to be performing incr and decr methods, but I think
                #  it makes sense to catch the error regardless
                decoded = self._decode(string)
                if decoded.isdigit():
                    return decoded
                raise pickle.UnpicklingError(e)

    def _dumps(self, obj):
        """ If :prop:serialized is True, @obj will be serialized
            using :prop:serializer
        """
        if not self.serialized:
            return obj
        return self.serializer.dumps(obj)


class RedisMap(BaseRedisStructure):
    """ ``RedisMap behaves like a python #dict, without a |__len__| method``
        ..
            import pickle
            from redis_structures import StrictRedis, RedisMap


            rm = RedisMap("practice", client=StrictRedis(), serializer=pickle)
            print(rm)
            '''
            <redis_structures.RedisMap(
                name=`practice`, key_prefix=`rs:map:practice`,
                serializer=<module 'pickle' from
                    '/usr/local/lib/python3.5.0/lib/python3.5/pickle.py'>
            ):0x7f9de1ebc0c8>
            '''
            rm.clear()

            rm["hello"] = "world"
            print(rm["hello"])
            # world

            print("hello" in rm)
            # True

            del rm["hello"]
            print("hello" in rm)
            # False

            print(rm.get("hello", "jared"))
            # jared

            print(rm.incr("views", 1))
            # 1
            print(rm.incr("views", 1))
            # 2

            rand = {
                'GNy': {
                    '6H7CVnxP7Y': 76855434120142179,
                    'Yi4tEyeYj': 75451199148498217,
                    'VkvI8Ju': 58509992008972989},
                'xsxb44': {
                    'm3PpVH': 11240718704668602,
                    'c2q': 51958730109782043,
                    'K4r8emcD6F': 65783979409080178},
                'pu': {
                    'T71nX': 84643776430801067,
                    'dLbW': 19553787616446251,
                    'qVCz':28313945830327169}
            }
            rm.update(rand)

            print(rm.all)
            '''
            {'views': '2', 'GNy': {'6H7CVnxP7Y': 76855434120142179, 'Yi4tEyeYj':
            75451199148498217, 'VkvI8Ju': 58509992008972989}, 'xsxb44':
            {'m3PpVH': 11240718704668602, 'c2q': 51958730109782043,
            'K4r8emcD6F': 65783979409080178}, 'pu': {'T71nX': 84643776430801067,
            'dLbW': 19553787616446251, 'qVCz': 28313945830327169}}
            '''
        ..
    """
    __slots__ = (
        'name', 'prefix', 'serializer', 'serialized', '_client', '_default',
        'encoding', 'decode_responses')

    def __init__(self, name, data=None, prefix="rs:map", **kwargs):
        """ Memory-persistent key/value-backed mapping
            For performance reasons it is recommended that if you
            need iter() methods like keys() you should use RedisHash
            and not RedisMap. The only advantage to RedisMap is a
            simple |{key: value}| get, set interface. The size of the
            map is unmonitored.

            :see::class:BaseRedisStructure
            @data: #dict or :class:RedisMap initial data to update this
                RedisMap with
        """
        super().__init__(name=name, prefix=prefix, **kwargs)
        self.update(data or {})

    @prepr(
        ('name', 'cyan'), 'key_prefix', 'serializer')
    def __repr__(self): return

    def __setitem__(self, key, value):
        """ -> #bool if @key set to @value """
        return self._client.set(self.get_key(key), self._dumps(value))

    def __getitem__(self, key):
        """ -> value for @key """
        try:
            result = self._loads(self._client.get(self.get_key(key)))
            assert result
            return result
        except (AssertionError, TypeError):
            raise KeyError('Key `{}` not in `{}`'.format(key, self.key_prefix))

    def __delitem__(self, key):
        """ -> #int number of keys removed (1 or 0) """
        return self._client.delete(self.get_key(key))

    def __contains__(self, key):
        """ -> #bool True if key exists """
        return self._client.exists(self.get_key(key))

    def get_key(self, key):
        """ @key: unique key within :prop:prefix
            -> :prop:key_prefix:@key ..
                from redis_structures import RedisMap

                rm = RedisMap("sessions", prefix="cool_app")
                rm.get_key("anXelFogNelaLElbz")
                # cool_app:sessions:anXelFogNelaLElbz
            ..
        """
        return "{}:{}".format(self.key_prefix, key)

    def get(self, key, default=None):
        """ Gets @key from :prop:key_prefix, defaulting to @default """
        try:
            return self[key]
        except KeyError:
            return default or self._default

    def set(self, key, value):
        """ :see::meth:__setitem__ """
        self[key] = value

    def setex(self, key, value, ttl=0):
        """ @ttl: time to live in seconds
            :see::meth:__setitem__
        """
        return self._client.setex(
            self.get_key(key), ttl, self._dumps(value))

    def psetex(self, key, value, ttl=0):
        """ @ttl: time to live in milliseconds
            :see::meth:__setitem__
        """
        return self._client.psetex(
            self.get_key(key), ttl, self._dumps(value))

    def incr(self, key, by=1):
        """ Increments @key by @by
            -> #int the value of @key after the increment """
        return self._client.incr(self.get_key(key), by)

    def decr(self, key, by=1):
        """ Decrements @key by @by
            -> #int the value of @key after the decrement """
        return self._client.decr(self.get_key(key), by)

    def mget(self, *keys):
        """ -> #list of values at the specified @keys """
        keys = list(map(self.get_key, keys))
        return list(map(self._loads, self._client.mget(*keys)))

    def update(self, data):
        """ Set given keys to their respective values
            @data: #dict or :class:RedisMap of |{key: value}| entries to set
        """
        if not data:
            return
        _rk, _dumps = self.get_key, self._dumps
        data = self._client.mset({
            _rk(key): _dumps(value)
            for key, value in data.items()})
    mset = update

    def ttl(self, key):
        """ Gets time to live in seconds for @key
            -> #int TTL seconds
        """
        return self._client.ttl(self.get_key(key))

    def pttl(self, key):
        """ Gets time to live in milliseconds for @key
            -> #int TTL milliseconds
        """
        return self._client.pttl(self.get_key(key))

    def set_ttl(self, key, ttl):
        """ Sets time to live for @key to @ttl seconds
            -> #bool True if the timeout was set
        """
        return self._client.expire(self.get_key(key), ttl)

    def set_pttl(self, key, ttl):
        """ Sets time to live for @key to @ttl milliseconds
            -> #bool True if the timeout was set
        """
        return self._client.pexpire(self.get_key(key), ttl)

    def expire_at(self, key, _time):
        """ Sets the expiration time of @key to @_time
            @_time: absolute Unix timestamp (seconds since January 1, 1970)
        """
        return self._client.expireat(self.get_key(key), round(_time))

    def pop(self, key):
        """ Removes @key from the instance, returns its value """
        r = self[key]
        self.remove(key)
        return r

    def remove(self, *keys):
        """ Deletes @keys from :prop:_client
            @*keys: keys to remove

            -> #int the number of keys that were removed
        """
        keys = list(map(self.get_key, keys))
        return self._client.delete(*keys)

    def scan(self, match="*", count=1000, cursor=0):
        """ Iterates the set of keys in :prop:key_prefix in :prop:_client
            @match: #str pattern to match after the :prop:key_prefix
            @count: the user specified the amount of work that should be done
                at every call in order to retrieve elements from the collection
            @cursor: the next cursor position

            -> #tuple (#int cursor position in scan, #list of full key names)
        """
        cursor, data = self._client.scan(
            cursor=cursor,
            match="{}:{}".format(self.key_prefix, match),
            count=count)
        return (cursor, list(map(self._decode, data)))

    def iter(self, match="*", count=1000):
        """ Iterates the set of keys in :prop:key_prefix in :prop:_client
            @match: #str pattern to match after the :prop:key_prefix
            @count: the user specified the amount of work that should be done
                at every call in order to retrieve elements from the collection

            -> yields redis keys within this instance
        """
        replace_this = self.key_prefix+":"
        for key in self._client.scan_iter(
           match="{}:{}".format(self.key_prefix, match), count=count):
            yield self._decode(key).replace(replace_this, "", 1)

    keys = iter

    def values(self):
        """ Iterates the set of values in :prop:key_prefix in :prop:_client

            -> yields redis values within this instance
        """
        for key, val in self.items():
            yield val

    def items(self):
        """ Iterates the set of |{key: value}| entries in :prop:key_prefix of
            :prop:_client

            -> yields redis (key, value) #tuples within this instance
        """
        cursor = '0'
        _loads = self._loads
        _mget = self._client.mget
        while cursor != 0:
            cursor, keys = self.scan(cursor=cursor)
            if keys:
                vals = _mget(*keys)
                for i, key in enumerate(keys):
                    yield (
                        key.replace(
                            self.key_prefix+":", "", 1),
                        _loads(vals[i])
                    )

    @property
    def all(self):
        """ !This can get very expensive!!

            -> #dict of all |{key: value}| entries in :prop:key_prefix of
                :prop:_client
        """
        return {k: v for k, v in self.items()}

    def clear(self, match="*", count=1000):
        """ Removes all |{key: value}| entries in :prop:key_prefix of
            :prop:_client
        """
        cursor = '0'
        while cursor != 0:
            cursor, keys = self.scan(cursor=cursor, match=match, count=count)
            if keys:
                self._client.delete(*keys)


class RedisDict(RedisMap):
    """ ..
            from redis_structures import StrictRedis, RedisDict

            rd = RedisDict("practice", client=StrictRedis(), serialize=True)
            print(rd)
            '''
            <redis_structures.RedisDict(
                name=`practice`,
                key_prefix=`rs:dict:practice`,
                _bucket_key=`rs:dict.size.51`,
                serializer=<module 'ujson' from
                    '/home/jared/git/ultrajson/ujson.cpython-35m-x86_64-linu'>,
                size=`4`
            ):0x7f6be62c02e8>
            '''
            rd.clear()

            rd["hello"] = "world"
            print(rd["hello"])
            # world

            print("hello" in rd)
            # True

            del rd["hello"]
            print("hello" in rd)
            # False

            print(rd.get("hello", "jared"))
            # jared

            print(rd.incr("views", 1))
            # 1
            print(rd.incr("views", 1))
            # 2

            rand = {
                'GNy': {
                    '6H7CVnxP7Y': 76855434120142179,
                    'Yi4tEyeYj': 75451199148498217,
                    'VkvI8Ju': 58509992008972989},
                'xsxb44': {
                    'm3PpVH': 11240718704668602,
                    'c2q': 51958730109782043,
                    'K4r8emcD6F': 65783979409080178},
                'pu': {
                    'T71nX': 84643776430801067,
                    'dLbW': 19553787616446251,
                    'qVCz': 28313945830327169}
            }
            rd.update(rand)

            print(rd.all)
            '''
            {'views': '2', 'GNy': {'6H7CVnxP7Y': 76855434120142179, 'Yi4tEyeYj':
            75451199148498217, 'VkvI8Ju': 58509992008972989}, 'xsxb44':
            {'m3PpVH': 11240718704668602, 'c2q': 51958730109782043,
            'K4r8emcD6F': 65783979409080178}, 'pu': {'T71nX': 84643776430801067,
            'dLbW': 19553787616446251, 'qVCz': 28313945830327169}}
            '''

            print(len(rd))
            # 4
        ..
    """
    __slots__ = (
        "name", "prefix", "_size_mod", "serializer", "_client", "_default",
        "serialized")

    def __init__(self, name, data=None, prefix="rs:dict", size_mod=5, **kwargs):
        """ Memory-persistent key/value-backed dictionaries
            For performance reasons it is recommended that if you
            need iter() methods like keys() you should use RedisHash
            and not RedisDict. The only advantage to RedisDict is a
            simple {key: value} get, set interface with the ability to
            call a len() on a given group of key/value pairs.

            :see::class:BaseRedisStructure.__init__
            @data: #dict or :class:RedisDict initial data to update this
                RedisDict with
            @size_mod: 10**_size_mod is for estimated number of dicts within
                a given @prefix. It's purpose is to properly distribute the
                dict_size hash buckets.
        """
        super().__init__(name=name, prefix=prefix, **kwargs)
        self._size_mod = size_mod
        #: 10**_size_mod is for estimated
        #  number of dicts within a given
        #  @prefix. It's purpose is to
        #  properly distribute the dict_size
        #  hash buckets. If your dict length
        #  starts to go over the bucket sizes,
        #  some memory optimization is lost
        #  in storing the key lengths.
        #: Default: 5 = 100,000 dicts
        self.update(data or {})

    @prepr(
        ('name', 'cyan'), 'key_prefix', '_bucket_key', 'serializer',
        ('size', 'purple'))
    def __repr__(self): return

    def __str__(self):
        return self.__repr__()

    def __setitem__(self, key, value):
        """ :see::meth:RedisMap.__setitem__ """
        pipe = self._client.pipeline(transaction=False)
        pipe.set(self.get_key(key), self._dumps(value))
        if key not in self:
            pipe.hincrby(self._bucket_key, self.key_prefix, 1)
        result = pipe.execute()
        return result[0]

    def __getitem__(self, key):
        """ :see::meth:RedisMap.__getitem__ """
        try:
            result = self._loads(self._client.get(self.get_key(key)))
            assert result
            return result
        except (AssertionError, TypeError):
            raise KeyError('Key `{}` not in `{}`'.format(key, self.key_prefix))

    def __delitem__(self, key):
        """ :see::meth:RedisMap.__delitem__ """
        pipe = self._client.pipeline(transaction=False)
        pipe.delete(self.get_key(key))
        if key in self:
            pipe.hincrby(self._bucket_key, self.key_prefix, -1)
        result = pipe.execute()
        return result[0]

    def __len__(self):
        """ -> #int number of keys in this instance """
        return self.size

    def __reversed__(self):
        raise RuntimeError('RedisDict does not support `reversed`')

    @property
    def size(self):
        """ -> #int number of keys in this instance """
        return int(self._client.hget(self._bucket_key, self.key_prefix) or 0)

    @property
    def _bucket_key(self):
        """ Returns hash bucket key for the redis key """
        return "{}.size.{}".format(
            self.prefix, (self._hashed_key//1000)
            if self._hashed_key > 1000 else self._hashed_key)

    def pttl(self, key):
        """ RedisDict does not support |pttl| """
        raise AttributeError("RedisDict does not support `pttl`")

    def ttl(self, key):
        """ RedisDict does not support |ttl| """
        raise AttributeError("RedisDict does not support `ttl`")

    def set_ttl(self, key, ttl):
        """ RedisDict does not support |set_ttl| """
        raise AttributeError("RedisDict does not support `set_ttl`")

    def set_pttl(self, key, ttl):
        """ RedisDict does not support |set_pttl| """
        raise AttributeError("RedisDict does not support `set_pttl`")

    def expire_at(self, key, _time):
        """ RedisDict does not support |expire_at| """
        raise AttributeError("RedisDict does not support `expire_at`")

    def setex(self, key, value, ttl=0):
        """ RedisDict does not support |setex| """
        raise AttributeError("RedisDict does not support `setex`")

    def incr(self, key, by=1):
        """ :see::meth:RedisMap.incr """
        pipe = self._client.pipeline(transaction=False)
        pipe.incr(self.get_key(key), by)
        if key not in self:
            pipe.hincrby(self._bucket_key, self.key_prefix, 1)
        result = pipe.execute()
        return result[0]

    def remove(self, *keys):
        """ Removes @keys from the instance """
        for key in keys:
            try:
                del self[key]
            except KeyError:
                pass

    def update(self, data):
        """ :see::meth:RedisMap.update """
        result = None
        if data:
            pipe = self._client.pipeline(transaction=False)
            for k in data.keys():
                pipe.exists(self.get_key(k))
            exists = pipe.execute()
            exists = exists.count(True)
            _rk, _dumps = self.get_key, self._dumps
            data = {
                _rk(key): _dumps(value)
                for key, value in data.items()}
            pipe.mset(data)
            pipe.hincrby(self._bucket_key, self.key_prefix, len(data)-exists)
            result = pipe.execute()[0]
        return result

    def clear(self, match="*", count=1000):
        """ :see:meth:RedisMap.clear """
        cursor = '0'
        pipe = self._client.pipeline(transaction=False)
        while cursor != 0:
            cursor, keys = self.scan(cursor=cursor, match=match, count=count)
            if keys:
                pipe.delete(*keys)
        pipe.hdel(self._bucket_key, self.key_prefix)
        pipe.execute()
        return True


class RedisDefaultDict(RedisDict):
    """ ..
            from redis_structures import StrictRedis, RedisDefaultDict

            rd = RedisDefaultDict(
                "practice", client=StrictRedis(), serialize=True)
            print(rd)
            '''
            <redis_structures.RedisDefaultDict(
                name=`practice`,
                key_prefix=`rs:defaultdict:practice`,
                _bucket_key=`rs:defaultdict.size.28`,
                _default={},
                serialized=True,
                size=`4`
            ):0x7f0d30a61278>
            '''
            rd.clear()

            rd["hello"] = "world"
            print(rd["hello"])
            # world

            print("hello" in rd)
            # True

            del rd["hello"]
            print("hello" in rd)
            # False

            print(rd["hello"])
            # {}

            print(rd.incr("views", 1))
            # 1
            print(rd.incr("views", 1))
            # 2

            rand = {
                'GNy': {
                    '6H7CVnxP7Y': 76855434120142179,
                    'Yi4tEyeYj': 75451199148498217,
                    'VkvI8Ju': 58509992008972989},
                'xsxb44': {
                    'm3PpVH': 11240718704668602,
                    'c2q': 51958730109782043,
                    'K4r8emcD6F': 65783979409080178},
                'pu': {
                    'T71nX': 84643776430801067,
                    'dLbW': 19553787616446251,
                    'qVCz': 28313945830327169}
            }
            rd.update(rand)

            print(rd.all)
            '''
            {'views': '2', 'GNy': {'6H7CVnxP7Y': 76855434120142179, 'Yi4tEyeYj':
            75451199148498217, 'VkvI8Ju': 58509992008972989}, 'xsxb44':
            {'m3PpVH': 11240718704668602, 'c2q': 51958730109782043,
            'K4r8emcD6F': 65783979409080178}, 'pu': {'T71nX': 84643776430801067,
            'dLbW': 19553787616446251, 'qVCz': 28313945830327169}}
            '''

            print(len(rd))
            # 4
        ..
    """
    __slots__ = (
        "name", "prefix", "_size_mod", "serializer", "_client", "_default",
        "serialized")

    def __init__(self, name, data={}, default=None,
                 prefix="rs:defaultdict", **kwargs):
        """ :see::meth:RedisDict.__init__
            @default: default value if a given key doesn't exist
        """
        super().__init__(name=name, prefix=prefix, **kwargs)
        self._default = default or dict()
        self.update(data)

    @prepr(
        ('name', 'cyan'), 'key_prefix', '_bucket_key', '_default',
        'serializer', ('size', 'purple'))
    def __repr__(self): return

    def __getitem__(self, key):
        """ Does not raise KeyError if @key doesn't exist, will return
            :prop:_default in that case.
            :see::RedisMap.__getitem__
        """
        return self.get(key)

    def get(self, key, default=None):
        """ Gets @key from :prop:key_prefix, defaulting to @default """
        try:
            result = self._loads(self._client.get(self.get_key(key)))
            assert result
            return result
        except AssertionError:
            return default or self._default


class RedisHash(BaseRedisStructure):
    """ ..
            from redis_structures import StrictRedis, RedisHash

            rh = RedisHash("practice", client=StrictRedis(), serialize=True)
            print(rh)
            '''
            <redis_structures.RedisHash(
                name=`practice`,
                key_prefix=`rs:hash:practice`,
                serializer=<module 'ujson' from '/home/jared/git/ultrajson/'>,
                size=0
            ):0x7f2f8590a178>
            '''
            rh.clear()

            rh["hello"] = "world"
            print(rh["hello"])
            # world

            print("hello" in rh)
            # True

            del rh["hello"]
            print("hello" in rh)
            # False

            print(rh.get("hello", "jared"))
            # jared

            print(rh.incr("views", 1))
            # 1
            print(rh.incr("views", 1))
            # 2

            rand = {
                'GNy': {
                    '6H7CVnxP7Y': 76855434120142179,
                    'Yi4tEyeYj': 75451199148498217,
                    'VkvI8Ju': 58509992008972989},
                'xsxb44': {
                    'm3PpVH': 11240718704668602,
                    'c2q': 51958730109782043,
                    'K4r8emcD6F': 65783979409080178},
                'pu': {
                    'T71nX': 84643776430801067,
                    'dLbW': 19553787616446251,
                    'qVCz': 28313945830327169}
            }
            rh.update(rand)

            print(rh.all)
            '''
            {'views': '2', 'GNy': {'6H7CVnxP7Y': 76855434120142179, 'Yi4tEyeYj':
            75451199148498217, 'VkvI8Ju': 58509992008972989}, 'xsxb44':
            {'m3PpVH': 11240718704668602, 'c2q': 51958730109782043,
            'K4r8emcD6F': 65783979409080178}, 'pu': {'T71nX': 84643776430801067,
            'dLbW': 19553787616446251, 'qVCz': 28313945830327169}}
            '''

            print(len(rh))
            # 4
        ..
    """
    __slots__ = (
        "name", "prefix", "serializer", "_client", "_default", "serialized")

    def __init__(self, name, data=None, prefix="rs:hash", **kwargs):
        """ Memory-persistent hashes, differs from dict because it uses the
            Redis Hash methods as opposed to simple set/get. In cases when the
            size is fewer than ziplist max entries(512 by defualt) and the value
            sizes are less than the defined ziplist max size(64 bytes), there
            are significant memory advantages to using RedisHash rather than
            RedisDict.

            Every RedisHash method is faster than RedisDict with the exception
            of get() and len(). All iter() methods are MUCH faster than
            RedisDict and iter() functions are safe here.

            It almost always makes sense to use this over RedisDict.

            :see::class:BaseRedisStructure.__init__
            @data: #dict initial data to update this RedisMap with
        """
        super().__init__(name=name, prefix=prefix, **kwargs)
        self.update(data or {})

    @prepr(
        ('name', 'cyan'), 'key_prefix', 'serializer', ('size', 'purple'))
    def __repr__(self): return

    def __str__(self):
        return self.__repr__()

    def __setitem__(self, field, value):
        """ :see::meth:RedisMap.__setitem__ """
        return self._client.hset(self.key_prefix, field, self._dumps(value))

    def __getitem__(self, field):
        """ :see::meth:RedisMap.__getitem__ """
        try:
            result = self._loads(self._client.hget(self.key_prefix, field))
            assert result
            return result
        except (AssertionError, TypeError):
            raise KeyError('Key `{}` not in `{}`'.format(
                field, self.key_prefix))

    def __delitem__(self, field):
        """ :see::meth:RedisMap.__delitem__ """
        return self._client.hdel(self.key_prefix, field)

    def __len__(self):
        """ :see::meth:RedisDict.__len__ """
        return self.size

    def __contains__(self, field):
        """ :see::meth:RedisMap.__contains__ """
        return self._client.hexists(self.key_prefix, field)

    def __reversed__(self):
        """ RedisHash does not support |reversed| """
        raise RuntimeError('RedisHash does not support `reversed`')

    def get_key(self, key):
        """ -> #tuple (hash_name, field name) """
        return (self.key_prefix, key)

    @property
    def size(self):
        """ :see::meth:RedisDict.size """
        return int(self._client.hlen(self.key_prefix) or 0)

    def get(self, key, default=None):
        """ Gets @key from :prop:key_prefix, defaulting to @default """
        try:
            return self[key]
        except KeyError:
            return default or self._default

    def set(self, key, value):
        """ :see::meth:__setitem__ """
        self[key] = value

    def incr(self, field, by=1):
        """ :see::meth:RedisMap.incr """
        return self._client.hincrby(self.key_prefix, field, by)

    def decr(self, field, by=1):
        """ :see::meth:RedisMap.decr """
        return self._client.hincrby(self.key_prefix, field, by * -1)

    def mget(self, *keys):
        """ -> #list of values at the specified @keys """
        return list(map(
            self._loads, self._client.hmget(self.key_prefix, *keys)))

    def remove(self, *keys):
        """ :see::meth:RedisMap.remove """
        return self._client.hdel(self.key_prefix, *keys)

    def pop(self, key):
        """ :see::meth:RedisDict.pop """
        r = self[key]
        self.remove(key)
        return r

    @property
    def all(self):
        """ -> #dict of all |{key: value}| entries in :prop:key_prefix of
                :prop:_client
        """
        return {
            self._decode(k): self._loads(v)
            for k, v in self._client.hgetall(self.key_prefix).items()
        }

    def update(self, data):
        """ :see::meth:RedisMap.update """
        result = None
        if data:
            _dumps = self._dumps
            data = {
                key: _dumps(value)
                for key, value in data.items()}
            result = self._client.hmset(self.key_prefix, data)
        return result

    def scan(self, match="*", count=1000, cursor=0):
        """ :see::meth:RedisMap.scan """
        cursor, results = self._client.hscan(
            self.key_prefix, cursor=cursor, match=match, count=count)
        return (cursor, list(map(self._decode, results)))

    def iter(self, match="*", count=1000):
        """ :see::meth:RedisMap.iter """
        for field, value in self._client.hscan_iter(
          self.key_prefix, match=match, count=count):
            yield self._decode(field)

    def items(self, match="*", count=1000):
        """ :see::meth:RedisMap.items """
        for field, value in self._client.hscan_iter(
          self.key_prefix, match=match, count=count):
            yield self._decode(field), self._loads(value)

    def keys(self):
        """ :see::meth:RedisMap.keys """
        for field in self._client.hkeys(self.key_prefix):
            yield self._decode(field)

    fields = keys

    def values(self):
        """ :see::meth:RedisMap.keys """
        for val in self._client.hvals(self.key_prefix):
            yield self._loads(val)

    def clear(self):
        """ :see::meth:RedisMap.clear """
        return self._client.delete(self.key_prefix)


class RedisDefaultHash(RedisHash):
    """ ..
            from redis_structures import StrictRedis, RedisDefaultHash

            rh = RedisDefaultHash("practice", client=StrictRedis(), serialize=True)
            print(rh)
            '''
            <redis_structures.RedisDefaultHash(
                name=`practice`,
                key_prefix=`rs:hash:practice`,
                _default={},
                serializer=<module 'ujson' from '/home/jared/git/ultrajson/'>,
                size=0
            ):0x7f2f8590a178>
            '''
            rh.clear()

            rh["hello"] = "world"
            print(rh["hello"])
            # world

            print("hello" in rh)
            # True

            del rh["hello"]
            print("hello" in rh)
            # False

            print(rh.get("hello", "jared"))
            # jared

            print(rh.incr("views", 1))
            # 1
            print(rh.incr("views", 1))
            # 2

            rand = {
                'GNy': {
                    '6H7CVnxP7Y': 76855434120142179,
                    'Yi4tEyeYj': 75451199148498217,
                    'VkvI8Ju': 58509992008972989},
                'xsxb44': {
                    'm3PpVH': 11240718704668602,
                    'c2q': 51958730109782043,
                    'K4r8emcD6F': 65783979409080178},
                'pu': {
                    'T71nX': 84643776430801067,
                    'dLbW': 19553787616446251,
                    'qVCz': 28313945830327169}
            }
            rh.update(rand)

            print(rh.all)
            '''
            {'views': '2', 'GNy': {'6H7CVnxP7Y': 76855434120142179, 'Yi4tEyeYj':
            75451199148498217, 'VkvI8Ju': 58509992008972989}, 'xsxb44':
            {'m3PpVH': 11240718704668602, 'c2q': 51958730109782043,
            'K4r8emcD6F': 65783979409080178}, 'pu': {'T71nX': 84643776430801067,
            'dLbW': 19553787616446251, 'qVCz': 28313945830327169}}
            '''

            print(len(rh))
            # 4
        ..
    """
    __slots__ = (
        "name", "prefix", "serializer", "_client", "_default", "serialized")

    def __init__(self, name, data=None, default={},
                 prefix="rs:dict", **kwargs):
        """ :see::meth:RedisHash.__init__
            @default: default value if a given key doesn't exist
        """
        super().__init__(name=name, prefix=prefix, **kwargs)
        self._default = default
        self.update(data or {})

    @prepr(
        ('name', 'cyan'), '_default', 'serialized',
        ('size', 'purple'))
    def __repr__(self): return

    def __getitem__(self, key):
        """ Does not raise KeyError if @key doesn't exist, will return
            :prop:_default in that case.
            :see::RedisMap.__getitem__
        """
        return self.get(key)

    def get(self, key, default=None):
        """ Gets @key from :prop:key_prefix, defaulting to @default """
        try:
            result = self._loads(self._client.hget(self.key_prefix, key))
            assert result
            return result
        except (AssertionError, KeyError):
            return default or self._default


class RedisList(BaseRedisStructure):
    """ ..
            from redis_structures import StrictRedis, RedisList

            rl = RedisList("practice", client=StrictRedis(), serialize=True)
            print(rl)
            '''
            <redis_structures.RedisList(
                name=`practice`,
                key_prefix=`rs:list:practice`,
                serializer=<module 'ujson' from '/home/jared/git/ultrajson/'>,
                size=`0`
            ):0x7f74a7187638>
            '''

            rl.extend([1, 2, 3, 4, 5])
            print(rl[:-1])
            # [1, 2, 3, 4]

            rl.reverse()
            print(rl.all)
            # [5, 4, 3, 2, 1]

            print(len(rl))
            # 5

            print(rl.pop())
            # 1

            rl.insert(1, 4)
            print(rl.count(4))
            # 2
            print(rl.index(4))
            # 1

            print([x for x in reversed(rl)])
            # [2, 3, 4, 4, 5]

            print(1 in rl, '+', 2 in rl)
            # False + True

            del rl[-1]
            print(rl.all)
            # [5, 4, 4, 3]

            rl2 = RedisList("practice2", client=StrictRedis(), serialize=True)
            rl2.extend(rl)
            print(rl2.all)
            # [5, 4, 4, 3]
        ..
    """
    __slots__ = (
        "name", "prefix", "serializer", "_client", "_default", "serialized")

    def __init__(self, name, data=None, prefix="rs:list", **kwargs):
        """ Memory-persistent lists
            Because this is not a linked list, it isn't recommend that you
            utilize certain methods available on long lists.  For instance,
            checking whether or not a value is contained within the list does
            not perform well as there is no native functionality within Redis
            to do so.

            :see::class:BaseRedisStructure.__init__
            @data: :class:RedisList, #list, #tuple or #generator with initial
                data to extend this RedisList with
        """
        super().__init__(name=name, prefix=prefix, **kwargs)
        self.extend(data or [])

    @prepr(
        ('name', 'cyan'), 'key_prefix', 'serializer', ('size', 'purple'))
    def __repr__(self): return

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        """ -> #int length of the list """
        return self.size

    def __contains__(self, item):
        """ Not recommended for use on large lists due to time
            complexity, but it works

            -> #bool True if the list contains @item
        """
        return False if self.index(item) is None else True

    def __getitem__(self, index):
        """ Gets item @index, also supports list splicing e.g. list[:-1],
            list[3:4], etc.

            -> item @index
        """
        start, stop = None, None
        if isinstance(index, slice):
            start = index.start or 0
            stop = (index.stop or 0) - 1
        if start is not None or stop is not None:
            #: Gets a slice
            return list(map(
                self._loads,
                self._client.lrange(self.key_prefix, start, stop)))
        else:
            #: Gets item at @index
            return self._loads(self._client.lindex(self.key_prefix, index))

    def __setitem__(self, index, value):
        """ Sets list item at @index to @value """
        self._client.lset(self.key_prefix, index, self._dumps(value))

    def __delitem__(self, index):
        """ Removes list item @index """
        self.pop(index)

    def __reversed__(self):
        """ Not recommended for use on large lists due to time
            complexity, but it works

            -> yields x in :meth:reverse_iter
        """
        for x in self.reverse_iter():
            yield x

    @property
    def size(self):
        """ -> #int length of the list """
        return self._client.llen(self.key_prefix)

    def reverse_iter(self, start=None, stop=None, count=2000):
        """ -> yields items of the list in reverse """
        cursor = '0'
        count = 1000
        start = start if start is not None else (-1 * count)
        stop = stop if stop is not None else -1
        _loads = self._loads
        while cursor:
            cursor = self._client.lrange(self.key_prefix, start, stop)
            for x in reversed(cursor or []):
                yield _loads(x)
            start -= count
            stop -= count

    def reverse(self):
        """ In place reverses the list. Very expensive on large data sets.
            The reversed list will be persisted to the redis :prop:_client
            as well.
        """
        tmp_list = RedisList(
            randint(0, 100000000), prefix=self.key_prefix,
            client=self._client, serializer=self.serializer,
            serialized=self.serialized)
        cursor = '0'
        count = 1000
        start = (-1 * count)
        stop = -1
        _loads = self._loads
        while cursor:
            cursor = self._client.lrange(self.key_prefix, start, stop)
            if cursor:
                tmp_list.extend(map(_loads, reversed(cursor)))
            start -= count
            stop -= count
        self._client.rename(tmp_list.key_prefix, self.key_prefix)
        tmp_list.clear()

    def pop(self, index=None):
        """ Removes and returns the item at @index or from the end of the list
            -> item at @index
        """
        if index is None:
            return self._loads(self._client.rpop(self.key_prefix))
        elif index == 0:
            return self._loads(self._client.lpop(self.key_prefix))
        else:
            _uuid = gen_rand_str(16, 24)
            r = self[index]
            self[index] = _uuid
            self.remove(_uuid)
            return r

    def extend(self, items):
        """ Adds @items to the end of the list
            -> #int length of list after operation
        """
        if items:
            if self.serialized:
                items = list(map(self._dumps, items))
            self._client.rpush(self.key_prefix, *items)

    def append(self, item):
        """ Adds @item to the end of the list
            -> #int length of list after operation
        """
        return self._client.rpush(self.key_prefix, self._dumps(item))

    def count(self, value):
        """ Not recommended for use on large lists due to time
            complexity, but it works. Use with caution.

            -> #int number of occurences of @value
        """
        cnt = 0
        for x in self:
            if x == value:
                cnt += 1
        return cnt

    def push(self, *items):
        """ Prepends the list with @items
            -> #int length of list after operation
        """
        if self.serialized:
            items = list(map(self._dumps, items))
        return self._client.lpush(self.key_prefix, *items)

    def index(self, item):
        """ Not recommended for use on large lists due to time
            complexity, but it works

            -> #int list index of @item
        """
        for i, x in enumerate(self.iter()):
            if x == item:
                return i
        return None

    def insert(self, index, value):
        """ Inserts @value before @index in the list.

            @index: list index to insert @value before
            @value: item to insert
            @where: whether to insert BEFORE|AFTER @refvalue

            -> #int new length of the list on success or -1 if refvalue is not
                in the list.
        """
        _uuid = gen_rand_str(24, 32)
        item_at_index = self[index]
        self[index] = _uuid
        uuid = _uuid
        _uuid = self._dumps(uuid)
        pipe = self._client.pipeline(transaction=True)  # Needs to be atomic
        pipe.linsert(
                self.key_prefix, "BEFORE", _uuid, self._dumps(value))
        pipe.linsert(
                self.key_prefix, "BEFORE", _uuid, item_at_index)
        results = pipe.execute()
        self.remove(uuid)
        return results[0]

    def remove(self, item, count=0):
        """ Removes @item from the list for @count number of occurences """
        self._client.lrem(self.key_prefix, count, self._dumps(item))

    '''def sort(self, start=None, num=None, by=None, get=None,
             desc=False, alpha=False, store=None, groups=False,
             in_place=False):
        """ Sort and return the list, set or sorted set at name.

            @start and @num: allow for paging through the sorted data
            @by: allows using an external key to weight and sort the items.
                Use an "*" to indicate where in the key the item value is
                located
            @get: allows for returning items from external keys rather than the
                sorted data itself.  Use an "*" to indicate where in the key
                the item value is located
            @desc: #bool sorts numbers from large to small
            @alpha: #bool allows for sorting lexicographically rather
                than numerically
            @store: #str new key name allows for storing the result of the sort
                into the key store
            @groups: if set to True and if get contains at least two
                elements, sort will return a list of tuples, each containing
                the values fetched from the arguments to get.
            @in_place: #bool True to sort the list in place, that is, it
                persists the sort to the redis instance and will not return
                the list

            -> sorted #list of items
        """
        store = store if not in_place else self.key_prefix
        result = self._client.sort(
            self.key_prefix, start=start, num=num, by=by, get=get,
            desc=desc, alpha=alpha, store=store, groups=groups)
        if in_place:
            return None
        else:
            return result'''

    def iter(self, start=0, count=1000):
        """ @start: #int cursor start position
            @stop: #int cursor stop position
            @count: #int buffer limit

            -> yields all of the items in the list
        """
        cursor = '0'
        _loads = self._loads
        stop = start + count
        while cursor:
            cursor = self._client.lrange(self.key_prefix, start, stop)
            for x in cursor or []:
                yield _loads(x)
            start += (count + 1)
            stop += (count + 1)

    @property
    def all(self):
        """ -> the entire list as a #list """
        return [x for x in self.iter()]

    def trim(self, start, end):
        """ Trim the list, removing all values not within the slice
            between @start and @end.

            @start and @end can be negative numbers just like python slicing
            notation.

            @start: #int start position
            @end: #int end position

            -> result of :meth:redis.StrictRedis.ltrim
        """
        return self._client.ltrim(self.key_prefix, start, end)


class RedisSet(BaseRedisStructure):
    """ ..
            from redis_structures import StrictRedis, RedisSet

            rs = RedisSet("practice", client=StrictRedis(), serialize=True)
            rs2 = RedisSet("practice2", client=StrictRedis(), serialize=True)

            print(rs, "\\n", rs2)
            '''
            <redis_structures.RedisSet(
                name=`practice`,
                key_prefix=`rs:set:practice`,
                serializer=<module 'ujson' from '/home/jared/git/ultrajson/'>,
                size=`0`
            ):0x7f957e9cb6d0>
            <redis_structures.RedisSet(
                name=`practice2`,
                key_prefix=`rs:set:practice2`,
                serializer=<module 'ujson' from '/home/jared/git/ultrajson/'>,
                size=`0`
            ):0x7f957e5a9df0>
            '''

            data = {"hello", "goodbye", "bonjour", "au revoir"}

            rs.update(data)
            rs2.update(rs)
            rs2.add('bienvenue')

            print(rs.union(rs2))
            # {'goodbye', 'hello', 'bonjour', 'au revoir', 'bienvenue'}
            print(rs.intersection(rs2))
            # {'goodbye', 'hello', 'au revoir', 'bonjour'}
            print(rs.members)
            print(rs2.members)
            # {'goodbye', 'hello', 'au revoir', 'bonjour'}
            # {'goodbye', 'hello', 'bonjour', 'au revoir', 'bienvenue'}

            for o in rs2.diffiter(rs):
                print(o)
            # bienvenue

            print(rs2.move('bienvenue', rs))
            # True
            print(rs.all)
            print(rs2.all)
            # {'goodbye', 'hello', 'bonjour', 'au revoir', 'bienvenue'}
            # {'goodbye', 'hello', 'au revoir', 'bonjour'}

            print(rs.get(2))
            # {'hello', 'au revoir'}

            rs.remove('bienvenue')
            print(rs.all)
            # {'goodbye', 'hello', 'au revoir', 'bonjour'}

            print("hello" in rs)
            # True

            print(rs.pop())
            # goodbye

            rs.clear()
            rs2.clear()
        ..
    """
    __slots__ = (
        "name", "prefix", "serializer", "_client", "_default", "serialized")

    def __init__(self, name, data=None, prefix="rs:set", **kwargs):
        """ Memory-persistent Sets
            This structure behaves nearly the same way that a Python set()
            does. All methods are production-ready.

            :see::class:BaseRedisStructure.__init__
            @data: #set or :class:RedisSet to initally load into the set
        """

        super().__init__(name=name, prefix=prefix, **kwargs)
        self.update(data or set())

    @prepr(
        ('name', 'cyan'), 'key_prefix', 'serializer', ('size', 'purple'))
    def __repr__(self): return

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        """ -> #int number of members in the set """
        return self.size

    def __contains__(self, member):
        """ -> #bool True if @member is in the set """
        return self._client.sismember(self.key_prefix, self._dumps(member))

    def __or__(self, other):
        """ :see::meth:union """
        return self.union(other)

    def __and__(self, other):
        """ :see::meth:intersection """
        return self.intersection(other)

    def __sub__(self, other):
        """ :see::meth:difference """
        return self.difference(other)

    def _typesafe_others(self, others):
        """ Gets the keyname from :class:RedisSet objects when they are passed
            instead of #str redis keys for @others

            @others: #iterable of other #str redis keys or
                :class:RedisSet objects

            -> #list of other keys
        """
        return list(map(self._typesafe, others))

    def _typesafe(self, other):
        """ -> :prop:RedisSet.key_prefix if @other is :class:RedisSet, else
                @other
        """
        return other.key_prefix if isinstance(other, RedisSet) else other

    @property
    def size(self):
        """ -> #int number of members in the set """
        return self._client.scard(self.key_prefix)

    def add(self, member):
        """ Adds @member to the set
            -> #int the number of @members that were added to the set,
                excluding pre-existing members (1 or 0)
        """
        return self._client.sadd(self.key_prefix, self._dumps(member))

    def update(self, members):
        """ Adds @members to the set
            @members: a :class:RedisSet object or #set

            -> #int the number of @members that were added to the set,
                excluding pre-existing members
        """
        if isinstance(members, RedisSet):
            size = self.size
            return (self.unionstore(
                self.key_prefix, members.key_prefix) - size)
        if self.serialized:
            members = list(map(self._dumps, members))
        if members:
            return self._client.sadd(self.key_prefix, *members)
        return 0

    def union(self, *others):
        """ Calculates union between sets
            @others: one or several :class:RedisSet objects or #str redis set
                keynames

            -> #set of new set members
        """
        others = self._typesafe_others(others)
        return set(map(
            self._loads, self._client.sunion(self.key_prefix, *others)))

    def unioniter(self, *others):
        """ The same as :meth:union, but returns iterator instead of #set

            @others: one or several :class:RedisSet objects or #str redis set
                keynames

            -> yields members of the resulting set
        """
        others = self._typesafe_others(others)
        for other in self._client.sunion(self.key_prefix, *others):
            yield self._loads(other)

    def unionstore(self, destination, *others):
        """ The same as :meth:union, but stores the result in @destination

            @destination: #str keyname or :class:RedisSet
            @others: one or several #str keynames or :class:RedisSet objects

            -> #int number of items in the resulting set
        """
        others = self._typesafe_others(others)
        destination = self._typesafe(destination)
        return self._client.sunionstore(destination, self.key_prefix, *others)

    def intersection(self, *others):
        """ Calculates the intersection of all the given sets, that is, members
            which are present in all given sets.

            @others: one or several #str keynames or :class:RedisSet objects

            -> #set of resulting intersection between @others and this set
        """
        others = self._typesafe_others(others)
        return set(map(
            self._loads, self._client.sinter(self.key_prefix, *others)))

    def interiter(self, *others):
        """ The same as :meth:intersection, but returns iterator instead of #set

            @others: one or several #str keynames or :class:RedisSet objects

            -> yields members of the resulting set
        """
        others = self._typesafe_others(others)
        for other in self._client.sinter(self.key_prefix, *others):
            yield self._loads(other)

    def interstore(self, destination, *others):
        """ The same as :meth:intersection, but stores the resulting set
            @destination

            @destination: #str keyname or :class:RedisSet
            @others: one or several #str keynames or :class:RedisSet objects

            -> #int number of members in resulting set
        """
        others = self._typesafe_others(others)
        destination = self._typesafe(destination)
        return self._client.sinterstore(destination, self.key_prefix, *others)

    def difference(self, *others):
        """ Calculates the difference between this set and @others

            @others: one or several #str keynames or :class:RedisSet objects

            -> set resulting from the difference between the first set and
                all @others.
        """
        others = self._typesafe_others(others)
        return set(map(
            self._loads, self._client.sdiff(self.key_prefix, *others)))

    def diffiter(self, *others):
        """ The same as :meth:difference, but returns iterator instead of #set

            @others: one or several #str keynames or :class:RedisSet objects

            -> yields members resulting from the difference between the first
                set and all @others.
        """
        others = self._typesafe_others(others)
        for other in self._client.sdiff(self.key_prefix, *others):
            yield self._loads(other)

    def diffstore(self, destination, *others):
        """ The same as :meth:difference, but stores the resulting set
            @destination

            @destination: #str keyname or :class:RedisSet
            @others: one or several #str keynames or :class:RedisSet objects

            -> #int number of members in resulting set
        """
        others = self._typesafe_others(others)
        destination = self._typesafe(destination)
        return self._client.sdiffstore(destination, self.key_prefix, *others)

    def move(self, member, destination):
        """ Moves @member from this set to @destination atomically

            @member: a member of this set
            @destination: #str redis keyname or :class:RedisSet object

            -> #bool True if the member was moved
        """
        destination = self._typesafe(destination)
        return self._client.smove(
            self.key_prefix, destination, self._dumps(member))

    def get(self, count=1):
        """ :see::meth:rand """
        return self.rand(count=count)

    def rand(self, count=1):
        """ Gets @count random members from the set
            @count: #int number of members to return

            -> @count set members
        """
        result = self._client.srandmember(self.key_prefix, count)
        return set(map(self._loads, result))

    def remove(self, *members):
        """ Removes @members from the set
            -> #int the number of members that were removed from the set
        """
        if self.serialized:
            members = list(map(self._dumps, members))
        return self._client.srem(self.key_prefix, *members)

    @property
    def members(self):
        """ -> #set of all members in the set """
        if self.serialized:
            return set(map(
                self._loads, self._client.smembers(self.key_prefix)))
        else:
            return set(map(
                self._decode, self._client.smembers(self.key_prefix)))

    all = members

    def pop(self):
        """ Removes a random member and returns it
            -> random set member
        """
        return self._loads(self._client.spop(self.key_prefix))

    def scan(self, match="*", count=1000, cursor=0):
        """ :see::RedisMap.scan """
        cursor, data = self._client.sscan(
            self.key_prefix, cursor=cursor, match=match, count=count)
        return (cursor, set(map(self._loads, data)))

    def iter(self, match="*", count=1000):
        """ Iterates the set members in :prop:key_prefix of :prop:_client
            @match: #str pattern to match items by
            @count: the user specified the amount of work that should be done
                at every call in order to retrieve elements from the collection

            -> yields members of the set
        """
        _loads = self._loads
        for m in self._client.sscan_iter(
           self.key_prefix, match="*", count=count):
            yield _loads(m)


class RedisSortedSet(BaseRedisStructure):
    """ ..
            from redis_structures import StrictRedis, RedisSortedSet

            rs = RedisSortedSet(
                "practice", client=StrictRedis(), serialize=True)

            print(rs)
            '''
            <redis_structures.RedisSortedSet(
                name=`practice`,
                key_prefix=`rs:sorted_set:practice`,
                serializer=<module 'ujson' from '/home/jared/git/ultrajson/'>,
                size=`0`,
                cast=<class 'float'>,
                reversed=False
            ):0x7fd935906f60>
            '''
            d = (2, 1, 4, 3)
            rs.add(*d)

            print(rs[3])
            # 4.0
            print(rs[1:2])
            # [3]

            d = {'hello': 3, 'world': 4}
            rs.add(**d)

            rs.incr('hello', 1.5)
            print(rs['hello'])
            # 4.5

            print(rs.rank('hello'))
            # 3
            print(rs.revrank('hello'))
            # 0

            rs[3] = 5
            print(rs[3])
            # 5.0

            del rs[3]
            try:
                rs[3]
            except KeyError as e:
                print(e)
                # 'Member `3` not in `rs:sorted_set:practice`'

            print(len(rs))
            # 3

            print([val for val in rs.values()])
            # [2.0, 4.0, 4.5]

            print([val for val in rs.keys()])
            # [1, 'world', 'hello']

            print([val for val in rs.items()])
            # [(1, 2.0), ('world', 4.0), ('hello', 4.5)]

            rs.update({4: 5, 6: 7})
            print(rs.all[4])
            # 5.0

            print([x for x in rs.itemsbyscore(reverse=True)])
            # [(6, 7.0), (4, 5.0), ('hello', 4.5), ('world', 4.0), (1, 2.0)]

            print([x for x in rs.iterbyscore()])
            # [1, 'world', 'hello', 4, 6]

            rs.clear()
        ..
    """
    __slots__ = (
        "name", "prefix", "serializer", "cast", "_client", "_default",
        "serialized", "reversed")

    def __init__(self, name, data=None, prefix="rs:sorted_set",
                 cast=float, reversed=None, **kwargs):
        """ An interesting, sort of hybrid dict/list structure.  You can get
            members from the sorted set by their index (rank) and  you can
            retrieve their associated values by their member names.
            You can iter() the set normally or in reverse.
            It is not possible to serialize the values of this structure,
            but you may serialize the member names.

            :see::meth:BaseRedisStructure.__init__
            @data: :class:RedisSortedSet, :class:OrderedDict, #dict or #list
                of #tuple (key, value)
            @cast: a callable used to cast the score return value
            @reverse: #bool True to reverse sort by default
        """
        super().__init__(name=name, prefix=prefix, **kwargs)
        self.cast = cast
        self.reversed = reversed or False
        if isinstance(data, (dict, UserDict, OrderedDict)) or \
           hasattr(data, 'items'):
            self.add(**data)
        elif data:
            self.add(*data)

    @prepr(
        ('name', 'cyan'), 'key_prefix', 'serializer',
        ('size', 'purple'), 'cast', 'reversed')
    def __repr__(self): return

    def __str__(self):
        return self.__repr__()

    def __setitem__(self, member, score):
        """ Adds at @member to the set with a score of @score """
        return self.add(score, member)

    def __getitem__(self, member):
        """ if @member is a #slice, -> #list of members in the @member range
            else -> :prop:_cast of the @member zscore
        """
        if isinstance(member, slice):
            #: Get by index range
            start = member.start if member.start else 0
            stop = member.stop-1 if member.stop else -1
            return list(self.iter(start=start, stop=stop))
        else:
            #: Get by member name
            try:
                return self.cast(self._client.zscore(
                    self.key_prefix, self._dumps(member)))
            except TypeError:
                raise KeyError(
                    'Member `{}` not in `{}`'.format(member, self.key_prefix))

    def __delitem__(self, member):
        """ Removes @member from the set """
        return self._client.zrem(self.key_prefix, self._dumps(member))

    def __len__(self):
        """ :see::RedisSet.__len__ """
        return self.size

    def __contains__(self, member):
        """ :see::RedisSet.__contains__ """
        return True if self._client.zscore(
            self.key_prefix, self._dumps(member)) is not None else False

    def __reversed__(self):
        """ :see::RedisList.__reversed__ """
        return iter(self.iter(reverse=True))

    @property
    def size(self):
        """ :see::meth:RedisSet.size """
        return int(self._client.zcard(self.key_prefix) or 0)

    def incr(self, member, by=1):
        """ Increments @member by @by within the sorted set """
        return self._client.zincrby(self.key_prefix, self._dumps(member), by)

    def decr(self, member, by=1):
        """ Decrements @member by @by within the sorted set """
        return self._client.zincrby(
            self.key_prefix, self._dumps(member), by * -1)

    def add(self, *args, **kwargs):
        """ Adds member/value pairs to the sorted set in two ways:

            To add with @args:
            ..
                pairs = [4.0, 'member1', 5.0, 'member2']
                sorted_set.add(*pairs)
                # sorted_set.add(4.0, 'member1', 5.0, 'member2')
            ..

            To add with @kwargs:
            ..
                pairs = {"member1": 4.0, "member2": 5.0}
                sorted_set.add(**pairs)
                # sorted_set.add(member1=4.0, member2=5.0)
            ..
        """
        if args or kwargs:
            _dumps = self._dumps
            zargs = list(args)
            if args and self.serialized:
                # args format: value, key, value, key...
                zargs = [
                    _dumps(x) if (i % 2 == 1 and self.serialized) else x
                    for i, x in enumerate(args)]
            if kwargs:
                # kwargs format: key=value, key=value
                zargs += [
                    _dumps(x) if (i % 2 == 1 and self.serialized) else x
                    for y in kwargs.items() for i, x in enumerate(reversed(y))]
            return self._client.zadd(self.key_prefix, *zargs)

    def update(self, data):
        """ Adds @data to the sorted set
            @data: #dict or dict-like object
        """
        if data:
            _dumps = self._dumps
            zargs = [
                _dumps(x) if (i % 2 == 1) else x
                for y in data.items()
                for i, x in enumerate(reversed(y))
            ]
            return self._client.zadd(self.key_prefix, *zargs)

    def remove(self, *members):
        """ Removes @members from the sorted set """
        members = list(map(self._dumps, members))
        self._client.zrem(self.key_prefix, *members)

    def rank(self, member):
        """ Gets the ASC rank of @member from the sorted set, that is,
            lower scores have lower ranks
        """
        if self.reversed:
            return self._client.zrevrank(self.key_prefix, self._dumps(member))
        return self._client.zrank(self.key_prefix, self._dumps(member))

    def revrank(self, member):
        """ Gets the DESC rank of @member from the sorted set, that is,
            higher scores have lower ranks
        """
        if self.reversed:
            return self._client.zrank(self.key_prefix, self._dumps(member))
        return self._client.zrevrank(self.key_prefix, self._dumps(member))

    index = rank

    def count(self, min, max):
        """ -> #int number of elements in the sorted set with a score between
                @min and @max.
        """
        return self._client.zcount(self.key_prefix, min, max)

    def iter(self, start=0, stop=-1, withscores=False, reverse=None):
        """ Return a range of values from sorted set name between
            @start and @end sorted in ascending order unless @reverse or
            :prop:reversed.

            @start and @end: #int, can be negative, indicating the end of
                the range.
            @withscores: #bool indicates to return the scores along with the
                members, as a list of |(member, score)| pairs
            @reverse: #bool indicating whether to sort the results descendingly

            -> yields members or |(member, score)| #tuple pairs
        """
        reverse = reverse if reverse is not None else self.reversed
        _loads = self._loads
        for member in self._client.zrange(
           self.key_prefix, start=start, end=stop, withscores=withscores,
           desc=reverse, score_cast_func=self.cast):
            if withscores:
                yield (_loads(member[0]), self.cast(member[1]))
            else:
                yield _loads(member)

    def iterbyscore(self, min='-inf', max='+inf', start=None, num=None,
                    withscores=False, reverse=None):
        """ Return a range of values from the sorted set name with scores
            between @min and @max.

            If @start and @num are specified, then return a slice
            of the range.

            @min: #int minimum score, or #str '-inf'
            @max: #int minimum score, or #str '+inf'
            @start: #int starting range position
            @num: #int number of members to fetch
            @withscores: #bool indicates to return the scores along with the
                members, as a list of |(member, score)| pairs
            @reverse: #bool indicating whether to sort the results descendingly

            -> yields members or |(member, score)| #tuple pairs
        """
        reverse = reverse if reverse is not None else self.reversed
        zfunc = self._client.zrangebyscore if not reverse \
            else self._client.zrevrangebyscore
        _loads = self._loads
        for member in zfunc(
           self.key_prefix, min=min, max=max, start=start, num=num,
           withscores=withscores, score_cast_func=self.cast):
            if withscores:
                yield (_loads(member[0]), self.cast(member[1]))
            else:
                yield _loads(member)

    def itemsbyscore(self, min='-inf', max='+inf', start=None, num=None,
                     reverse=None):
        """ Return a range of |(member, score)| pairs from the sorted set name
            with scores between @min and @max.

            If @start and @num are specified, then return a slice
            of the range.

            @min: #int minimum score, or #str '-inf'
            @max: #int minimum score, or #str '+inf'
            @start: #int starting range position
            @num: #int number of members to fetch
            @reverse: #bool indicating whether to sort the results descendingly

            -> yields |(member, score)| #tuple pairs
        """
        reverse = reverse if reverse is not None else self.reversed
        for member in self.iterbyscore(
           min, max, start, num, withscores=True, reverse=reverse):
            yield member

    def iterscan(self, match="*", count=1000):
        """ Much slower than iter(), but much more memory efficient if
            k/v's retrieved are one-offs

            @match: matches member names in the sorted set
            @count: the user specified the amount of work that should be done
                at every call in order to retrieve elements from the collection

            -> iterator of |(member, score)| pairs
        """
        if self.serialized:
            return map(
                lambda x: (self._loads(x[0]), self.cast(x[1])),
                self._client.zscan_iter(
                    self.key_prefix, match=match, count=count))
        else:
            return map(
                lambda x: (self._decode(x[0]), self.cast(x[1])),
                self._client.zscan_iter(
                    self.key_prefix, match=match, count=count))

    keys = iter

    def values(self, reverse=None):
        """ @reverse: #bool True to return revranked scores
            -> yields :prop:cast scores in the sorted set
        """
        reverse = reverse if reverse is not None else self.reversed
        for member, score in self.items(reverse=reverse):
            yield self.cast(score)

    def items(self, reverse=None):
        """ @reverse: #bool True to return revranked scores
            -> yields |(member, score)| #tuple pairs in the sorted set
        """
        reverse = reverse if reverse is not None else self.reversed
        for member in self.iter(withscores=True, reverse=reverse):
            yield member

    @property
    def all(self):
        """ -> :class:OrderedDict of |{"member": score}| pairs, ordered by
                reverse if :prop:reversed
        """
        return OrderedDict([item for item in self.items()])

    def scan(self, match="*", count=1000, cursor=0):
        """ :see::meth:RedisMap.scan """
        if self.serialized:
            cursor, data = self._client.zscan(
                self.key_prefix, cursor=cursor, match=match, count=count)
            return (cursor, list(map(
                lambda x: (self._loads(x[0]), self.cast(x[1])), data)))
        else:
            cursor, data = self._client.zscan(
                self.key_prefix, cursor=cursor, match=match, count=count)
            return (cursor, list(map(
                lambda x: (self._decode(x[0]), self.cast(x[1])), data)))
