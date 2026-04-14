const ctx = document.getElementById('adherenceChart');

if (ctx) {
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
                backgroundColor: '#355ad8',
                borderRadius: 12,
                barThickness: 18
            }]
        },
        options: {
            indexAxis: 'y', // 🔥 MAKES IT HORIZONTAL
            responsive: true,
            maintainAspectRatio: false,

            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1f2937',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 10,
                    cornerRadius: 8
                }
            },

            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: '#e5e7eb'
                    },
                    ticks: {
                        callback: value => value + '%'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}