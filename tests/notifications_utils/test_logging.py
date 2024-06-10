import json
import logging as builtin_logging

from notifications_utils import logging


def test_get_handlers_sets_up_logging_appropriately_with_debug():
    class App:
        config = {"NOTIFY_APP_NAME": "bar", "NOTIFY_LOG_LEVEL": "ERROR"}
        debug = True

    app = App()

    handlers = logging.get_handlers(app)

    assert len(handlers) == 1
    assert isinstance(handlers[0], builtin_logging.StreamHandler)
    assert isinstance(handlers[0].formatter, builtin_logging.Formatter)


def test_get_handlers_sets_up_logging_appropriately_without_debug():
    class App:
        config = {"NOTIFY_APP_NAME": "bar", "NOTIFY_LOG_LEVEL": "ERROR"}
        debug = False

    app = App()

    handlers = logging.get_handlers(app)

    assert len(handlers) == 1
    assert isinstance(handlers[0], builtin_logging.StreamHandler)
    assert isinstance(handlers[0].formatter, logging.JSONFormatter)


def test_base_json_formatter_contains_service_id():
    record = builtin_logging.LogRecord(
        name="log thing",
        level="info",
        pathname="path",
        lineno=123,
        msg="message to log",
        exc_info=None,
        args=None,
    )

    service_id_filter = logging.ServiceIdFilter()
    assert (
        json.loads(logging.BaseJSONFormatter().format(record))["message"]
        == "message to log"
    )
    assert service_id_filter.filter(record).service_id == "no-service-id"


def test_scrub():
    result = logging.scrub(
        "This is a message with 17775554324, and also 18884449323 and also 17775554324"
    )
    assert (
        result
        == "This is a message with 1XXXXX54324, and also 1XXXXX49323 and also 1XXXXX54324"
    )
