document.addEventListener("DOMContentLoaded", () => {
    let doctorAdherenceChart = null;

function buildDoctorChart(payload) {
    const canvas = document.getElementById("doctorAdherenceSideEffectsChart");
    if (!canvas) return;

    const labels = payload.labels || [];
    const adherence = payload.adherence || [];
    const events = payload.events || [];

    const mildDots = events
        .filter(e => e.severity === "mild")
        .map(e => ({
            x: e.date,
            y: e.adherence,
            symptom: e.symptom,
            medication: e.medication,
            severity: e.severity,
        }));

    const moderateDots = events
        .filter(e => e.severity === "moderate")
        .map(e => ({
            x: e.date,
            y: e.adherence,
            symptom: e.symptom,
            medication: e.medication,
            severity: e.severity,
        }));

    const ctx = canvas.getContext("2d");

    if (doctorAdherenceChart) {
        doctorAdherenceChart.destroy();
    }

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
                        title(items) {
                            return items?.[0]?.label || "";
                        },
                        label(context) {
                            const dsLabel = context.dataset.label || "";
                            if (context.dataset.type === "scatter") {
                                const raw = context.raw || {};
                                return `${dsLabel}: ${raw.symptom || "Side effect"} (${raw.medication || "Unknown medication"})`;
                            }
                            return `${dsLabel}: ${context.raw}%`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 10 },
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback(value) {
                            return `${value}%`;
                        },
                    },
                },
            },
        },
    });
}

async function loadDoctorAdherenceChart() {
    try {
        const response = await fetch("/doctor/adherence-sideeffects-data");
        if (!response.ok) throw new Error("Failed to load chart data");
        const payload = await response.json();
        buildDoctorChart(payload);
    } catch (err) {
        // Keep failure quiet in UI for now; E4 remains non-blocking.
        console.error("Doctor chart load error:", err);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadDoctorAdherenceChart();
});
});