 document.addEventListener('DOMContentLoaded', function() {
    // Define constants
    const COLORS = {
        delivered: '#0076d6',
        failed: '#fa9441',
        text: '#666'
    };

    const FONT_SIZE = 16;
    const FONT_WEIGHT = 'bold';
    const MAX_Y = 120;

    const tabButtons = document.querySelectorAll('.tablinks');
    let monthlyChartInitialized = false;
    let yearlyChartInitialized = false;


    // Function to create a chart
    function createChart(ctx, labels, deliveredData, failedData) {
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Delivered',
                    data: deliveredData,
                    backgroundColor: COLORS.delivered,
                    stack: 'Stack 0'
                }, {
                    label: 'Failed',
                    data: failedData,
                    backgroundColor: COLORS.failed,
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
                        max: MAX_Y,
                        title: {
                            display: true,
                            text: 'SMS Sent',
                            color: COLORS.text,
                            font: {
                                size: FONT_SIZE,
                                weight: FONT_WEIGHT
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end',
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
    }

    // Function to get number of days in a month
    function getDaysInMonth(year, month) {
        return new Date(year, month + 1, 0).getDate();
    }

    function generateYearlyData(labels) {
        const deliveredData = labels.map((label, index) => {
            return index < 6 ? Math.floor(Math.random() * 81) + 20 : 0; // Random between 20 and 100 for months Jan-June, zero for others
        });
        const failedData = deliveredData.map(delivered => Math.floor(delivered * (Math.random() * 0.15 + 0.05))); // 5-20% of delivered
        return { deliveredData, failedData };
    }

    // Function to generate random data
    function generateRandomData(labels) {
        const deliveredData = labels.map(() => Math.floor(Math.random() * 81) + 20); // Random between 20 and 100
        const failedData = deliveredData.map(delivered => Math.floor(delivered * (Math.random() * 0.15 + 0.05))); // 5-20% of delivered
        return { deliveredData, failedData };
    }

    // Function to create an accessible table
    function createTable(tableId, chartType, labels, deliveredData, failedData) {
        const table = document.getElementById(tableId);
        const captionText = document.querySelector(`#${chartType} .chart-subtitle`).textContent;
        const caption = document.createElement('caption');
        caption.textContent = captionText;
        const thead = document.createElement('thead');
        const tbody = document.createElement('tbody');

        // Create table header
        const headerRow = document.createElement('tr');
        const headers = ['Day', 'Delivered', 'Failed'];
        headers.forEach(headerText => {
            const th = document.createElement('th');
            th.textContent = headerText;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);

        // Create table body
        labels.forEach((label, index) => {
            const row = document.createElement('tr');
            const cellDay = document.createElement('td');
            cellDay.textContent = label;
            row.appendChild(cellDay);

            const cellDelivered = document.createElement('td');
            cellDelivered.textContent = deliveredData[index];
            row.appendChild(cellDelivered);

            const cellFailed = document.createElement('td');
            cellFailed.textContent = failedData[index];
            row.appendChild(cellFailed);

            tbody.appendChild(row);
        });

        table.appendChild(caption);
        table.appendChild(thead);
        table.appendChild(tbody);
    }

    // Function to handle tab switching
    function openTab(button, tabName) {
        // Hide all tab contents
        document.querySelectorAll('.tabcontent').forEach(content => {
            content.style.display = 'none';
        });

        // Remove "active" class from all buttons
        tabButtons.forEach(button => {
            button.classList.remove('active');
        });

        // Show the current tab and add "active" class to the button
        document.getElementById(tabName).style.display = 'block';
        button.classList.add('active');

        // Initialize monthly chart if the "Monthly" tab is clicked
        if (tabName === 'Monthly' && !monthlyChartInitialized) {
            const monthlyCtx = document.getElementById('monthlyChart').getContext('2d');
            const now = new Date();
            const daysInMonth = getDaysInMonth(now.getFullYear(), now.getMonth());
            const monthlyLabels = Array.from({ length: daysInMonth }, (_, i) => `${i + 1}`);
            const { deliveredData, failedData } = generateRandomData(monthlyLabels);
            createChart(monthlyCtx, monthlyLabels, deliveredData, failedData);
            createTable('monthlyTable', 'Monthly', monthlyLabels, deliveredData, failedData);
            monthlyChartInitialized = true;
        }

         // Initialize yearly chart if the "Yearly" tab is clicked
        if (tabName === 'Yearly' && !yearlyChartInitialized) {
            const yearlyCtx = document.getElementById('yearlyChart').getContext('2d');
            const yearlyLabels = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
                    const { deliveredData, failedData } = generateYearlyData(yearlyLabels);
            createChart(yearlyCtx, yearlyLabels, deliveredData, failedData);
            createTable('yearlyTable', 'Yearly', yearlyLabels, deliveredData, failedData);
            yearlyChartInitialized = true;
        }
    }

    // Add event listeners to the tab buttons
    tabButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            openTab(this, this.getAttribute('data-tab'));
        });
    });

    // Show the first tab by default
    tabButtons[0].click();

    // Initialize weekly chart and table
    const weeklyCtx = document.getElementById('weeklyChart').getContext('2d');
    const weeklyLabels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const { deliveredData: weeklyDeliveredData, failedData: weeklyFailedData } = generateRandomData(weeklyLabels);
    createChart(weeklyCtx, weeklyLabels, weeklyDeliveredData, weeklyFailedData);
    createTable('weeklyTable', 'Weekly', weeklyLabels, weeklyDeliveredData, weeklyFailedData);
});
