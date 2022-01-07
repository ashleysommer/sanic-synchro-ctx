import logging

from functools import partial, wraps
from types import SimpleNamespace


try:
    from distutils.version import LooseVersion
except ImportError:
    from setuptools._distutils.version import LooseVersion

from typing import Optional

from sanic import Sanic
from sanic.__version__ import __version__ as sanic_version
from sanic.log import logger


try:
    import sanic_ext  # noqa: F401

    from sanic_ext.config import Config
    from sanic_ext.extensions.base import Extension

    use_ext = True
except ImportError:
    use_ext = False
    Extension = object
    from sanic.config import Config

SANIC_VERSION = LooseVersion(sanic_version)
SANIC_21_9_0 = LooseVersion("21.9.0")


class SanicSynchroCtx(Extension):
    name: str = "SanicSynchroCtx"

    def __init__(self, app: Sanic, config: Optional[Config] = None, *args, **kwargs):
        if SANIC_21_9_0 > SANIC_VERSION:
            raise RuntimeError("You cannot use this version of Sanic-Synchro-Ctx with " "Sanic earlier than v21.9.0")
        self._options = kwargs
        if use_ext:
            super(SanicSynchroCtx, self).__init__(app, config)
        else:
            super(SanicSynchroCtx, self).__init__(*args)
            self.app = app
            self.config = config or {}
            bootstrap = SimpleNamespace()
            bootstrap.app = self.app
            bootstrap.config = self.config
            self.startup(bootstrap)

    @classmethod
    def log(cls, level, message, *args, exc_info=None, **kwargs):
        msg = f"Sanic-Synchro-Ctx: {message}"
        logger.log(level, msg, *args, exc_info=exc_info, **kwargs)

    def label(self):
        # TODO, make this expose some configured options
        return "Sanic-Synchro-Ctx"

    def startup(self, bootstrap):
        """
        Used by sanic-ext to start up an extension
        """
        if bootstrap.app != self.app:
            raise RuntimeError("Woops, looks like this extension was registered on the wrong app!")
        _options = self._options
        synchro_options = _options or bootstrap.config.get("SYNCHRO_OPTIONS", {})
        no_startup = synchro_options.pop("no_startup", None)
        if no_startup:
            return
        self.app.ctx._sanic_synchro_ctx = context = SimpleNamespace()
        context._options = synchro_options
        context.log = self.log
        self.init_app_context(context)
        self.install_signals(self.app, context)

    @classmethod
    def server_init_after_handler(cls, app: Sanic, loop=None, _plugin_ctx=None, **kwargs):
        if _plugin_ctx is None:
            return
        app.ctx.synchro = _plugin_ctx.ns

    def install_signals(self, app: Sanic, context):
        hdl = wraps(self.server_init_after_handler)(partial(self.server_init_after_handler, _plugin_ctx=context))
        app.signal("server.init.after")(hdl)

    def init_app_context(self, context: SimpleNamespace):
        log = context.log
        _options = context._options
        backend = _options.get("backend", "native")
        if backend in ("native", "syncns", "syncmanager"):
            from sanic_synchro_ctx.syncns import SyncNamespace

            manager = _options.get("syncmanager", None)
            lock = _options.get("synclock", True)
            ns = SyncNamespace(manager=manager, lock=lock)
        elif backend in ("redis",):
            from sanic_synchro_ctx.redisns import RedisNamespace

            redis_url = _options.get("redis_url", "redis://localhost")
            redis_client = _options.get("redis_client", None)
            redis_kwargs = _options.get("redis_kwargs", {})
            ns = RedisNamespace(redis_url, redis_client, **redis_kwargs)
        else:
            raise RuntimeError("Sync Ctx Backend not supported: {}".format(backend))
        log(logging.DEBUG, f"Sanic-Synchro-Ctx installed with backend: {backend}")
        context.ns = ns


if __name__ == "__main__":
    from sanic.request import Request
    from sanic.response import html

    app = Sanic("main")
    s = SanicSynchroCtx(app, backend="redis")

    @app.after_server_start
    async def handler(app, loop=None):
        await app.ctx.synchro.set_default({"counter": 0})

    @app.route("/")
    async def index(request: Request):
        counter = await request.app.ctx.synchro.increment("counter")

        print("counter: {}".format(counter), flush=True)
        return html("<p>Hello World</p>")

    app.run("127.0.0.1", port=8000, workers=8, debug=True, auto_reload=False, access_log=False)
