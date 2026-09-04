from functools import wraps
from hmac import compare_digest

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from .forms import LoginForm

bp = Blueprint("auth", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("listings.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        expected_username = current_app.config["APP_USERNAME"]
        password_hash = current_app.config["APP_PASSWORD_HASH"]
        username_ok = compare_digest(form.username.data, expected_username)
        password_ok = bool(password_hash) and check_password_hash(password_hash, form.password.data)
        if username_ok and password_ok:
            session.clear()
            session["authenticated"] = True
            session["username"] = expected_username
            flash("Signed in.", "success")
            target = request.args.get("next")
            return redirect(target if target and target.startswith("/") else url_for("listings.dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html", form=form)


@bp.post("/logout")
@login_required
def logout():
    session.clear()
    flash("Signed out.", "success")
    return redirect(url_for("auth.login"))
