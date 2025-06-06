import logging
import os
import ssl

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


def get_no_x509_strict_context():
    context = ssl.create_default_context()
    context.options |= ssl.OP_NO_X509_STRICT
    return context


def is_api_down():
    api_base_url = os.getenv("API_HOST_NAME")
    try:
        response = requests.get(
            api_base_url, timeout=2, cert=get_no_x509_strict_context()
        )
        is_down = response.status_code != 200
        if is_down:
            logger.warning(
                f"API responded with status {response.status_code} at {api_base_url}"
            )
        return is_down
    except RequestException as e:
        logger.error(f"API down when loading homepage {e}")
        return True
