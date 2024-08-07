(function (window) {

    function initializeChartAndSocket() {
        var ctx = document.getElementById('myChart');
        if (!ctx) {
            return;
        }

        var myBarChart = new Chart(ctx.getContext('2d'), {
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
                animation: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        var socket = io();

        socket.on('connect', function() {
            socket.emit('fetch_daily_stats_by_user');
        });

        socket.on('daily_stats_by_user_update', function(data) {
            // console.log('Data received:', data);
            var labels = [];
            var deliveredData = [];
            var failedData = [];

            for (var date in data) {
                labels.push(date);
                deliveredData.push(data[date].sms.delivered);

            }

            myBarChart.data.labels = labels;
            myBarChart.data.datasets[0].data = deliveredData;
            myBarChart.update();
        });

        socket.on('error', function(data) {
            // console.log('Error:', data);
        });

        var sevenDaysButton = document.getElementById('sevenDaysButton');
        if (sevenDaysButton) {
            sevenDaysButton.addEventListener('click', function() {
                socket.emit('fetch_daily_stats_by_user');
                // console.log('clicked');
            });
        }
    }

    document.addEventListener('DOMContentLoaded', initializeChartAndSocket);

})(window);
