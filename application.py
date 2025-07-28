from gevent import monkey

monkey.patch_all()

from flask import Flask  # noqa
from werkzeug.serving import WSGIRequestHandler  # noqa

from app import create_app  # noqa

WSGIRequestHandler.version_string = lambda self: "SecureServer"

application = Flask("app")

create_app(application)
