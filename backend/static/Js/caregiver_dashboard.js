document.addEventListener("DOMContentLoaded", () => {
    console.log("Caregiver JS loaded");

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

    document.querySelectorAll(".caregiver-note-btn").forEach(button => {
        button.addEventListener("click", () => {
            const row = button.closest(".caregiver-item");
            const form = row.querySelector(".note-form");

            if (form) {
                form.classList.toggle("active");
            }
        });
    });

    document.querySelectorAll(".save-note-btn").forEach(button => {
        button.addEventListener("click", () => {
            const form = button.closest(".note-form");
            const textarea = form.querySelector("textarea");

            if (!textarea.value.trim()) {
                alert("Please write a note first.");
                return;
            }

            button.textContent = "Saved";
            button.disabled = true;
            textarea.disabled = true;
        });
    });
});