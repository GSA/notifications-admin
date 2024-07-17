(function (window) {
    var chartContainer = document.getElementById('chartContainer');
    if (chartContainer) {
        var chartTitle = document.getElementById('chartTitle').textContent;

        // Access data attributes from the HTML
        var sms_sent = parseInt(chartContainer.getAttribute('data-sms-sent'));
        var sms_remaining_messages = parseInt(chartContainer.getAttribute('data-sms-allowance-remaining'));
        var totalMessages = sms_sent + sms_remaining_messages;

        // Update the message below the chart
        document.getElementById('message').innerText = `${sms_sent.toLocaleString()} sent / ${sms_remaining_messages.toLocaleString()} remaining`;

        // Calculate minimum width for "Messages Sent" as 1% of the total chart width
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

        // Create tooltip dynamically
        var tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("position", "absolute")
            .style("background", "#fff")
            .style("border", "1px solid #ccc")
            .style("padding", "5px")
            .style("box-shadow", "0px 0px 10px rgba(0, 0, 0, 0.1)")
            .style("pointer-events", "none")
            .style("display", "none");

        // Create the initial bars
        var sentBar = svg.append("rect")
            .attr("x", 0)
            .attr("y", 0)
            .attr("height", height)
            .attr("fill", '#0076d6')
            .attr("width", 0); // Start with width 0 for animation

        var remainingBar = svg.append("rect")
            .attr("x", 0) // Initially set to 0, will be updated during animation
            .attr("y", 0)
            .attr("height", height)
            .attr("fill", '#fa9441')
            .attr("width", 0); // Start with width 0 for animation

        // Animate the bars together as a single cohesive line
        svg.transition()
            .duration(1000)  // Total animation duration
            .attr("width", width)
            .tween("resize", function() {
                var interpolator = d3.interpolate(0, width);
                return function(t) {
                    var newWidth = interpolator(t);
                    var sentWidth = x(displaySent) / width * newWidth;
                    var remainingWidth = x(displayRemaining) / width * newWidth;
                    sentBar.attr("width", sentWidth);
                    remainingBar.attr("x", sentWidth).attr("width", remainingWidth);
                };
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
        table.appendChild(theadRow);
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
            sentBar.attr("width", x(displaySent));
            remainingBar.attr("x", x(displaySent)).attr("width", x(displayRemaining));
        });
    }
})(window);
