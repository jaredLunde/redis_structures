# Redis Structures [![Build Status](https://travis-ci.org/jaredlunde/redis_structures.svg?branch=master)](https://travis-ci.org/jaredlunde/redis_structures)
##### Full documentation at http://docr.it/redis_structures
Redis data structures wrapped with Python.


#### Benefits
* `Auto-serialization` (using the serializer of your choice)
* `Auto response decoding` (using the encoding of your choice)
* `Namespace maintanability` via prefix and name class properties
* `Pythonic interface` provides nearly all of the same methods available to
  builtin Python structures, so there is a minimal learning curve
* `Persistent` dictionaries, lists and sets which perhaps won't fit in the
  local memory, or that you merely wish to save

#### Table of contents
* [RedisMap](#redismap) behaves similarly to `dict()` and is a wrapper for
  simple GET/SET Redis operations
* [RedisDict](#redisdict) behaves similarly to `dict()` and is a wrapper for
  simple GET/SET Redis operations
* [RedisDefaultDict](#redisdefaultdict) behaves similarly to
  `defaultdict()` and is a wrapper for simple GET/SET
  Redis operations
* [RedisHash](#redishash) behaves similarly to `dict()` and is a wrapper for
  Redis HASH operations
* [RedisDefaultHash](#redisdefaulthash) behaves similarly to
  `defaultdict()` and is a wrapper for Redis HASH operations
* [RedisSet](#redisset) behaves similarly to `set()` and is a wrapper for Redis
  SET operations
* [RedisList](#redislist) behaves nearly identitical to `list()` and is a
  wrapper for Redis LIST operations
* [RedisSortedSet](#redissortedset) behaves like a `list()` and `dict()` hybrid
  and is a wrapper for Redis Sorted Set operations

#### Installation
```shell
pip install redis_structures
```
or
```shell
git clone https://github.com/jaredlunde/redis_structures.git
pip install -e ./redis_structures
```
#### Package Requirements
* `redis-py` https://github.com/andymccurdy/redis-py

#### System Requirements
* `Python 3.3+`

#### Unit tests available
https://github.com/jaredlunde/redis_structures/tree/master/tests

#### RedisMap
> Memory-persistent key/value-backed mapping
> For performance reasons it is recommended that if you
> need `iter()` methods like `keys()` you should use RedisHash
> and not RedisMap. The only advantage to RedisMap is a
> simple `{key: value}` get, set interface. The size of the
> map is unmonitored.
>
> Behaves like a Python `dict()` without the
> `__len__` method.

```python
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
```


#### RedisDict
> Memory-persistent key/value-backed dictionaries
> For performance reasons it is recommended that if you
> need `iter()` methods like `keys()` you should use RedisHash
> and not RedisDict. The only advantage to RedisDict is a
> simple `{key: value}` get, set interface with the ability to
> call a `len()` on a given group of key/value pairs.
>
> Behaves like a Python `dict()`

```python
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
```

#### RedisDefaultDict
> The same as RedisDict(), but has the default property of `defaultdict()`
>
> Behaves like a Python `defaultdict()`

```python
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
```


#### RedisHash
> Memory-persistent hashes, differs from dict because it uses the
> Redis Hash methods as opposed to simple set/get. In cases when the
> size is fewer than ziplist max entries(512 by defualt) and the value
> sizes are less than the defined ziplist max size(64 bytes), there are
> significant memory advantages to using RedisHash rather than
> RedisDict.
>
> Every RedisHash method is faster than RedisDict with the exception of
> `get()` and `len()`. All `iter()` methods are MUCH faster than
> RedisDict and `iter()` functions are safe here.
> It almost always makes sense to use this over RedisDict. """
>
> Behaves like a Python `dict()`

```python
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
```


#### RedisDefaultHash
> The same as RedisHash(), but has the default property of `defaultdict()`
>
> Behaves like a Python `defaultdict()`

```python
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
```


#### RedisList
> Memory-persistent lists
> Because this is not a linked list, it isn't recommend that you
> utilize certain methods available on long lists.  For instance,
> checking whether or not a value is contained within the list does
> not perform well as there is no native function within Redis to do
> so.
>
> Behaves like a Python `list()`

```python
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
```


#### RedisSet
> Memory-persistent Sets
> This structure behaves nearly the same way that a Python set()
> does.
>
> Behaves like a Python `set()`

```python
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
```


#### RedisSortedSet
> An interesting, sort of hybrid dict/list structure.  You can get
> members from the sorted set by their index (rank) and  you can
> retrieve their associated values by their member names.
> You can `iter()` the set normally or in reverse.
> It is not possible to serialize the values of this structure,
> but you may serialize the member names.

```python
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
```
