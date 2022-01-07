from multiprocessing.managers import State as ManagerState
from multiprocessing.managers import SyncManager
from typing import Optional


class SyncNamespace(object):
    __slots__ = ("_l", "_manager", "_lock", "_ns")

    def __init__(self, manager: Optional[SyncManager] = None, lock=True, start=True):
        self._l = lock
        if manager is None:
            manager = SyncManager()
        if manager._state.value == ManagerState.INITIAL and start:
            manager.start()
        self._manager = manager
        if self._l:
            self._lock = manager.Lock()
        else:
            self._lock = None
        self._ns = manager.Namespace()

    @property
    def manager(self):
        return object.__getattribute__(self, "_ns")

    def __getattr__(self, item):
        if item in self.__slots__:
            return object.__getattribute__(self, item)
        return self._ns.__getattr__(item)

    def __setattr__(self, item, val):
        if item in self.__slots__:
            return object.__setattr__(self, item, val)
        return self._ns.__setattr__(item, val)

    def __delattr__(self, item):
        if item in self.__slots__:
            return object.__delattr__(self, item)
        return self._ns.__delattr__(item)

    def acquire(self):
        if self._l:
            return self._lock.acquire()

    def release(self):
        if self._l:
            return self._lock.release()

    def get(self, item):
        return self._ns.__getattr__(item)

    def set(self, item, val):
        return self._ns.__setattr__(item, val)

    def delete(self, *items):
        if self._l:
            self._lock.acquire()
            try:
                for i in items:
                    self._ns.__delattr__(i)
            finally:
                self._lock.release()
        else:
            for i in items:
                self._ns.__delattr__(i)

    def replace(self, item, val=None):
        """Atomic get+set operation. Returns old value."""
        if self._l:
            self._lock.acquire()
            try:
                a = self._ns.__getattr__(item)
                self._ns.__setattr__(item, val)
            finally:
                self._lock.release()
        else:
            a = self._ns.__getattr__(item)
            self._ns.__setattr__(item, val)
        return a

    def increment(self, item, by=1):
        """Atomic += operation"""
        if self._l:
            self._lock.acquire()
            try:
                a = self._ns.__getattr__(item) + by
                self._ns.__setattr__(item, a)
            finally:
                self._lock.release()
        else:
            a = self._ns.__getattr__(item) + by
            self._ns.__setattr__(item, a)
        return a

    def decrement(self, item, by=1):
        """Atomic -= operation"""
        if self._l:
            self._lock.acquire()
            try:
                a = self._ns.__getattr__(item) - by
                self._ns.__setattr__(item, a)
            finally:
                self._lock.release()
        else:
            a = self._ns.__getattr__(item) - by
            self._ns.__setattr__(item, a)
        return a

    def set_default(self, kvs: dict):
        # Atomic, set values if they don't already exist
        if self._l:
            self._lock.acquire()
            try:
                for key, val in kvs.items():
                    a = getattr(self._ns, key, None)
                    if a is None:
                        print("Setting default {} = {}".format(key, val), flush=True)
                        self._ns.__setattr__(key, val)
            finally:
                self._lock.release()
        else:
            for key, val in kvs.items():
                a = getattr(self._ns, key, None)
                if a is None:
                    self._ns.__setattr__(key, val)
