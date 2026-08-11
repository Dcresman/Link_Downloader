const form =
    document.querySelector("form");

const button =
    document.querySelector("button");

const glassCard =
    document.querySelector(".glass-card");

const helmetLoader =
    document.querySelector("#helmet-loader");

const helmetStatus =
    document.querySelector("#helmet-status");


function getFilename(response) {

    const contentDisposition =
        response.headers.get(
            "Content-Disposition"
        );


    if (!contentDisposition) {
        return "download";
    }


    /*
        Handles:

        filename*=UTF-8''video%20name.mp4
    */

    const utf8Match =
        contentDisposition.match(
            /filename\*=UTF-8''([^;]+)/i
        );


    if (utf8Match) {

        try {

            return decodeURIComponent(
                utf8Match[1]
                    .replace(/"/g, "")
                    .trim()
            );

        } catch (error) {

            console.warn(
                "Could not decode filename."
            );

        }

    }


    /*
        Handles:

        filename="video name.mp4"
    */

    const normalMatch =
        contentDisposition.match(
            /filename="?([^";]+)"?/i
        );


    if (normalMatch) {

        return normalMatch[1].trim();

    }


    return "download";
}


function startLoading() {

    button.textContent =
        "Downloading...";

    button.disabled =
        true;


    glassCard.classList.add(
        "downloading"
    );


    helmetLoader.style.display =
        "flex";


    helmetStatus.textContent =
        "Finding media...";

}


function stopLoading() {

    button.textContent =
        "Download";

    button.disabled =
        false;


    glassCard.classList.remove(
        "downloading"
    );


    helmetLoader.style.display =
        "none";


    helmetStatus.textContent =
        "Finding media...";

}


form.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();


        startLoading();


        const formData =
            new FormData(form);


        /*
            We cannot receive real yt-dlp progress
            through this simple Flask request yet,
            so these status changes are visual.
        */

        const processingTimer =
            setTimeout(
                function () {

                    helmetStatus.textContent =
                        "Downloading and processing...";

                },
                1200
            );


        try {

            const response =
                await fetch(
                    "/download",
                    {
                        method: "POST",
                        body: formData
                    }
                );


            clearTimeout(
                processingTimer
            );


            if (!response.ok) {

                throw new Error(
                    "Download failed."
                );

            }


            helmetStatus.textContent =
                "Preparing file...";


            const blob =
                await response.blob();


            const filename =
                getFilename(response);


            const downloadUrl =
                window.URL.createObjectURL(
                    blob
                );


            const downloadLink =
                document.createElement(
                    "a"
                );


            downloadLink.href =
                downloadUrl;


            downloadLink.download =
                filename;


            downloadLink.style.display =
                "none";


            document.body.appendChild(
                downloadLink
            );


            downloadLink.click();


            downloadLink.remove();


            setTimeout(
                function () {

                    window.URL.revokeObjectURL(
                        downloadUrl
                    );

                },
                1000
            );


            helmetStatus.textContent =
                "Download ready!";


            setTimeout(
                function () {

                    stopLoading();

                },
                1200
            );


        } catch (error) {

            clearTimeout(
                processingTimer
            );


            console.error(
                error
            );


            helmetStatus.textContent =
                "Download failed. Please try again.";


            button.textContent =
                "Download";


            button.disabled =
                false;


            glassCard.classList.remove(
                "downloading"
            );


            setTimeout(
                function () {

                    helmetLoader.style.display =
                        "none";

                },
                2000
            );

        }

    }
);