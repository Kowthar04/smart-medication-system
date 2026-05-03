document.querySelectorAll(".caregiver-log-btn").forEach(button => {
    button.addEventListener("click", async () => {
        const time = button.dataset.time;

        try {
            const response = await fetch("/log-dose", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ time })
            });

            if (!response.ok) {
                throw new Error("Failed to log dose");
            }

            button.textContent = "Logged";
            button.disabled = true;

            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } catch (error) {
            alert("Could not log dose.");
        }
    });
});