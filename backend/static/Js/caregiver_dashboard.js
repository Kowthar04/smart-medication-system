document.addEventListener("DOMContentLoaded", () => {

    // Log dose buttons
    document.querySelectorAll(".caregiver-log-btn").forEach(button => {
        button.addEventListener("click", async () => {
            const time = button.dataset.time;
            try {
                const response = await fetch("/log-dose", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        time: time,
                        source: "caregiver",
                    }),
                });
                if (!response.ok) {
                    throw new Error("Failed to log dose");
                }
                button.textContent = "Logged";
                button.disabled = true;
                setTimeout(() => { window.location.reload(); }, 800);
            } catch (error) {
                alert("Could not log dose.");
            }
        });
    });
    // Note button toggles inline form
    document.querySelectorAll(".caregiver-note-btn").forEach(button => {
        button.addEventListener("click", () => {
            const row = button.closest(".caregiver-item");
            const form = row.querySelector(".note-form");
            if (form) form.classList.toggle("active");
        });
    });
    // Tag chip selection (per form)
    document.querySelectorAll(".note-form").forEach(form => {
        const chips = form.querySelectorAll(".tag-chip");
        chips.forEach(chip => {
            chip.addEventListener("click", () => {
                if (chip.classList.contains("selected")) {
                    chip.classList.remove("selected");
                    return;
                }
                chips.forEach(c => c.classList.remove("selected"));
                chip.classList.add("selected");
            });
        });
    });
    // Save note (text + tag + dose time)
    document.querySelectorAll(".save-note-btn").forEach(button => {
        button.addEventListener("click", async () => {
            const form = button.closest(".note-form");
            if (!form) return;
            const textarea = form.querySelector("textarea");
            const noteText = textarea.value.trim();
            if (!noteText) {
                alert("Please write a note first.");
                return;
            }
            const selectedChip = form.querySelector(".tag-chip.selected");
            const selectedTag = selectedChip ? selectedChip.dataset.tag : null;
            const relatedTime = button.dataset.time || null;
            try {
                const response = await fetch("/save-note", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        note_text: noteText,
                        tag: selectedTag,
                        related_time: relatedTime,
                    }),
                });
                if (!response.ok) {
                    throw new Error("Failed to save note");
                }
                button.textContent = "Saved";
                button.disabled = true;
                textarea.disabled = true;
                setTimeout(() => { window.location.reload(); }, 700);
            } catch (error) {
                alert("Could not save note.");
            }
        });
    });
});