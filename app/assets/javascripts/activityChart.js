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

            // Check if there is any data in deliveredData or failedData before creating the legend
            const totalMessages = d3.sum(deliveredData) + d3.sum(failedData);

            const legendContainer = d3.select('.chart-legend');

            if (totalMessages === 0) {
                legendContainer.style('display', 'none');  // Try manually setting this in the console to see if it hides the legend
                console.log('Hiding legend');  // Ensure this branch is being hit
            } else {
                legendContainer.style('display', 'flex');
                console.log('Showing legend');
            }

            if (totalMessages > 0) {
                // Create legend only if there is data
                legendContainer.selectAll('*').remove(); // Clear any existing legend

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

                legendContainer.style('display', 'flex');  // Ensure the legend is shown
            } else {
                // Hide legend container if there is no data
                legendContainer.style('display', 'none');   // Hide the legend
            }

            // Proceed with creating the chart as usual
            const x = d3.scaleBand()
                .domain(labels)
                .range([0, width])
                .padding(0.1);

            const maxY = d3.max(deliveredData.map((d, i) => d + (failedData[i] || 0)));
            const y = d3.scaleSqrt()
                .domain([0, maxY + 2]) // Add 2 units of space at the top
                .nice()
                .range([height, 0]);

            svg.append('g')
                .attr('class', 'x axis')
                .attr('transform', `translate(0,${height})`)
                .call(d3.axisBottom(x));

            const yAxis = d3.axisLeft(y)
                .ticks(Math.min(maxY + 2, 10))
                .tickFormat(d3.format('d'));

            svg.append('g')
                .attr('class', 'y axis')
                .call(yAxis);

            const stackData = labels.map((label, i) => ({
                label: label,
                delivered: deliveredData[i],
                failed: failedData[i] || 0 // Ensure there's a value for failed, even if it's 0
            }));

            const stack = d3.stack()
                .keys(['delivered', 'failed'])
                .order(d3.stackOrderNone)
                .offset(d3.stackOffsetNone);

            const series = stack(stackData);

            const color = d3.scaleOrdinal()
                .domain(['delivered', 'failed'])
                .range([COLORS.delivered, COLORS.failed]);

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

        const fetchData = function(type) {
            const ctx = document.getElementById('weeklyChart');
            if (!ctx) {
                return;
            }

            const url = type === 'service' ? `/daily_stats.json` : `/daily_stats_by_user.json`;
            return fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {

                    let labels = [];
                    let deliveredData = [];
                    let failedData = [];

                    let totalMessages = 0;

                    for (var dateString in data) {
                        if (data.hasOwnProperty(dateString)) {
                            const dateParts = dateString.split('-');
                            const formattedDate = `${dateParts[1]}/${dateParts[2]}/${dateParts[0].slice(2)}`;

                            labels.push(formattedDate);
                            deliveredData.push(data[dateString].sms.delivered || 0);  // Fallback to 0 if missing
                            failedData.push(data[dateString].sms.failure || 0);  // Fallback to 0 if missing

                            totalMessages += data[dateString].sms.delivered + data[dateString].sms.failure;
                        }
                    }


                    const subTitle = document.querySelector(`#activityChartContainer .chart-subtitle`);
                    const liveRegion = document.getElementById('aria-live-account');

                    if (totalMessages === 0) {
                        d3.select('#weeklyChart').selectAll('*').remove();
                        d3.select('#weeklyChart')
                            .append('div')
                            .html(`
                                <div class="usa-alert usa-alert--info usa-alert--slim" aria-live="polite">
                                    <div class="usa-alert__body">
                                        <p class="usa-alert__text">
                                            No messages sent in the last 7 days
                                        </p>
                                    </div>
                                </div>
                            `);
                        if (subTitle) {
                            subTitle.style.display = 'none';
                        }
                        liveRegion.textContent = `No data available for ${type} - last 7 days.`;

                        // Here: Check if the legend exists and remove it if necessary
                        const legendContainer = document.querySelector('.chart-legend');
                        if (legendContainer) {
                            console.log('Legend exists, hiding it...');
                            legendContainer.style.display = 'none';  // Hide the legend
                        } else {
                            console.log('Legend does not exist at this point.');
                        }

                    } else {
                        createChart('#weeklyChart', labels, deliveredData, failedData);
                        liveRegion.textContent = `Data updated for ${type} - last 7 days.`;

                        // Check if legend should be shown after chart is created
                        const legendContainer = document.querySelector('.chart-legend');
                        if (legendContainer) {
                            console.log('Legend exists, showing it...');
                            legendContainer.style.display = 'flex';  // Show the legend
                        } else {
                            console.log('Legend does not exist at this point.');
                        }
                    }

                    return data;
                })
                .catch(error => console.error('Error fetching daily stats:', error));
        };

        document.addEventListener('DOMContentLoaded', function() {
            fetchData('service');

            const dropdown = document.getElementById('options');
            dropdown.addEventListener('change', function(event) {
                fetchData(event.target.value);
            });
        });
    }

})(window);
