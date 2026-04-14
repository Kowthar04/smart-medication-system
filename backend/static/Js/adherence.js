const ctx = document.getElementById('adherenceChart');

if (ctx) {

    const chartContext = ctx.getContext('2d');

    const gradient = chartContext.createLinearGradient(0, 0, 400, 0);
    gradient.addColorStop(0, '#4f7cff');
    gradient.addColorStop(1, '#355ad8');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [
                'Blood Pressure Medication',
                'Vitamin D',
                'Iron Tablet',
                'Metformin'
            ],
            datasets: [{
                label: 'Adherence (%)',
                data: [100, 80, 90, 60],
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
                            return context.raw + '%';
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
                            return value + '%';
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
