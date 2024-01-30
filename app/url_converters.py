from werkzeug.routing import BaseConverter

from app.models.service import Service


class TemplateTypeConverter(BaseConverter):
    regex = "(?:{})".format("|".join(Service.TEMPLATE_TYPES))


class SimpleDateTypeConverter(BaseConverter):
    regex = r"([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))"
