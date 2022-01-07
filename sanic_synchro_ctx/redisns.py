from typing import Optional

import aioredis

from aioredis.client import Redis
from aioredis.lock import Lock


class RedisNamespace(object):
    __slots__ = ("_client", "_lock", "_l")

    def __init__(self, redis_url=Optional[str], client: Optional[Redis] = None, lock=True, **kwargs):
        if redis_url is None and client is None:
            raise RuntimeError(
                "When initializing a redis namespace, please pass in either a redis_url or existing client object."
            )
        if client is None:
            self._client = aioredis.from_url(redis_url, **kwargs)  # type: Redis
        else:
            self._client = client
        self._l = lock
        if lock:
            _id = "%x" % id(self)
            try:
                self._lock = Lock(self._client, "_sanic_sync_lock_{}".format(_id))
            except Exception as e:
                print(e)
        else:
            self._lock = None

    def __getattr__(self, item):
        if item in self.__slots__:
            return object.__getattribute__(self, item)
        return self._client.get(item)

    def __setattr__(self, item, val):
        if item in self.__slots__:
            return object.__setattr__(self, item, val)
        return self._ns.__setattr__(item, val)

    def __delattr__(self, item):
        if item in self.__slots__:
            return object.__delattr__(self, item)
        return self._ns.__delattr__(item)

    async def acquire(self):
        if self._l:
            return await self._lock.acquire()

    async def release(self):
        if self._l:
            return await self._lock.release()

    async def get(self, item):
        return await self._client.get(item)

    async def set(self, item, val):
        return await self._client.set(item, val)

    async def delete(self, *items):
        return await self._client.delete(*items)

    async def replace(self, item, val=None):
        """Atomic get+set operation. Returns old value."""
        return await self._client.getset(item, val)

    async def increment(self, item, by=1):
        """Atomic += operation"""
        return await self._client.incrby(item, amount=by)

    async def decrement(self, item, by=1):
        """Atomic -= operation"""
        return await self._client.decrby(item, amount=by)

    async def set_default(self, kvs: dict):
        # Atomic, set values if they don't already exist
        if self._l:
            await self._lock.acquire()
            try:
                for key, val in kvs.items():
                    await self._client.setnx(key, val)
            finally:
                await self._lock.release()
        else:
            for key, val in kvs.items():
                await self._client.setnx(key, val)
