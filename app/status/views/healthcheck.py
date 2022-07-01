from flask import current_app, jsonify, request
from notifications_python_client.errors import HTTPError

from app import status_api_client, version, basic_auth
from app.status import status

from functools import wraps


def health_check():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            return jsonify(status="ok"), 200
            # if '/_status' in request.url:
            #     return jsonify(status="ok"), 200
            # else:
            #     return fn(*args, **kwargs)
        return decorator
    return wrapper

@status.route('/_status', methods=['GET'])
def show_status():
    if request.args.get('elb', None) or request.args.get('simple', None):
        return jsonify(status="ok"), 200
    else:
        try:
            api_status = status_api_client.get_status()
        except HTTPError as e:
            current_app.logger.exception("API failed to respond")
            return jsonify(status="error", message=str(e.message)), 500
        return jsonify(
            status="ok",
            api=api_status,
            git_commit=version.__git_commit__,
            build_time=version.__time__), 200
