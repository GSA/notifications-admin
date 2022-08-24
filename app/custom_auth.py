from flask import jsonify, request
from flask_basicauth import BasicAuth


class CustomBasicAuth(BasicAuth):
    """
        Description:
        Override BasicAuth to permit anonymous healthcheck at /_status?simple=true
    """

    def challenge(self):
        if "/_status" in request.url:
            if request.args.get('elb', None) or request.args.get('simple', None):
                return jsonify(status="ok"), 200
        return super(CustomBasicAuth, self).challenge()


custom_basic_auth = CustomBasicAuth()
