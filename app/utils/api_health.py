import os

import requests
from requests.exceptions import RequestException


def is_api_down():
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:6011")
    try:
        response = requests.get(api_base_url, timeout=2)
        return response.status_code != 200
    except RequestException:
        return True
