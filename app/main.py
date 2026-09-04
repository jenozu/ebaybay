from flask import Blueprint, jsonify, redirect, session, url_for

bp = Blueprint("main", __name__)


@bp.get("/")
def home():
    if session.get("authenticated"):
        return redirect(url_for("listings.dashboard"))
    return redirect(url_for("auth.login"))


@bp.get("/health")
def health():
    return jsonify(status="ok")
