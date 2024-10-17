from flask import send_from_directory

from app.main import main


@main.route("/.well-known/security.txt", methods=["GET"])
@main.route("/security.txt", methods=["GET"])
def security_policy():
    return send_from_directory(".well-known", "security.txt")
