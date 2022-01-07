
# Sanic-Synchro-Ctx
Plugin to provide an App context that is shared across multiple workers

Can use native python SyncManager backend, or Redis if you want. (Redis is much faster).

## Installation
```bash
$ pip3 install sanic-synchro-ctx
```

Or in a python virtualenv _(these example commandline instructions are for a Linux/Unix based OS)_
```bash
$ python3 -m virtualenv --python=python3 --no-site-packages .venv
$ source ./.venv/bin/activate
$ pip3 install sanic sanic-synchro-ctx
```

To exit the virtual enviornment:
```bash
$ deactivate
```

## Redis Extension
You can install the relevant Redis libraries for this plugin, with the installable redis extension:
```bash
$ pip3 install sanic-synchro-ctx[redis]
```
That is the same as running:
```bash
$ pip3 install "sanic-synchro-ctx" "aioredis>=2.0" "hiredis>=1.0"
```

## Compatibility
* Works with Python 3.8 and greater.
* Works with Sanic v21.9.0 and greater.
* If you are installing the redis library separately, use aioredis >= 2.0


## Usage
A very simple example, it uses the native python SyncManager backend, doesn't require a Redis connection.
```python3
from sanic_synchro_ctx import SanicSynchroCtx
app = Sanic("sample")
s = SanicSynchroCtx(app)

@app.after_server_start
def handler(app, loop=None):
    # This will only set this value if it doesn't already exist
    # So only the first worker will set this value
    app.ctx.synchro.set_default({"counter": 0})

@app.route("/inc")
def increment(request: Request):
    # atomic increment operation
    counter = request.app.ctx.synchro.increment("counter")
    print("counter: {}".format(counter), flush=True)
    return html("<p>Incremented!</p>")

@app.route("/count")
def increment(request: Request):
    # Get from shared context:
    counter = request.app.ctx.synchro.counter
    print("counter: {}".format(counter), flush=True)
    return html(f"<p>count: {counter}</p>")

app.run("127.0.0.1", port=8000, workers=8)
```

Redis example:
```python3
from sanic_synchro_ctx import SanicSynchroCtx
redis = aioredis.from_url("redis://localhost")
app = Sanic("sample")
s = SanicSynchroCtx(app, backend="redis", redis_client=redis)

@app.after_server_start
async def handler(app, loop=None):
    # This will only set this value if it doesn't already exist
    # So only the first worker will set this value
    await app.ctx.synchro.set_default({"counter": 0})

@app.route("/inc")
async def increment(request: Request):
    # atomic increment operation
    counter = await request.app.ctx.synchro.increment("counter")
    print(f"counter: {counter}", flush=True)
    return html("<p>Incremented!</p>")

@app.route("/count")
async def increment(request: Request):
    # Get from shared context:
    counter = await request.app.ctx.synchro.counter
    print(f"counter: {counter}", flush=True)
    return html(f"<p>count: {counter}</p>")

app.run("127.0.0.1", port=8000, workers=8)
```


## Changelog
A comprehensive changelog is kept in the [CHANGELOG file](https://github.com/ashleysommer/sanic-synchro-ctx/blob/master/CHANGELOG.md).


## Benchmarks
I've done some basic benchmarks. SyncManager works surprisingly well, but Redis backend is much faster. 


## License
This repository is licensed under the MIT License. See the [LICENSE deed](https://github.com/ashleysommer/sanic-synchro-ctx/blob/master/LICENSE.txt) for details.

