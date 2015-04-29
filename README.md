# redis_structures
Pythonic data structures backed by Redis. Full documentation is coming soon.

* [RedisMap](#redismap) -> `dict`
* [RedisDict](#redisdict) -> `dict`
* [RedisHash](#redishash) -> `dict`
* [RedisList](#redislist) -> `list`
* [RedisSet](#redisset) -> `set`
* [RedisSortedSet](#redissortedset) -> `dict` and `list` hybrid

#### RedisMap
> Memory-persistent key/value-backed mapping
> For performance reasons it is recommended that if you
> need iter() methods like keys() you should use RedisHash
> and not RedisMap. The only advantage to RedisMap is a
> simple {key: value} get, set interface. The size of the
> map is unmonitored. 
>
> Behaves like a Python `dict()` without the
> `__len__` property.

```python
from redis import StrictRedis
from redis_structures import RedisMap

redis_connection = StrictRedis(**strict_redis_config)
redis_map = RedisMap("MyMapName", {'hello': 'world2'}, connection=redis_connection)

print(redis_map)
# {'hello': 'world2'}

redis_map["hello"] = "world"
print(redis_map["hello"]) 
# world

print(redis_map.get('world', 'hello')) 
# hello

redis_map.clear()
print(redis_map['hello']) 
# None
```

#### RedisDict
> Memory-persistent key/value-backed dictionaries
> For performance reasons it is recommended that if you
> need iter() methods like keys() you should use RedisHash
> and not RedisDict. The only advantage to RedisDict is a
> simple {key: value} get, set interface with the ability to
> call a len() on a given group of key/value pairs.
>
> Behaves like a Python `dict()`

```python
from redis import StrictRedis
from redis_structures import RedisDict

redis_connection = StrictRedis(**strict_redis_config)
redis_dict = RedisDict("MyDictName", connection=redis_connection)

redis_dict["test"] = "best"
redis_dict.update({'hello': 'world', 'jello': 'curls'})

for k in redis_dict.keys():
    print(k)
# test
# hello
# jello

for k, v in redis_dict.items():
    print(k ,v)
# hello world
# test best
# jello curls

del redis_dict['test']

for v in redis_dict.values():
    print(v)
# curls
# world

print("needle" in redis_dict)
# False
```

#### RedisHash
> Memory-persistent hashes, differs from dict because it uses the
> Redis Hash methods as opposed to simple set/get. In cases when the
> size is fewer than ziplist max entries(512 by defualt) and the value
> sizes are less than the defined ziplist max size(64 bytes), there are
> significant memory advantages to using RedisHash rather than
> RedisDict.
> Every RedisHash method is faster than RedisDict with the exception of
> get() and len(). All iter() methods are MUCH faster than
> RedisDict and iter() functions are safe here.
> It almost always makes sense to use this over RedisDict. """
>
> Behaves like a Python `dict()`

#### RedisList
> Memory-persistent lists
> Because this is not a linked list, it isn't recommend that you
> utilize certain methods available on long lists.  For instance,
> checking whether or not a value is contained within the list does
> not perform well as there is no native function within Redis to do
> so.
>
> Behaves like a Python `list()`

#### RedisSet
> Memory-persistent Sets
> This structure behaves nearly the same way that a Python set()
> does.
>
> Behaves like a Python `set()`

#### RedisSortedSet
> An interesting, sort of hybrid dict/list structure.  You can get
> members from the sorted set by their index (rank) and  you can
> retrieve their associated values by their member names.
> You can iter() the set normally or in reverse.
> It is not possible to serialize the values of this structure,
> but you may serialize the member names.
