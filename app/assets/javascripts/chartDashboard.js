(function (window) {

    var socket = io();
    var serviceId = chart.getAttribute('data-service-id');

    socket.on('connect', function() {
        console.log('Connected to the server');  // Debug log, i'll delete later
        socket.emit('fetch_daily_stats', serviceId);
        socket.emit('fetch_single_month_notification_stats', serviceId);
        socket.emit('fetch_monthly_stats_by_year', serviceId);
    });

    //this is for previous 7 days
    socket.on('daily_stats_update', function(data) {
        console.log('Received daily_stats_update:', data);
        // Process the data
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
    //this is for a single month
    socket.on('single_month_notification_stats_update', function(data) {
        console.log('Received single_month_notification_stats_update:', data);
        // Update Chart.js with new data here
    });
    //this is for monthly stats by year
    socket.on('monthly_stats_by_year_update', function(data) {
        console.log('Received monthly_stats_by_year_update:', data);
        // Update Chart.js with new data here
    });

    socket.on('error', function(data) {
        console.log('Error:', data);
    });

    sevenDaysButton.addEventListener('click', function() {
        socket.emit('fetch_monthly_stats_by_year', serviceId);
        console.log('button click');  // Debug log, i'll delete later
    });

    // Initialize Chart.js bar chart
    var ctx = document.getElementById('myChart').getContext('2d');
    var myBarChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [], // Initialize with empty data
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
