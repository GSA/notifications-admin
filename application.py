from flask import Flask
from werkzeug.serving import WSGIRequestHandler

from app import create_app

WSGIRequestHandler.version_string = lambda self: "SecureServer"

application = Flask("app")

create_app(application)
