document.addEventListener('DOMContentLoaded', function () {
    var canvas = document.getElementById('myChart');
    var ctx = canvas.getContext('2d');
    // Set explicit dimensions for the canvas
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = 100;

    var chartContainer = document.getElementById('chartContainer');
    var sms_sent = parseInt(chartContainer.getAttribute('data-sms-sent'));
    var sms_remaining_messages = parseInt(chartContainer.getAttribute('data-sms-allowance-remaining'));
    var totalMessages = sms_sent + sms_remaining_messages;

    var myChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [''],
            datasets: [{
                label: 'Messages Sent',
                data: [sms_sent],
                backgroundColor: '#0076d6',
            },
            {
                label: 'Remaining',
                data: [sms_remaining_messages],
                backgroundColor: '#fa9441',
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
                            return tooltipItem.dataset.label + ': ' + tooltipItem.raw.toLocaleString();
                        }
                    }
                },
                title: {
                    display: false // Hide the Chart.js title and use custom title
                }
            },
            responsive: true,
            layout: {
                padding: {
                    left: -10, // Adjust left padding to remove extra space
                    top: 0,
                    bottom: 0
                }
            }
        }
    });

    // Update the message below the chart
    document.getElementById('message').innerText = `${sms_sent.toLocaleString()} sent / ${sms_remaining_messages.toLocaleString()} remaining`;

});
