# import datetime
import logging
import os
import socket
import ssl

import requests
from requests.exceptions import RequestException

# from pprint import pprint


logger = logging.getLogger(__name__)


def inspect_certificate():
    try:
        cert_string = ""
        context = ssl.create_default_context()
        with socket.create_connection(
            ("notify-api-staging.apps.internal", "61443"), timeout=10
        ) as sock:
            with context.wrap_socket(
                sock, server_hostname="notify-api-staging.apps.internal"
            ) as ssock:
                cert = ssock.getpeercert(binary_form=False)

                cert_string.append("Certificate Details:\n")
                cert_string.append("-" * 50)
                cert_string.append("\nSubject:")
                for _, value in cert.get("subject", []):
                    for k, v in value:
                        cert_string.append(f" {k}: {v}")
                cert_string.append("\nIssuer")
                for _, value in cert.get("issuer", []):
                    for k, v in value:
                        cert_string.append(f" {k}: {v}")
                not_before = cert.get("notBefore")
                not_after = cert.get("notAfter")
                cert_string.append(f"\nValid From: {not_before}")
                cert_string.append(f"\nValid Until: {not_after}")
                cert_string.append(
                    f"\nSerial Number: {cert.get('serialNumber', 'N/A')}"
                )
                cert_string.append(f"Version: {cert.get('version', 'N/A')}")
                cert_string.append("\nExtensions:")
                for ext in cert.get("extensions", []):
                    ext_name = ext.get("oid", "Unknown")
                    critical = "Critical" if ext.get("critical") else "Non-critical"
                    value = ext.get("value", "N/A")
                    cert_string.append(f" {ext_name} ({critical}): {value}")
                key_usage = next(
                    (
                        ext
                        for ext in cert.get("extensions", [])
                        if ext.get("old") == "keyUsage"
                    ),
                    None,
                )
                if key_usage:
                    cert_string.append(f"\nKey Usage (Detailed): {key_usage['value']}")
                else:
                    cert_string.append("\nKey Usage: Not present")
        logger.warning(f"CERT STRING {cert_string}")

    except ssl.SSLCertVerificationError as e:
        logger.error(f"SSL Certification Verification Error: {e}")
        logger.error("This may be the cause of the 'key usage extension' error")
    except socket.gaierror:
        logger.error(
            "Error: could not resolve hostname 'notify-api-staging.apps.internal'"
        )
    except socket.timeout:
        logger.error("Connection timed out")
    except Exception as e:
        logger.error(f"Unexpected exception occurred {e}")


def is_api_down():
    inspect_certificate()
    api_base_url = os.getenv("API_HOST_NAME")
    try:
        response = requests.get(api_base_url, timeout=2)
        is_down = response.status_code != 200
        if is_down:
            logger.warning(
                f"API responded with status {response.status_code} at {api_base_url}"
            )
        return is_down
    except RequestException as e:
        logger.error(f"API down when loading homepage {e}")
        return True
