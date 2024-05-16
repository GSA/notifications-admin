document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('myChart').getContext('2d');
    const labels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

    const dataDelivered = labels.map(() => Math.floor(Math.random() * 81) + 20); // Random between 20 and 100
    const dataFailed = dataDelivered.map(delivered => Math.floor(delivered * (Math.random() * 0.15 + 0.05))); // 5-20% of delivered

    const myChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Delivered',
                data: dataDelivered,
                backgroundColor: '#0076d6',
                stack: 'Stack 0'
            }, {
                label: 'Failed',
                data: dataFailed,
                backgroundColor: '#fa9441',
                stack: 'Stack 0'
            }]
        },
        options: {
            scales: {
                x: {
                    stacked: true,
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    max: 120,
                      title: {
                        display: true,
                        text: 'SMS Sent', // Label for the Y-axis
                        color: '#666',   // Optional: you can change the label color
                        font: {
                            size: 16,     // Optional: change the font size
                            weight: 'bold', // Optional: change the font weight
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end',  // This aligns the legend items to the end of the area
                    labels: {
                        padding: 20,
                        boxWidth: 14,
                        font: {
                            size: 14
                        }
                    }
                }
            },
            responsive: true,
            maintainAspectRatio: true
        }
    });
});
