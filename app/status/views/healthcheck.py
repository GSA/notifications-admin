import time
import traceback

from flask import current_app, jsonify, request
from notifications_python_client.errors import HTTPError
from redis import RedisError

from app import status_api_client, version
from app.extensions import redis_client
from app.status import status


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
        try:
            api_status = {"error": "unexpected error"}
            redis_uri = current_app.config['REDIS_URL']
            current_app.logger.info(f"config['REDIS_URL']: {redis_uri}")
            redis_enabled = current_app.config['REDIS_ENABLED']
            current_app.logger.info(f"config['REDIS_ENABLED']: {redis_enabled}")
            if redis_enabled:
                current_app.logger.info("config['REDIS_ENABLED'] evaluates as True")

            try:
                now = time.time()
                redis_client.set('mytestkey', now)
                val = redis_client.get('mytestkey')
                current_app.logger.info(f"Retrieved value from redis for mytestkey is: {val}")
            except RedisError as err:
                current_app.logger.exception(f"Redis service failed to respond with {err}")

            api_status = status_api_client.get_count_of_live_services_and_organisations_cached()
        except HTTPError as err:
            current_app.logger.exception("API failed to respond")
            return jsonify(status="error", message=str(err.message)), 500
        return jsonify(
            status="ok",
            api=api_status,
            git_commit=version.__git_commit__,
            build_time=version.__time__), 200
    except Exception as err:
        current_app.logger.exception(F"Unhandled exception: {err} - {traceback.format_exc()}")
        return jsonify(
            status=f"error: {err}",
            api=api_status,
            git_commit=version.__git_commit__,
            build_time=version.__time__), 500
