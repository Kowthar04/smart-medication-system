const steps = document.querySelectorAll(".checkin-step");

const toStep2 = document.getElementById("to-step-2");
const backToStep1 = document.getElementById("back-to-step-1");
const toStep3 = document.getElementById("to-step-3");
const backToStep2 = document.getElementById("back-to-step-2");
const saveCheckin = document.getElementById("save-checkin");
const editCheckin = document.getElementById("edit-checkin");

const summaryMood = document.getElementById("summary-mood");
const summaryEnergy = document.getElementById("summary-energy");
const summarySideEffects = document.getElementById("summary-side-effects");
const currentTimeEl = document.getElementById("current-time");

const checkinData = {
    mood: null,
    energy: null,
    side_effects: null
};

function showStep(stepClass) {
    steps.forEach(step => step.classList.remove("active-step"));
    const nextStep = document.querySelector(stepClass);

    if (nextStep) {
        nextStep.classList.add("active-step");
    }
}

function updateCurrentTime() {
    const now = new Date();

    if (currentTimeEl) {
        currentTimeEl.textContent = now.toLocaleString([], {
            weekday: "short",
            day: "numeric",
            month: "short",
            hour: "2-digit",
            minute: "2-digit"
        });
    }
}

function setupOptionGroups() {
    const optionGroups = document.querySelectorAll(".checkin-options");

    optionGroups.forEach(group => {
        const buttons = group.querySelectorAll(".checkin-option");

        buttons.forEach(button => {
            button.addEventListener("click", () => {
                buttons.forEach(btn => btn.classList.remove("selected"));
                button.classList.add("selected");

                const step = group.closest(".checkin-step");

                if (step.classList.contains("step-1")) {
                    checkinData.mood = button.innerText;
                } else if (step.classList.contains("step-2")) {
                    checkinData.energy = button.innerText;
                } else if (step.classList.contains("step-3")) {
                    checkinData.side_effects = button.innerText;
                }
            });
        });
    });
}

async function saveWellbeingCheckin() {
    if (!checkinData.mood || !checkinData.energy || !checkinData.side_effects) {
        alert("Please complete all steps before saving.");
        return;
    }

    try {
        const response = await fetch("/wellbeing", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(checkinData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Failed to save wellbeing check-in");
        }

        summaryMood.textContent = checkinData.mood;
        summaryEnergy.textContent = checkinData.energy;
        summarySideEffects.textContent = checkinData.side_effects;

        showStep(".step-complete");
    } catch (error) {
        console.error("Error saving check-in:", error);
        alert("There was a problem saving the check-in.");
    }
}

if (toStep2) {
    toStep2.addEventListener("click", () => showStep(".step-2"));
}

if (backToStep1) {
    backToStep1.addEventListener("click", () => showStep(".step-1"));
}

if (toStep3) {
    toStep3.addEventListener("click", () => showStep(".step-3"));
}

if (backToStep2) {
    backToStep2.addEventListener("click", () => showStep(".step-2"));
}

if (saveCheckin) {
    saveCheckin.addEventListener("click", saveWellbeingCheckin);
}

if (editCheckin) {
    editCheckin.addEventListener("click", () => showStep(".step-1"));
}

setupOptionGroups();
updateCurrentTime();
setInterval(updateCurrentTime, 60000);