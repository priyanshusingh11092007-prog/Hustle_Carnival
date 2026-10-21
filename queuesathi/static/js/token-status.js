document.addEventListener("DOMContentLoaded", () => {

    const container = document.getElementById("token-status");

    if (!container) {
        return;
    }

    const publicId = container.dataset.publicId;

    const statusElement = document.getElementById("status");

    const aheadElement = document.getElementById("people-ahead");

    const waitElement = document.getElementById("estimated-wait");

    const sourceElement = document.getElementById("estimate-source");

    const updatedElement = document.getElementById("last-updated");

    const errorElement = document.getElementById("refresh-error");


    async function refreshStatus() {

        try {

            const response = await fetch(
                `/api/token/${encodeURIComponent(publicId)}`,
                {
                    method: "GET",
                    credentials: "same-origin",
                    cache: "no-store",
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );

            if (!response.ok) {

                throw new Error(
                    "Unable to retrieve token status."
                );

            }

            const data = await response.json();

            const previousStatus = statusElement.textContent.trim();

            statusElement.textContent = data.status;

            aheadElement.textContent = data.people_ahead;

            if (data.estimated_minutes === null) {

                waitElement.textContent = "Unavailable";

            } else {

                waitElement.textContent =
                    `${data.estimated_minutes} min`;

            }

            sourceElement.textContent = data.estimate_source;

            updatedElement.textContent =
                new Date(data.updated_at).toLocaleTimeString();

            errorElement.textContent = "";

            if (previousStatus !== data.status) {

                window.location.reload();

            }

        } catch (error) {

            console.error(
                "Token tracking error:",
                error
            );

            errorElement.textContent =
                "Unable to refresh queue status. Please check your connection.";

        }

    }


    refreshStatus();

    setInterval(refreshStatus, 10000);

});