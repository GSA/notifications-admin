from flask import current_app, jsonify, request
from notifications_python_client.errors import HTTPError

from app import status_api_client, version
from app.status import status

from redis import Redis, RedisError


@status.route('/_status', methods=['GET'])
def show_status():
    if request.args.get('elb', None) or request.args.get('simple', None):
        return jsonify(status="ok"), 200
    else:
        try:
            api_status = status_api_client.get_status()
        except HTTPError as err:
            current_app.logger.exception("API failed to respond")
            return jsonify(status="error", message=str(err.message)), 500
        return jsonify(
            status="ok",
            api=api_status,
            git_commit=version.__git_commit__,
            build_time=version.__time__), 200


@status.route('/_status/redis', methods=['GET'])
def show_redis_status():
    try:
        redis_uri = current_app.config['REDIS_URL']
        current_app.logger.info(f"config['REDIS_URL']: {redis_uri}")

        try:
            r = Redis(redis_uri, socket_connect_timeout=1)
            r.ping()
        except RedisError as err:
            current_app.logger.exception("Redis service failed to respond")
            return jsonify(status="error", message=str(err)), 500

        api_status = status_api_client.get_count_of_live_services_and_organisations_cached()
    except HTTPError as err:
        current_app.logger.exception("API failed to respond")
        return jsonify(status="error", message=str(err.message)), 500
    return jsonify(
        status="ok",
        api=api_status,
        git_commit=version.__git_commit__,
        build_time=version.__time__), 200
