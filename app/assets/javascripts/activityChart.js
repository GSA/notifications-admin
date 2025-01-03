(function (window) {

    if (document.getElementById('activityChartContainer')) {

        const COLORS = {
            delivered: '#0076d6',
            failed: '#fa9441',
            text: '#666'
        };

        const FONT_SIZE = 16;
        const FONT_WEIGHT = 'bold';
        const MAX_Y = 120;

        const createChart = function(containerId, labels, deliveredData, failedData) {
            const container = d3.select(containerId);
            container.selectAll('*').remove(); // Clear any existing content

            const margin = { top: 60, right: 20, bottom: 40, left: 20 }; // Adjusted top margin for legend
            const width = container.node().getBoundingClientRect().width - margin.left - margin.right;
            const height = 400 - margin.top - margin.bottom;

            const svg = container.append('svg')
                .attr('width', width + margin.left + margin.right)
                .attr('height', height + margin.top + margin.bottom)
                .append('g')
                .attr('transform', `translate(${margin.left},${margin.top})`);

            let tooltip = d3.select('#tooltip');

            if (tooltip.empty()) {
                tooltip = d3.select('body').append('div')
                    .attr('id', 'tooltip')
                    .style('display', 'none');
            }

            // Calculate total messages
            const totalMessages = d3.sum(deliveredData) + d3.sum(failedData);

            // Create legend only if there are messages
            const legendContainer = d3.select('.chart-legend');
            legendContainer.selectAll('*').remove(); // Clear any existing legend

            if (totalMessages > 0) {
                // Show legend if there are messages
                const legendData = [
                    { label: 'Delivered', color: COLORS.delivered },
                    { label: 'Failed', color: COLORS.failed }
                ];

                const legendItem = legendContainer.selectAll('.legend-item')
                    .data(legendData)
                    .enter()
                    .append('div')
                    .attr('class', 'legend-item');

                legendItem.append('div')
                    .attr('class', 'legend-rect')
                    .style('background-color', d => d.color)
                    .style('display', 'inline-block')
                    .style('margin-right', '5px');

                legendItem.append('span')
                    .attr('class', 'legend-label')
                    .text(d => d.label);

                // Ensure the legend is shown
                legendContainer.style('display', 'flex');
            } else {
                // Hide the legend if there are no messages
                legendContainer.style('display', 'none');
            }

            const x = d3.scaleBand()
                .domain(labels)
                .range([0, width])
                .padding(0.1);
                            // Adjust the y-axis domain to add some space above the tallest bar
            const maxY = d3.max(deliveredData.map((d, i) => d + (failedData[i] || 0)));
            const y = d3.scaleSqrt()
                .domain([0, maxY + 2]) // Add 2 units of space at the top
                .nice()
                .range([height, 0]);

            svg.append('g')
                .attr('class', 'x axis')
                .attr('transform', `translate(0,${height})`)
                .call(d3.axisBottom(x));

            // Generate the y-axis with whole numbers
            const yAxis = d3.axisLeft(y)
                .ticks(Math.min(maxY + 2, 10)) // Generate up to 10 ticks based on the data
                .tickFormat(d3.format('d')); // Ensure whole numbers on the y-axis

            svg.append('g')
                .attr('class', 'y axis')
                .call(yAxis);

            // Data for stacking
            const stackData = labels.map((label, i) => ({
                label: label,
                delivered: deliveredData[i],
                failed: failedData[i] || 0 // Ensure there's a value for failed, even if it's 0
            }));

            // Stack the data
            const stack = d3.stack()
                .keys(['delivered', 'failed'])
                .order(d3.stackOrderNone)
                .offset(d3.stackOffsetNone);

            const series = stack(stackData);

            // Color scale
            const color = d3.scaleOrdinal()
                .domain(['delivered', 'failed'])
                .range([COLORS.delivered, COLORS.failed]);

        // Create bars with animation
        const barGroups = svg.selectAll('.bar-group')
            .data(series)
            .enter()
            .append('g')
            .attr('class', 'bar-group')
            .attr('fill', d => color(d.key));

        barGroups.selectAll('rect')
            .data(d => d)
            .enter()
            .append('rect')
            .attr('x', d => x(d.data.label))
            .attr('y', height)
            .attr('height', 0)
            .attr('width', x.bandwidth())
            .on('mouseover', function(event, d) {
                const key = d3.select(this.parentNode).datum().key;
                const capitalizedKey = key.charAt(0).toUpperCase() + key.slice(1);
                tooltip.style('display', 'block')
                    .html(`${d.data.label}<br>${capitalizedKey}: ${d.data[key]}`);
            })
            .on('mousemove', function(event) {
                tooltip.style('left', `${event.pageX + 10}px`)
                    .style('top', `${event.pageY - 20}px`);
            })
            .on('mouseout', function() {
                tooltip.style('display', 'none');
            })
            .transition()
            .duration(1000)
            .attr('y', d => y(d[1]))
            .attr('height', d => y(d[0]) - y(d[1]));
    };

    // Function to create an accessible table
    const createTable = function(tableId, chartType, labels, deliveredData, failedData) {
        const table = document.getElementById(tableId);
        table.innerHTML = ""; // Clear previous data

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
        table.append(tbody);
    };

    const fetchData = function(type) {
        var ctx = document.getElementById('weeklyChart');
        if (!ctx) {
            return;
        }

        var url = type === 'service' ? `/daily_stats.json` : `/daily_stats_by_user.json`;
        return fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                labels = [];
                deliveredData = [];
                failedData = [];

                let totalMessages = 0;

                for (var dateString in data) {
                    if (data.hasOwnProperty(dateString)) {
                        const dateParts = dateString.split('-');
                        const formattedDate = `${dateParts[1]}/${dateParts[2]}/${dateParts[0].slice(2)}`;

                        labels.push(formattedDate);
                        deliveredData.push(data[dateString].sms.delivered);
                        failedData.push(data[dateString].sms.failure);

                        // Calculate the total number of messages
                        totalMessages += data[dateString].sms.delivered + data[dateString].sms.failure;
                    }
                }

                // Check if there are no messages sent
                const subTitle = document.querySelector(`#activityChartContainer .chart-subtitle`);
                if (totalMessages === 0) {
                    // Remove existing chart and render the alert message
                    d3.select('#weeklyChart').selectAll('*').remove();
                    d3.select('#weeklyChart')
                        .append('div')
                        .html(`
                            <div class="usa-alert usa-alert--info usa-alert--slim">
                                <div class="usa-alert__body">
                                    <p class="usa-alert__text">
                                        No messages sent in the last 7 days
                                    </p>
                                </div>
                            </div>
                        `);
                    // Hide the subtitle
                    if (subTitle) {
                        subTitle.style.display = 'none';
                    }
                } else {
                    // If there are messages, create the chart and table
                    createChart('#weeklyChart', labels, deliveredData, failedData);
                    createTable('weeklyTable', 'activityChart', labels, deliveredData, failedData);
                }

                return data;
            })
            .catch(error => console.error('Error fetching daily stats:', error));
    };

    const handleDropdownChange = function(event) {
        const selectedValue = event.target.value;
        const subTitle = document.querySelector(`#activityChartContainer .chart-subtitle`);
        const selectElement = document.getElementById('options');
        const selectedText = selectElement.options[selectElement.selectedIndex].text;

        subTitle.textContent = `${selectedText} - last 7 days`;
        fetchData(selectedValue);

        // Update ARIA live region
        const liveRegion = document.getElementById('aria-live-account');
        liveRegion.textContent = `Data updated for ${selectedText} - last 7 days`;

        // Switch tables based on dropdown selection
        const selectedTable = selectedValue === "individual" ? "table1" : "table2";
        const tables = document.querySelectorAll('.table-overflow-x-auto');
        tables.forEach(function(table) {
            table.classList.add('hidden'); // Hide all tables by adding the hidden class
            table.classList.remove('visible'); // Ensure they are not visible
        });
        const tableToShow = document.getElementById(selectedTable);
        tableToShow.classList.remove('hidden'); // Remove hidden class
        tableToShow.classList.add('visible'); // Add visible class
    };

    document.addEventListener('DOMContentLoaded', function() {
        // Initialize activityChart chart and table with service data by default
        fetchData('service');

        // Add event listener to the dropdown
        const dropdown = document.getElementById('options');
        dropdown.addEventListener('change', handleDropdownChange);
    });

        // Resize chart on window resize
        window.addEventListener('resize', function() {
            if (labels.length > 0 && deliveredData.length > 0 && failedData.length > 0) {
                createChart('#weeklyChart', labels, deliveredData, failedData);
                createTable('weeklyTable', 'activityChart', labels, deliveredData, failedData);
            }
        });

        // Export functions for testing
        window.createChart = createChart;
        window.createTable = createTable;
        window.handleDropdownChange = handleDropdownChange;
        window.fetchData = fetchData;
    }

})(window);
