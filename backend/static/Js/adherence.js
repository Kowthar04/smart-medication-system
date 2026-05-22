let adherenceChart = null;
let currentPeriod = "daily";
let currentMedication = "all";

function getCssVariable(name) {
    return getComputedStyle(document.documentElement)
        .getPropertyValue(name)
        .trim();
}

function pointColor(value) {
    if (value >= 80) return getCssVariable("--success") || "#22c55e";
    if (value >= 60) return getCssVariable("--warning") || "#eab308";
    return getCssVariable("--danger") || "#ef4444";
}

const targetLinePlugin = {
    id: "targetLinePlugin",
    afterDatasetsDraw(chart) {
        const { ctx, chartArea, scales } = chart;
        const yScale = scales.y;

        if (!yScale) return;

        const y = yScale.getPixelForValue(80);

        ctx.save();
        ctx.beginPath();
        ctx.setLineDash([8, 6]);
        ctx.moveTo(chartArea.left, y);
        ctx.lineTo(chartArea.right, y);
        ctx.lineWidth = 2;
        ctx.strokeStyle = "rgba(34, 197, 94, 0.75)";
        ctx.stroke();

        ctx.setLineDash([]);
        ctx.fillStyle = "rgba(34, 197, 94, 0.12)";
        ctx.strokeStyle = "rgba(34, 197, 94, 0.25)";

        const label = "Target 80%";
        ctx.font = "700 12px Manrope, Arial, sans-serif";

        const textWidth = ctx.measureText(label).width;
        const boxWidth = textWidth + 18;
        const boxHeight = 24;
        const boxX = chartArea.right - boxWidth;
        const boxY = y - 34;

        ctx.beginPath();
        ctx.roundRect(boxX, boxY, boxWidth, boxHeight, 12);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = "#047857";
        ctx.fillText(label, boxX + 9, boxY + 16);

        ctx.restore();
    }
};

Chart.register(targetLinePlugin);

function createChart(labels, values) {
    const canvas = document.getElementById("adherenceChart");

    if (!canvas) return;

    const chartContext = canvas.getContext("2d");

    const primary = getCssVariable("--primary") || "#3b5fe0";
    const textMuted = getCssVariable("--text-muted") || "#64748b";
    const borderSubtle = getCssVariable("--border-subtle") || "#f0f3f9";
    const text = getCssVariable("--text") || "#0f172a";

    const gradient = chartContext.createLinearGradient(0, 0, 0, 320);
    gradient.addColorStop(0, "rgba(59, 95, 224, 0.22)");
    gradient.addColorStop(1, "rgba(59, 95, 224, 0.02)");

    adherenceChart = new Chart(canvas, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "% of doses on time",
                data: values,
                borderColor: primary,
                backgroundColor: gradient,
                fill: true,
                tension: 0.35,
                pointRadius: 7,
                pointHoverRadius: 9,
                pointBackgroundColor: values.map(pointColor),
                pointBorderColor: "#ffffff",
                pointBorderWidth: 3,
                borderWidth: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 700,
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
                    padding: 13,
                    cornerRadius: 12,
                    displayColors: false,
                    callbacks: {
                        title: function(context) {
                            return context[0].label;
                        },
                        label: function(context) {
                            const value = context.raw;

                            if (value >= 80) {
                                return `${value}% of doses were on time — good`;
                            }

                            if (value >= 60) {
                                return `${value}% of doses were on time — needs watching`;
                            }

                            return `${value}% of doses were on time — needs attention`;
                        },
                        afterLabel: function(context) {
                            const value = context.raw;

                            if (value >= 80) {
                                return "Above the 80% target.";
                            }

                            return "Below the 80% target.";
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
                            weight: "700"
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: "% of doses on time",
                        color: textMuted,
                        font: {
                            size: 12,
                            weight: "700"
                        }
                    },
                    grid: {
                        color: borderSubtle
                    },
                    border: {
                        display: false
                    },
                    ticks: {
                        stepSize: 20,
                        callback: function(value) {
                            return `${value}%`;
                        },
                        color: textMuted,
                        font: {
                            size: 12,
                            weight: "600"
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
    adherenceChart.data.datasets[0].pointBackgroundColor = values.map(pointColor);
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

    if (!medicationFilter) return;

    medicationFilter.addEventListener("change", () => {
        currentMedication = medicationFilter.value;
        fetchAdherenceData();
    });
}

function setupBreakdownBars() {
    document.querySelectorAll(".breakdown-fill").forEach(el => {
        const width = el.dataset.width || "0";
        el.style.width = `${width}%`;
    });
}

document.addEventListener("DOMContentLoaded", () => {
    setupTimeTabs();
    setupMedicationFilter();
    setupBreakdownBars();
    fetchAdherenceData();
});