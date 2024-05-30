document.addEventListener('DOMContentLoaded', function () {
    var canvas = document.getElementById('totalMessageChart');
    var ctx = canvas.getContext('2d');
    // Set explicit dimensions for the canvas
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = 100;

    var chartContainer = document.getElementById('chartContainer');
    var sms_sent = parseInt(chartContainer.getAttribute('data-sms-sent'));
    var sms_remaining_messages = parseInt(chartContainer.getAttribute('data-sms-allowance-remaining'));
    var totalMessages = sms_sent + sms_remaining_messages;

    // Set a minimum value for "Messages Sent" based on a percentage of the remaining messages
    var minSentPercentage = 0.01; // Minimum width as a percentage of total messages (1% in this case)
    var minSentValue = totalMessages * minSentPercentage;
    var displaySent = Math.max(sms_sent, minSentValue);
    var displayRemaining = totalMessages - displaySent;

    var myChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [''],
            datasets: [{
                label: 'Messages Sent',
                data: [displaySent],
                backgroundColor: '#0076d6',
                actualValue: sms_sent // Store the actual value for tooltips
            },
            {
                label: 'Remaining',
                data: [displayRemaining],
                backgroundColor: '#fa9441',
                actualValue: sms_remaining_messages // Store the actual value for tooltips
            }]
        },
        options: {
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true,
                    stacked: true,
                    max: totalMessages,
                    grid: {
                        display: false,
                    },
                    border: {
                        display: false,
                    },
                    ticks: {
                        display: false // Hide x-axis ticks
                    }
                },
                y: {
                    stacked: true,
                    grid: {
                        display: false,
                    },
                    border: {
                        display: false,
                    },
                    ticks: {
                        display: false // Hide y-axis ticks
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(tooltipItem) {
                            var dataset = tooltipItem.dataset;
                            return dataset.label + ': ' + dataset.actualValue.toLocaleString();
                        }
                    }
                },
                title: {
                    display: false // Hide the Chart.js title and use custom title
                }
            },
            responsive: true,
            // maintainAspectRatio: false,
            layout: {
                padding: {
                    left: 0, // Adjust left padding to remove extra space
                    top: 0,
                    bottom: 0,
                    right: 0
                }
            }
        }
    });

    // Update the message below the chart
    document.getElementById('message').innerText = `${sms_sent.toLocaleString()} sent / ${sms_remaining_messages.toLocaleString()} remaining`;

    // Ensure the chart resizes correctly on window resize
    window.addEventListener('resize', function() {
        canvas.width = canvas.parentElement.clientWidth;
        myChart.resize();
    });
});
