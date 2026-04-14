let adherenceChart = null;
let currentPeriod = "daily";
let currentMedication = "all";

function createChart(labels, values) {
    const canvas = document.getElementById("adherenceChart");

    if (!canvas) {
        return;
    }

  
    const chartContext = canvas.getContext('2d');

    const gradient = chartContext.createLinearGradient(0, 0, 400, 0);
    gradient.addColorStop(0, '#4f7cff');
    gradient.addColorStop(1, '#355ad8');

    adherenceChart = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Adherence (%)',
                data: values,
                backgroundColor: gradient,
                borderRadius: 12,
                barThickness: 26,
                borderSkipped: false

                 }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 800,
                easing: 'easeOutQuart'
            },

            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1f2937',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 10,
                    cornerRadius: 8,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return `${context.raw}%`;
                        }
                    }
                }
    },

            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: '#e5e7eb'
                    },
                    border: {
                        display: false
                    },
                    ticks: {
                        callback: function(value) {
                            return `${value}%`;
                        },
                        color: '#6b7280',
                        font: {
                            size: 12
                        }
                    }
                },
                y: {
                    grid: {
                        display: false
                    },
                    border: {
                        display: false
                    },
                    ticks: {
                        color: '#1f2937',
                        font: {
                            size: 13,
                            weight: '600'
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

    