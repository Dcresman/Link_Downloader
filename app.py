import os
import shutil

from flask import Flask, render_template, request, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

from main import download_video


app = Flask(__name__)


# --------------------------------------------------
# BASIC SECURITY SETTINGS
# --------------------------------------------------

# The form only sends a URL and a few small settings.
# Reject abnormally large requests.
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024


# Render places the Flask app behind a proxy.
if os.environ.get("RENDER") == "true":

    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
    )


# --------------------------------------------------
# RATE LIMITING
# --------------------------------------------------

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[
        "60 per hour"
    ],
    storage_uri=os.environ.get(
        "RATELIMIT_STORAGE_URI",
        "memory://"
    ),
)


# --------------------------------------------------
# SECURITY HEADERS
# --------------------------------------------------

@app.after_request
def add_security_headers(response):

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "X-Frame-Options"
    ] = "DENY"

    response.headers[
        "Referrer-Policy"
    ] = "no-referrer"

    response.headers[
        "Permissions-Policy"
    ] = (
        "camera=(), "
        "microphone=(), "
        "geolocation=()"
    )

    response.headers[
        "Content-Security-Policy"
    ] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self';"
    )

    if request.is_secure:

        response.headers[
            "Strict-Transport-Security"
        ] = (
            "max-age=31536000; "
            "includeSubDomains"
        )

    return response


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# --------------------------------------------------
# DOWNLOAD
# --------------------------------------------------

@app.route(
    "/download",
    methods=["POST"]
)
@limiter.limit("5 per hour")
def download():

    url = request.form.get(
        "url",
        ""
    ).strip()

    quality = request.form.get(
        "quality",
        "best"
    )

    download_type = request.form.get(
        "download_type",
        "video"
    )


    # ------------------------------
    # CHECK INPUTS
    # ------------------------------

    if not url:

        return (
            "No URL was provided.",
            400
        )


    allowed_qualities = {
        "best",
        "1080",
        "720",
        "480",
    }


    if quality not in allowed_qualities:

        return (
            "Invalid quality.",
            400
        )


    if download_type not in {
        "video",
        "audio",
    }:

        return (
            "Invalid download type.",
            400
        )


    # ------------------------------
    # DOWNLOAD MEDIA
    # ------------------------------

    try:

        file_path = download_video(
            url,
            quality,
            download_type,
        )


    except ValueError as error:

        return (
            str(error),
            400
        )


    except RuntimeError:

        app.logger.exception(
            "Download failed."
        )

        return (
            "Download failed.",
            500
        )


    # ------------------------------
    # SEND FILE
    # ------------------------------

    response = send_file(
        str(file_path),
        as_attachment=True,
        download_name=file_path.name,
        conditional=False,
    )


    # Do not let browsers/proxies cache
    # somebody else's downloaded media.
    response.headers[
        "Cache-Control"
    ] = "no-store, private"


    # ------------------------------
    # DELETE SERVER COPY AFTERWARD
    # ------------------------------

    job_folder = file_path.parent


    def cleanup_download():

        shutil.rmtree(
            job_folder,
            ignore_errors=True
        )


    response.call_on_close(
        cleanup_download
    )


    return response


# --------------------------------------------------
# LOCAL DEVELOPMENT ONLY
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True
    )