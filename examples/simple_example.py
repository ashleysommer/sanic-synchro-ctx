from sanic import Sanic
from sanic.response import html
from sanic.request import Request

from sanic_synchro_ctx import SanicSynchroCtx

app = Sanic("simple")
s = SanicSynchroCtx(app)

@app.after_server_start
def handler(app, loop=None):
    # This will only set this value if it doesn't already exist
    # So only the first worker will set this value
    app.ctx.synchro.set_default({"counter": 0})

@app.route("/")
def index(request: Request):
    counter = request.app.ctx.synchro.increment("counter")

    print("counter: {}".format(counter), flush=True)
    return html("<p>Hello World</p>")

app.run("127.0.0.1", port=8000, workers=8, debug=False, auto_reload=False, access_log=False)
