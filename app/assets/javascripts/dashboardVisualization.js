(function (window) {
    const COLORS = {
        delivered: '#0076d6',
        failed: '#fa9441',
        text: '#666'
    };

    const FONT_SIZE = 16;
    const FONT_WEIGHT = 'bold';
    const MAX_Y = 120;

    // Function to create a stacked bar chart with animation using D3.js
    function createChart(containerId, labels, deliveredData, failedData) {
        const container = d3.select(containerId);
        container.selectAll('*').remove(); // Clear any existing content

        // Dynamically create tooltip element
        const tooltip = container.append('div')
            .attr('id', 'tooltip');

        const margin = { top: 60, right: 20, bottom: 40, left: 20 }; // Adjusted top margin for legend
        const width = container.node().getBoundingClientRect().width - margin.left - margin.right;
        const height = 400 - margin.top - margin.bottom;

        const svg = container.append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        // Create legend
        const legend = svg.append('g')
            .attr('class', 'legend')
            .attr('transform', `translate(${width - 200},-40)`); // Adjust the position of the legend

        const legendData = [
            { label: 'Delivered', color: COLORS.delivered },
            { label: 'Failed', color: COLORS.failed }
        ];

        const legendItem = legend.selectAll('.legend-item')
            .data(legendData)
            .enter()
            .append('g')
            .attr('class', 'legend-item')
            .attr('transform', (d, i) => `translate(${i * 100},0)`); // Adjust the spacing between legend items

        legendItem.append('rect')
            .attr('width', 18)
            .attr('height', 18)
            .attr('fill', d => d.color);

        legendItem.append('text')
            .attr('x', 24)
            .attr('y', 9)
            .attr('dy', '0.35em')
            .style('text-anchor', 'start')
            .text(d => d.label);

        const x = d3.scaleBand()
            .domain(labels)
            .range([0, width])
            .padding(0.1);

        // Adjust the y-axis domain to add some space above the tallest bar
        const maxY = d3.max(deliveredData.map((d, i) => d + (failedData[i] || 0)));
        const y = d3.scaleLinear()
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
                const containerPosition = container.node().getBoundingClientRect();
                tooltip.style('left', `${event.clientX - containerPosition.left + 10}px`)
                    .style('top', `${event.clientY - containerPosition.top + 10}px`);
            })
            .on('mouseout', function() {
                tooltip.style('display', 'none');
            })
            .transition()
            .duration(1000)
            .attr('y', d => y(d[1]))
            .attr('height', d => y(d[0]) - y(d[1]));
    }

    // Function to create an accessible table
    function createTable(tableId, chartType, labels, deliveredData, failedData) {
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
    }

    function fetchServiceData() {
        var ctx = document.getElementById('weeklyChart');
        if (!ctx) {
            return;
        }

        var socket = io();
        var serviceId = ctx.getAttribute('data-service-id');

        socket.on('connect', function() {
            socket.emit('fetch_daily_stats', serviceId);
        });

        socket.on('daily_stats_update', function(data) {
            var labels = [];
            var deliveredData = [];
            var failedData = [];

            for (var date in data) {
                labels.push(date);
                deliveredData.push(data[date].sms.delivered);
                failedData.push(data[date].sms.failed !== undefined ? data[date].sms.failed : 0);
            }

            createChart('#weeklyChart', labels, deliveredData, failedData);
            createTable('weeklyTable', 'Weekly', labels, deliveredData, failedData);
        });

        socket.on('error', function(data) {
            console.log('Error:', data);
        });
    }

    // Function to handle dropdown change
    function handleDropdownChange(event) {
        const selectedValue = event.target.value;
        const subTitle = document.querySelector(`#chartsArea .chart-subtitle`);
        const selectElement = document.getElementById('options');
        const selectedText = selectElement.options[selectElement.selectedIndex].text;

        if (selectedValue === "individual") {
            // Mock individual data
            const labels = ["2024-06-06", "2024-06-07", "2024-06-08", "2024-06-09", "2024-06-10", "2024-06-11", "2024-06-12"];
            const deliveredData = labels.map(() => Math.floor(Math.random() * 5) + 1); // Random between 1 and 5
            const failedData = [0, 1, 0, 0, 1, 2, 1];
            subTitle.textContent = selectedText + " - Last 7 Days";
            createChart('#weeklyChart', labels, deliveredData, failedData);
            createTable('weeklyTable', 'Weekly', labels, deliveredData, failedData);
        } else if (selectedValue === "service") {
            subTitle.textContent = selectedText + " - Last 7 Days";
            // Fetch and use real service data
            fetchServiceData();
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        // Initialize weekly chart and table with service data by default
        fetchServiceData();

        // Add event listener to the dropdown
        const dropdown = document.getElementById('options');
        dropdown.addEventListener('change', handleDropdownChange);
    });
})(window);
