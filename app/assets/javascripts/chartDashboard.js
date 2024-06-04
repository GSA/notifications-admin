(function (window) {

    var socket = io();
    var serviceId = chart.getAttribute('data-service-id');

    socket.on('connect', function() {
        console.log('Connected to the server');  // Debug log, i'll delete later
        socket.emit('fetch_daily_stats', serviceId);
    });

    //this is for previous 7 days
    socket.on('daily_stats_update', function(data) {
        console.log('Received daily_stats_update:', data);

        var labels = [];
        var deliveredData = [];
        // var failureData = [];
        // var requestedData = [];

        for (var date in data) {
            labels.push(date);
            deliveredData.push(data[date].sms.delivered);
            // failureData.push(data[date].sms.failure);
            // requestedData.push(data[date].sms.requested);
        }

        // Update Chart.js
        myBarChart.data.labels = labels;
        myBarChart.data.datasets[0].data = deliveredData;
        myBarChart.update();
    });

    socket.on('error', function(data) {
        console.log('Error:', data);
    });

    sevenDaysButton.addEventListener('click', function() {
        socket.emit('fetch_daily_stats', serviceId);
        console.log('button click');  // Debug log, i'll delete later
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
