(function (window) {
    var chartContainer = document.getElementById('chartContainer');
    var chartTitle = document.getElementById('chartTitle').textContent;
    var sms_sent = 100;
    var sms_remaining_messages = 249900;
    var totalMessages = sms_sent + sms_remaining_messages;

    // Update the message below the chart
    document.getElementById('message').innerText = `${sms_sent.toLocaleString()} sent / ${sms_remaining_messages.toLocaleString()} remaining`;
    console.log('Message element textContent set to:', document.getElementById('message').innerText);

    // Set a minimum value for "Messages Sent" based on a percentage of the remaining messages
    var minSentPercentage = 0.01; // Minimum width as a percentage of total messages (1% in this case)
    var minSentValue = totalMessages * minSentPercentage;
    var displaySent = Math.max(sms_sent, minSentValue);
    var displayRemaining = totalMessages - displaySent;

    var svg = d3.select("#totalMessageChart");
    var width = chartContainer.clientWidth;
    var height = 64;
    svg.attr("width", width).attr("height", height);

    var x = d3.scaleLinear()
        .domain([0, totalMessages])
        .range([0, width]);

    var tooltip = d3.select(".tooltip");

    var data = [
        { label: 'Messages Sent', value: displaySent, actualValue: sms_sent, color: '#0076d6' },
        { label: 'Remaining', value: displayRemaining, actualValue: sms_remaining_messages, color: '#fa9441' }
    ];

    var totalAnimationDuration = 1000; // Total animation duration in milliseconds
    var sentPercentage = displaySent / totalMessages;
    var remainingPercentage = displayRemaining / totalMessages;

    var sentDuration = totalAnimationDuration * sentPercentage;
    var remainingDuration = totalAnimationDuration * remainingPercentage;

    var bars = svg.selectAll("rect")
        .data(data)
        .enter()
        .append("rect")
        .attr("x", (d, i) => i === 0 ? 0 : x(data[0].value))
        .attr("y", 0)
        .attr("width", 0)  // Start with width 0 for animation
        .attr("height", height)
        .attr("fill", d => d.color)
        .on("mousemove", function (event, d) {
            tooltip.classed("hidden", false)
                .style("left", event.pageX + "px")
                .style("top", event.pageY - 28 + "px")
                .html(d.label + ": " + d.actualValue.toLocaleString());
        })
        .on("mouseout", function () {
            tooltip.classed("hidden", true);
        });

    // Animate "Messages Sent" first
    bars.filter((d, i) => i === 0)
        .transition()
        .duration(sentDuration)  // Animation duration for "Messages Sent"
        .attr("width", d => x(d.value))
        .on("end", function() {
            // Animate "Remaining" immediately after "Messages Sent"
            bars.filter((d, i) => i === 1)
                .transition()
                .duration(remainingDuration)  // Animation duration for "Remaining"
                .attr("width", d => x(d.value));
        });

    // Create and populate the accessible table
    var tableContainer = document.getElementById('totalMessageTable');
    var table = document.createElement('table');
    table.className = 'usa-sr-only usa-table';

    var caption = document.createElement('caption');
    caption.textContent = chartTitle;
    table.appendChild(caption);

    var thead = document.createElement('thead');
    var theadRow = document.createElement('tr');
    var thLabel = document.createElement('th');
    thLabel.textContent = 'Label';
    var thValue = document.createElement('th');
    thValue.textContent = 'Value';
    theadRow.appendChild(thLabel);
    theadRow.appendChild(thValue);
    thead.appendChild(theadRow);
    table.appendChild(thead);

    var tbody = document.createElement('tbody');
    var tableData = [
        { label: 'Messages Sent', value: sms_sent.toLocaleString() },
        { label: 'Remaining', value: sms_remaining_messages.toLocaleString() }
    ];

    tableData.forEach(function (rowData) {
        var row = document.createElement('tr');
        var cellLabel = document.createElement('td');
        var cellValue = document.createElement('td');
        cellLabel.textContent = rowData.label;
        cellValue.textContent = rowData.value;
        row.appendChild(cellLabel);
        row.appendChild(cellValue);
        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    tableContainer.appendChild(table);

    // Ensure the chart resizes correctly on window resize
    window.addEventListener('resize', function () {
        width = chartContainer.clientWidth;
        x.range([0, width]);
        svg.attr("width", width);
        svg.selectAll("rect")
            .attr("width", d => x(d.value))
            .attr("x", (d, i) => i === 0 ? 0 : x(data[0].value));
    });
})(window);
