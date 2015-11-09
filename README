===============================
Redis Structures
===============================

Redis data structures wrapped with Python 3.

`Full documentation can be found at http://docr.it/redis_structures
<http://docr.it/redis_structures>`_

.. image:: https://travis-ci.org/jaredlunde/redis_structures.svg?branch=master
   :target: https://travis-ci.org/jaredlunde/redis_structures

Installation
------------

redis_structures requires a running Redis server. See `Redis's quickstart
<http://redis.io/topics/quickstart>`_ for installation instructions.

To install redis_structures:

.. code-block:: bash

    $ sudo pip install redis_structures

or from source:

.. code-block:: bash

    $ git clone https://github.com/jaredlunde/redis_structures
    $ cd redis_structures
    $ sudo python setup.py install


Getting Started
---------------

.. code-block:: pycon

    >>> from redis_structures import StrictRedis, RedisHash
    >>> client = StrictRedis(host='localhost', port=6379, db=0)
    >>> rh = RedisHash("my_hash", prefix="rs:hash" client=StrictRedis)
    >>> rh['hello'] = "world"  # sets the field name 'hello' to value 'world' in
    >>>                        # redis under the key rs:hash:my_hash
    >>> rh['hello']
    'world'
    >>> del rh['hello']
    >>> rh.get('hello')
    None
