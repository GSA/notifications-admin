(function (window) {
    // Initialize flask-socketio
    var socket = io();
    var serviceId = chart.getAttribute('data-service-id');

    socket.on('connect', function() {
        socket.emit('fetch_daily_stats', serviceId);
    });

    socket.on('daily_stats_update', function(data) {
        var labels = [];
        var deliveredData = [];

        for (var date in data) {
            labels.push(date);
            deliveredData.push(data[date].sms.delivered);
        }

        myBarChart.data.labels = labels;
        myBarChart.data.datasets[0].data = deliveredData;
        myBarChart.update();
    });

    socket.on('error', function(data) {
        console.log('Error:', data);
    });

    sevenDaysButton.addEventListener('click', function() {
        socket.emit('fetch_daily_stats', serviceId);
    });

    // Initialize Chart.js bar chart
    var ctx = document.getElementById('myChart').getContext('2d');
    var myBarChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Delivered',
                    data: [],
                    backgroundColor: '#0076d6',
                    stack: 'Stack 0'
                },
            ]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

})(window);
