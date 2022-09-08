import importlib
import json
import os
from unittest import mock

import pytest

from app import config


def cf_conf():
    os.environ['API_HOST_NAME'] = 'cf'


@pytest.fixture
def reload_config(os_environ):
    """
    Reset config, by simply re-running config.py from a fresh environment
    """
    old_env = os.environ.copy()
    os.environ.clear()

    yield

    os.environ.clear()
    for k, v in old_env.items():
        os.environ[k] = v
    importlib.reload(config)


def test_load_cloudfoundry_config_if_available(reload_config):
    os.environ['API_HOST_NAME'] = 'env'
    os.environ['REDIS_URL'] = 'some uri'
    os.environ['VCAP_APPLICATION'] = 'some json blob'
    os.environ['VCAP_SERVICES'] = json.dumps({
        'aws-elasticache-redis': [{
            'credentials': {
                'uri': 'redis://xxx:6379'
            }
        }],
    })

    with mock.patch('app.cloudfoundry_config.extract_cloudfoundry_config', side_effect=cf_conf):
        # reload config so that its module level code (ie: all of it) is re-instantiated
        importlib.reload(config)

    assert os.environ['REDIS_URL'] == 'rediss://xxx:6379'
    assert config.Config.REDIS_URL == 'rediss://xxx:6379'


def test_load_config_if_cloudfoundry_not_available(reload_config):
    os.environ['API_HOST_NAME'] = 'env'

    os.environ.pop('VCAP_APPLICATION', None)

    with mock.patch('app.cloudfoundry_config.extract_cloudfoundry_config') as cf_config:
        # reload config so that its module level code (ie: all of it) is re-instantiated
        importlib.reload(config)

    assert not cf_config.called

    assert os.environ['API_HOST_NAME'] == 'env'
    assert config.Config.API_HOST_NAME == 'env'
