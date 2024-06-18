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
                        label: 'Requested',
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

        var socket = io();

        socket.on('connect', function() {
            socket.emit('fetch_daily_stats');
        });

        socket.on('daily_stats_update', function(data) {
            // console.log('Data received:', data);
            var labels = [];
            var requestedData = [];

            for (var date in data) {
                labels.push(date);
                requestedData.push(data[date].sms.requested);
            }

            myBarChart.data.labels = labels;
            myBarChart.data.datasets[0].data = requestedData;
            myBarChart.update();
        });

        socket.on('error', function(data) {
            // console.log('Error:', data);
        });

        var sevenDaysButton = document.getElementById('sevenDaysButton');
        if (sevenDaysButton) {
            sevenDaysButton.addEventListener('click', function() {
                socket.emit('fetch_daily_stats');
                // console.log('clicked');
            });
        }
    }

    document.addEventListener('DOMContentLoaded', initializeChartAndSocket);

})(window);
