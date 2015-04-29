# redis_structures
Pythonic data structures backed by Redis.

## Full documentation coming soon.

##### RedisMap
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

##### RedisDict
> Memory-persistent key/value-backed dictionaries
> For performance reasons it is recommended that if you
> need iter() methods like keys() you should use RedisHash
> and not RedisDict. The only advantage to RedisDict is a
> simple {key: value} get, set interface with the ability to
> call a len() on a given group of key/value pairs.
>
> Behaves like a Python `dict()`

```python
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
