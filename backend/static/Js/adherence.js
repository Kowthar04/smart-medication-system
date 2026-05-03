let adherenceChart = null;
let currentPeriod = "daily";
let currentMedication = "all";

function getCssVariable(name) {
    return getComputedStyle(document.documentElement)
        .getPropertyValue(name)
        .trim();
}

function createChart(labels, values) {
    const canvas = document.getElementById("adherenceChart");

    if (!canvas) {
        return;
    }

    const chartContext = canvas.getContext("2d");

    const primary = getCssVariable("--primary") || "#3b5fe0";
    const textMuted = getCssVariable("--text-muted") || "#64748b";
    const borderSubtle = getCssVariable("--border-subtle") || "#f0f3f9";
    const text = getCssVariable("--text") || "#0f172a";

    const gradient = chartContext.createLinearGradient(0, 0, 0, 320);
    gradient.addColorStop(0, "rgba(59, 95, 224, 0.25)");
    gradient.addColorStop(1, "rgba(59, 95, 224, 0.02)");

    adherenceChart = new Chart(canvas, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Adherence (%)",
                data: values,
                borderColor: primary,
                backgroundColor: gradient,
                fill: true,
                tension: 0.4,
                pointRadius: 5,
                pointHoverRadius: 7,
                pointBackgroundColor: primary,
                pointBorderColor: "#ffffff",
                pointBorderWidth: 2,
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 800,
                easing: "easeOutQuart"
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: text,
                    titleColor: "#ffffff",
                    bodyColor: "#ffffff",
                    padding: 12,
                    cornerRadius: 10,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return `${context.raw}% adherence`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    border: {
                        display: false
                    },
                    ticks: {
                        color: textMuted,
                        font: {
                            size: 12,
                            weight: "600"
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: borderSubtle
                    },
                    border: {
                        display: false
                    },
                    ticks: {
                        callback: function(value) {
                            return `${value}%`;
                        },
                        color: textMuted,
                        font: {
                            size: 12
                        }
                    }
                }
            }
        }
    });
}

function updateChart(labels, values) {
    if (!adherenceChart) {
        createChart(labels, values);
        return;
    }

    adherenceChart.data.labels = labels;
    adherenceChart.data.datasets[0].data = values;
    adherenceChart.update();
}

function fetchAdherenceData() {
    const params = new URLSearchParams({
        period: currentPeriod,
        medication: currentMedication
    });

    fetch(`/adherence-data?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            const labels = data.labels || [];
            const values = data.data || [];

            updateChart(labels, values);
        })
        .catch(error => {
            console.error("Error loading adherence data:", error);
        });
}

function setupTimeTabs() {
    const tabs = document.querySelectorAll(".time-tab");

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(button => button.classList.remove("active"));
            tab.classList.add("active");

            currentPeriod = tab.dataset.period;
            fetchAdherenceData();
        });
    });
}

function setupMedicationFilter() {
    const medicationFilter = document.getElementById("medicationFilter");

    if (!medicationFilter) {
        return;
    }

    medicationFilter.addEventListener("change", () => {
        currentMedication = medicationFilter.value;
        fetchAdherenceData();
    });
}

document.addEventListener("DOMContentLoaded", () => {
    setupTimeTabs();
    setupMedicationFilter();
    fetchAdherenceData();
});

document.querySelectorAll(".breakdown-fill").forEach(el => {
    el.style.width = el.dataset.width + "%";
});