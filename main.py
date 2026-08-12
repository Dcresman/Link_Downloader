from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import shutil

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

DOWNLOAD_ROOT = (
    Path(__file__).resolve().parent
    / "downloads"
)


MAX_FILE_SIZE = (
    300
    * 1024
    * 1024
)


# For the public MVP, restrict the server
# to the service we have actually tested.
ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}


# --------------------------------------------------
# URL VALIDATION
# --------------------------------------------------

def validate_url(url: str):

    parsed = urlparse(url)


    if parsed.scheme != "https":

        raise ValueError(
            "Only HTTPS links are allowed."
        )


    hostname = (
        parsed.hostname
        or ""
    ).lower().rstrip(".")


    if hostname not in ALLOWED_HOSTS:

        raise ValueError(
            "For now, only YouTube links are allowed."
        )


# --------------------------------------------------
# CHOOSE QUALITY
# --------------------------------------------------

def choose_format(
    quality,
    download_type,
):

    if download_type == "audio":

        return (
            "bestaudio[ext=m4a]"
            "/bestaudio"
            "/best"
        )


    if quality == "1080":

        return (
            "bestvideo[height<=1080]"
            "+bestaudio"
            "/best[height<=1080]"
        )


    if quality == "720":

        return (
            "bestvideo[height<=720]"
            "+bestaudio"
            "/best[height<=720]"
        )


    if quality == "480":

        return (
            "bestvideo[height<=480]"
            "+bestaudio"
            "/best[height<=480]"
        )


    return (
        "bestvideo"
        "+bestaudio"
        "/best"
    )


# --------------------------------------------------
# DOWNLOAD FUNCTION
# --------------------------------------------------

def download_video(
    url: str,
    quality="best",
    download_type="video",
):

    validate_url(url)


    DOWNLOAD_ROOT.mkdir(
        exist_ok=True
    )


    # Every download gets its own
    # temporary folder.
    job_folder = (
        DOWNLOAD_ROOT
        / uuid4().hex
    )


    job_folder.mkdir(
        parents=True,
        exist_ok=False
    )


    video_format = choose_format(
        quality,
        download_type,
    )


    options = {

        "outtmpl": str(
            job_folder
            / "%(title)s [%(id)s].%(ext)s"
        ),

        "format": video_format,

        "noplaylist": True,

        "overwrites": True,

        "socket_timeout": 60,

        "extractor_args": {
            "youtube": {
                "player_client": [
                    "mweb"
                ]
            }
        },

        "retries": 3,

        "fragment_retries": 3,

        "concurrent_fragment_downloads": 1,

        "max_filesize": MAX_FILE_SIZE,
    }


    # --------------------------------------------------
    # VIDEO-SPECIFIC OPTIONS
    # --------------------------------------------------

    if download_type == "video":

        options[
            "merge_output_format"
        ] = "mp4"

        options[
            "format_sort"
        ] = [
            "+codec:avc:m4a"
        ]


    # --------------------------------------------------
    # FIND DENO AUTOMATICALLY
    # --------------------------------------------------

    deno_path = shutil.which(
        "deno"
    )


    if deno_path:

        options[
            "js_runtimes"
        ] = {

            "deno": {

                "path":
                    deno_path

            }

        }


    # --------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------

    try:

        with YoutubeDL(
            options
        ) as downloader:

            downloader.extract_info(
                url,
                download=True,
            )


        # --------------------------------------------------
        # FIND THE FINAL OUTPUT FILE
        # --------------------------------------------------

        files = [

            file

            for file
            in job_folder.iterdir()

            if (
                file.is_file()
                and
                not file.name.endswith(
                    (
                        ".part",
                        ".ytdl",
                    )
                )
            )

        ]


        if not files:

            raise RuntimeError(
                "No output file was created."
            )


        file_path = max(
            files,
            key=lambda file:
                file.stat().st_mtime
        )


        # Final safety check.
        if (
            file_path.stat().st_size
            > MAX_FILE_SIZE
        ):

            raise RuntimeError(
                "Downloaded file is too large."
            )


        return file_path


    except DownloadError as error:

        shutil.rmtree(
            job_folder,
            ignore_errors=True
        )

        raise RuntimeError(
            "The media could not be downloaded."
        ) from error


    except Exception:

        shutil.rmtree(
            job_folder,
            ignore_errors=True
        )

        raise