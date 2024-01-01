from flask import render_template

from app.main import main
from app.utils.user import user_is_logged_in


@main.route("/support", methods=["GET"])
@user_is_logged_in
def support():
    return render_template("views/support/index.html")
