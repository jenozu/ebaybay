"""Authenticated Settings and eBay seller-connection routes."""
import secrets

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .auth import login_required
from .services.ebay.oauth import OAuthError, get_oauth_service
from .services.ebay.account import AccountServiceError, cached_options, refresh_cached_options, save_defaults

bp = Blueprint("oauth", __name__)
_STATE_KEY = "ebay_oauth_state"


@bp.get("/privacy")
def privacy():
    return "<h1>Privacy Policy</h1><p>This private application stores seller authorization credentials securely.</p>"


@bp.get("/settings/ebay")
@login_required
def settings():
    service = get_oauth_service()
    try:
        connection = service.import_legacy_token() or service.connection()
    except OAuthError:
        connection = service.connection()
        flash("A legacy eBay token could not be imported. Reconnect the seller account.", "error")
    return render_template("ebay_settings.html", connection=connection, options=cached_options(connection))


@bp.post("/settings/ebay/connect")
@login_required
def connect():
    state = secrets.token_urlsafe(32)
    session[_STATE_KEY] = state
    try:
        return redirect(get_oauth_service().authorization_url(state))
    except OAuthError as exc:
        session.pop(_STATE_KEY, None)
        flash(str(exc), "error")
        return redirect(url_for("oauth.settings"))


@bp.get("/oauth/callback")
@login_required
def oauth_callback():
    expected_state = session.pop(_STATE_KEY, None)  # one-time even on mismatch
    returned_state = request.args.get("state")
    if not expected_state or not returned_state or not secrets.compare_digest(expected_state, returned_state):
        return render_template("oauth_callback_error.html", message="The eBay connection request could not be verified. Start a new connection request."), 400
    if request.args.get("error"):
        return render_template("oauth_callback_error.html", message="eBay authorization was declined or cancelled. No connection was changed."), 400
    code = request.args.get("code")
    if not code:
        return render_template("oauth_callback_error.html", message="eBay did not return an authorization code. Start a new connection request."), 400
    try:
        get_oauth_service().complete_authorization(code)
    except OAuthError as exc:
        flash(str(exc), "error")
    else:
        flash("eBay seller account connected.", "success")
    return redirect(url_for("oauth.settings"))


@bp.get("/oauth/declined")
@login_required
def oauth_declined():
    session.pop(_STATE_KEY, None)
    flash("eBay authorization was declined.", "error")
    return redirect(url_for("oauth.settings"))


@bp.post("/settings/ebay/disconnect")
@login_required
def disconnect():
    get_oauth_service().disconnect()
    flash("eBay seller account disconnected locally.", "success")
    return redirect(url_for("oauth.settings"))


@bp.post("/settings/ebay/defaults/refresh")
@login_required
def refresh_defaults():
    try:
        refresh_cached_options(get_oauth_service().config)
    except (OAuthError, AccountServiceError) as exc:
        flash(str(exc), "error")
    else:
        flash("Available eBay policies and inventory locations refreshed.", "success")
    return redirect(url_for("oauth.settings"))


@bp.post("/settings/ebay/defaults")
@login_required
def update_defaults():
    try:
        save_defaults(get_oauth_service().config, request.form)
    except (OAuthError, AccountServiceError) as exc:
        flash(str(exc), "error")
    else:
        flash("Default seller policies and inventory location saved.", "success")
    return redirect(url_for("oauth.settings"))
