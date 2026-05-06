let doctorAdherenceChart = null;

function buildDoctorChart(payload) {
    const canvas = document.getElementById("doctorAdherenceSideEffectsChart");
    if (!canvas) return;

    const labels = payload.labels || [];
    const adherence = payload.adherence || [];
    const events = payload.events || [];

    const mildDots = events
        .filter(e => e.severity === "mild")
        .map(e => ({ x: e.date, y: e.adherence, symptom: e.symptom, medication: e.medication }));

    const moderateDots = events
        .filter(e => e.severity === "moderate")
        .map(e => ({ x: e.date, y: e.adherence, symptom: e.symptom, medication: e.medication }));

    const ctx = canvas.getContext("2d");
    if (doctorAdherenceChart) doctorAdherenceChart.destroy();

    doctorAdherenceChart = new Chart(ctx, {
        data: {
            labels,
            datasets: [
                {
                    type: "line",
                    label: "Adherence (%)",
                    data: adherence,
                    borderColor: "#3b5fe0",
                    backgroundColor: "rgba(59, 95, 224, 0.15)",
                    fill: true,
                    tension: 0.35,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    borderWidth: 2.5,
                    yAxisID: "y",
                },
                {
                    type: "scatter",
                    label: "Mild side effect",
                    data: mildDots,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointBackgroundColor: "#facc15",
                    pointBorderColor: "#b45309",
                    pointBorderWidth: 1,
                    yAxisID: "y",
                },
                {
                    type: "scatter",
                    label: "Moderate side effect",
                    data: moderateDots,
                    pointRadius: 5.5,
                    pointHoverRadius: 7.5,
                    pointBackgroundColor: "#ef4444",
                    pointBorderColor: "#991b1b",
                    pointBorderWidth: 1,
                    yAxisID: "y",
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title(items) { return items?.[0]?.label || ""; },
                        label(context) {
                            if (context.dataset.type === "scatter") {
                                const raw = context.raw || {};
                                return `${context.dataset.label}: ${raw.symptom || "Side effect"} (${raw.medication || "Unknown medication"})`;
                            }
                            return `${context.dataset.label}: ${context.raw}%`;
                        },
                    },
                },
            },
            scales: {
                x: { grid: { display: false }, ticks: { maxTicksLimit: 10 } },
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { callback(value) { return `${value}%`; } },
                },
            },
        },
    });
}

async function loadDoctorAdherenceChart() {
    const response = await fetch("/doctor/adherence-sideeffects-data");
    if (!response.ok) throw new Error("Failed to load chart data");
    const payload = await response.json();
    buildDoctorChart(payload);
}

async function addMedication(payload) {
    const res = await fetch("/doctor/medications", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Add medication failed");
}

async function editMedication(scheduleId, payload) {
    const res = await fetch(`/doctor/medications/${scheduleId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Edit medication failed");
}

async function deleteMedication(scheduleId) {
    const res = await fetch(`/doctor/medications/${scheduleId}/delete`, {
        method: "POST",
    });
    if (!res.ok) throw new Error("Delete medication failed");
}

function setupMedicationCrud() {
    const addForm = document.getElementById("doctorAddMedicationForm");
    if (addForm) {
        addForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const name = document.getElementById("newMedName").value.trim();
            const dose = document.getElementById("newMedDose").value.trim();
            const time = document.getElementById("newMedTime").value;

            if (!name || !dose || !time) {
                alert("Please complete medication name, dose, and time.");
                return;
            }

            try {
                await addMedication({ name, dose, time });
                window.location.reload();
            } catch (err) {
                alert("Could not add medication.");
            }
        });
    }

    document.querySelectorAll(".doctor-edit-med-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const row = btn.closest(".doctor-med-row");
            const scheduleId = row?.dataset.scheduleId;
            if (!scheduleId) return;

            const currentName = row.dataset.name || "";
            const currentDose = row.dataset.dose || "";
            const currentTime = row.dataset.time || "";

            const name = prompt("Medication name:", currentName);
            if (name === null) return;
            const dose = prompt("Dose:", currentDose);
            if (dose === null) return;
            const time = prompt("Time (HH:MM):", currentTime);
            if (time === null) return;

            try {
                await editMedication(scheduleId, {
                    name: name.trim(),
                    dose: dose.trim(),
                    time: time.trim(),
                });
                window.location.reload();
            } catch (err) {
                alert("Could not update medication.");
            }
        });
    });

    document.querySelectorAll(".doctor-delete-med-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const row = btn.closest(".doctor-med-row");
            const scheduleId = row?.dataset.scheduleId;
            if (!scheduleId) return;

            if (!confirm("Delete this medication schedule entry?")) return;

            try {
                await deleteMedication(scheduleId);
                window.location.reload();
            } catch (err) {
                alert("Could not delete medication.");
            }
        });
    });
}

function renderSparklines() {
    document.querySelectorAll(".doctor-sparkline").forEach((canvas) => {
        const raw = canvas.dataset.points || "";
        const points = raw.split(",").map(v => Number(v.trim())).filter(v => !Number.isNaN(v));
        if (!points.length) return;

        const ctx = canvas.getContext("2d");
        new Chart(ctx, {
            type: "line",
            data: {
                labels: points.map((_, i) => i + 1),
                datasets: [{
                    data: points,
                    borderColor: "#3b5fe0",
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.35,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { enabled: false } },
                scales: { x: { display: false }, y: { display: false, min: 0, max: 100 } },
            },
        });
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    try {
        await loadDoctorAdherenceChart();
    } catch (err) {
        console.error("Doctor chart load error:", err);
    }

    setupMedicationCrud();
    renderSparklines();
});