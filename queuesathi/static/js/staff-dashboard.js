document.addEventListener("DOMContentLoaded", () => {
    let previousQueue = null;

    async function refreshQueue() {
        try {
            const response = await fetch(
                "/staff/api/queue",
                {
                    cache: "no-store",
                    credentials: "same-origin"
                }
            );

            if (!response.ok) {
                return;
            }

            const data = await response.json();

            const currentQueue = JSON.stringify(
                data.tokens
            );

            if (
                previousQueue !== null &&
                previousQueue !== currentQueue
            ) {
                window.location.reload();
            }

            previousQueue = currentQueue;

        } catch (error) {
            console.warn(
                "Queue refresh failed.",
                error
            );
        }
    }

    refreshQueue();

    setInterval(refreshQueue, 10000);
});