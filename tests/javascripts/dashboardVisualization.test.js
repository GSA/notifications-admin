const path = require('path');
const fs = require('fs');

// Load the D3 script content
const d3ScriptContent = fs.readFileSync(path.resolve(__dirname, '../javascripts/support/d3.min.js'), 'utf-8');

// Helper function to dynamically load a script
function loadScript(scriptContent) {
  const script = document.createElement('script');
  script.textContent = scriptContent;
  document.head.appendChild(script);
}

// Mocking `clientWidth`
Object.defineProperty(HTMLElement.prototype, 'clientWidth', {
  value: 600,
  writable: true,
});

// beforeAll hook to set up the DOM and load D3.js script
beforeAll(done => {
  // Set up the DOM with the D3 script included
  document.body.innerHTML = `
    <div id="totalMessageChartContainer" data-sms-sent="100" data-sms-allowance-remaining="249900" style="width: 600px;">
      <h1 id="chartTitle">Total Messages</h1>
      <svg id="totalMessageChart"></svg>
    </div>
    <div id="totalMessageTable"></div>
    <div id="message"></div>
    <div class="tooltip hidden"></div>
    <div id="activityChartContainer">
      <form class="usa-form">
        <label class="usa-label" for="options">Account</label>
        <select class="usa-select margin-bottom-2" name="options" id="options">
          <option value="">- Select -</option>
          <option value="service" selected>Service Name</option>
          <option value="individual">User Name</option>
        </select>
      </form>
      <div id="activityChart">
        <div class="chart-header">
          <div class="chart-subtitle">Service Name - Last 7 Days</div>
          <div class="chart-legend" aria-label="Legend"></div>
        </div>
        <div class="chart-container" id="weeklyChart" data-service-id="12345"></div>
        <table id="weeklyTable" class="usa-sr-only usa-table"></table>
      </div>
    </div>
    <div id="aria-live-account" class="usa-sr-only" aria-live="polite"></div>
  `;

  // Load the D3 script dynamically
  loadScript(d3ScriptContent);

  // Wait a bit to ensure the script is executed
  setTimeout(() => {

    // Require the actual JavaScript file you are testing
    require('../../app/assets/javascripts/dashboardVisualization.js');

    // Call the function to create the chart
    window.createTotalMessagesChart();

    done();
  }, 100);
});

// Single test to check if D3 is loaded correctly
test('D3 is loaded correctly', () => {
    // Check if D3 is loaded by verifying the existence of the d3 object
    expect(window.d3).toBeDefined();
    expect(typeof window.d3.version).toBe('string');
});

  // Test to check if the SVG element is correctly set up
test('SVG element is correctly set up', () => {
    const svg = document.getElementById('totalMessageChart');
    expect(svg).not.toBeNull();
    expect(svg.getAttribute('width')).toBe('600');
    expect(svg.getAttribute('height')).toBe('64');
});

  // Test to check if the table is created and populated correctly
test('Populates the accessible table correctly', () => {
    const table = document.getElementById('totalMessageTable').getElementsByTagName('table')[0];
    expect(table).toBeDefined();

    const rows = table.getElementsByTagName('tr');
    expect(rows.length).toBe(2); // Header + 1 data row

    const headers = rows[0].getElementsByTagName('th');
    expect(headers[0].textContent).toBe('Messages Sent');
    expect(headers[1].textContent).toBe('Remaining');

    const firstRowCells = rows[1].getElementsByTagName('td');
    expect(firstRowCells[0].textContent).toBe('100');
    expect(firstRowCells[1].textContent).toBe('249,900');
});

  // Test to check if the chart title is correctly set
test('Chart title is correctly set', () => {
    const chartTitle = document.getElementById('chartTitle').textContent;
    expect(chartTitle).toBe('Total Messages');
});

// Test to check if the chart resizes correctly on window resize
test('Chart resizes correctly on window resize', done => {
    setTimeout(() => {
        const svg = document.getElementById('totalMessageChart');
        const chartContainer = document.getElementById('totalMessageChartContainer');

        // Initial check
        expect(svg.getAttribute('width')).toBe('600');

        // Set new container width
        Object.defineProperty(chartContainer, 'clientWidth', { value: 800 });

        // Trigger resize event
        window.dispatchEvent(new Event('resize'));

        setTimeout(() => {
        // Check if SVG width is updated
        expect(svg.getAttribute('width')).toBe('800');
        done();
        }, 500); // Adjust the timeout if necessary
    }, 1000); // Initial wait for the chart to render
}, 10000); // Adjust the overall test timeout if necessary

test('Populates the accessible table for activity chart correctly', () => {
// Mock fetchData to provide sample data for the table
    const sampleData = {
        '2024-07-01': { sms: { delivered: 50, failed: 5 } },
        '2024-07-02': { sms: { delivered: 60, failed: 2 } },
        '2024-07-03': { sms: { delivered: 70, failed: 1 } },
        '2024-07-04': { sms: { delivered: 80, failed: 0 } },
        '2024-07-05': { sms: { delivered: 90, failed: 3 } },
        '2024-07-06': { sms: { delivered: 100, failed: 4 } },
        '2024-07-07': { sms: { delivered: 110, failed: 2 } },
    };

    const labels = Object.keys(sampleData).map(dateString => {
    const dateParts = dateString.split('-');
        return `${dateParts[1]}/${dateParts[2]}/${dateParts[0].slice(2)}`; // Format to MM/DD/YY
    });
    const deliveredData = Object.values(sampleData).map(d => d.sms.delivered);
    const failedData = Object.values(sampleData).map(d => d.sms.failed);

    window.createTable('weeklyTable', 'activityChart', labels, deliveredData, failedData);

    const table = document.getElementById('weeklyTable');
    expect(table).toBeDefined();

    const rows = table.getElementsByTagName('tr');
    expect(rows.length).toBe(8); // Header + 7 data rows

    const headers = rows[0].getElementsByTagName('th');
    expect(headers[0].textContent).toBe('Day');
    expect(headers[1].textContent).toBe('Delivered');
    expect(headers[2].textContent).toBe('Failed');

    // Check the content of the first data row
    const firstRowCells = rows[1].getElementsByTagName('td');
    expect(firstRowCells[0].textContent).toBe('07/01/24');
    expect(firstRowCells[1].textContent).toBe('50');
    expect(firstRowCells[2].textContent).toBe('5');
});

test('updates subtitle and aria-live region correctly', () => {
    const fetchDataSpy = jest.spyOn(window, 'fetchData');

    // Initial check before changing the dropdown
    let subTitle = document.querySelector('.chart-subtitle');
    expect(subTitle.textContent).toBe('Service Name - Last 7 Days');

    let ariaLiveRegion = document.getElementById('aria-live-account');
    expect(ariaLiveRegion.textContent).toBe('Data updated for Service Name - Last 7 Days');

    // Change dropdown to 'individual'
    const dropdown = document.getElementById('options');
    dropdown.value = 'individual';

    handleDropdownChange({ target: dropdown });

    // Check the subtitle and aria-live region for 'individual'
    subTitle = document.querySelector('.chart-subtitle');
    expect(subTitle.textContent).toBe('User Name - Last 7 Days');

    ariaLiveRegion = document.getElementById('aria-live-account');
    expect(ariaLiveRegion.textContent).toBe('Data updated for User Name - Last 7 Days');

    // Change dropdown back to 'service'
    dropdown.value = 'service';
    handleDropdownChange({ target: dropdown });

    // Check the subtitle and aria-live region for 'service'
    subTitle = document.querySelector('.chart-subtitle');
    expect(subTitle.textContent).toBe('Service Name - Last 7 Days');

    ariaLiveRegion = document.getElementById('aria-live-account');
    expect(ariaLiveRegion.textContent).toBe('Data updated for Service Name - Last 7 Days');

});

// Testing the tooltip
test('Tooltip displays on hover', () => {
    document.body.innerHTML = `
        <div id="totalMessageChartContainer" data-sms-sent="100" data-sms-allowance-remaining="249900" style="width: 600px;">
            <h1 id="chartTitle">Total Messages</h1>
            <svg id="totalMessageChart"></svg>
        </div>
        <div id="totalMessageTable"></div>
        <div id="message"></div>
    `;

    createTotalMessagesChart();

    const svg = document.getElementById('totalMessageChart');
    const sentBar = svg.querySelector('rect[fill="#0076d6"]');

    const event = new Event('mouseover');
    sentBar.dispatchEvent(event);

    const tooltip = document.getElementById('tooltip');
    expect(tooltip.style.display).toBe('block');
    expect(tooltip.innerHTML).toContain('Messages Sent: 100');
});

test('SVG bars are created and animated correctly', done => {
    const svg = document.getElementById('totalMessageChart');

    // Initial check
    const sentBar = svg.querySelector('rect[fill="#0076d6"]');
    const remainingBar = svg.querySelector('rect[fill="#fa9441"]');

    expect(sentBar).not.toBeNull();
    expect(remainingBar).not.toBeNull();
    expect(sentBar.getAttribute('width')).toBe('0');
    expect(remainingBar.getAttribute('width')).toBe('0');

    // Wait for the animation to complete
    setTimeout(() => {
        expect(parseInt(sentBar.getAttribute('width'))).toBeGreaterThan(0);
        expect(parseInt(remainingBar.getAttribute('width'))).toBeGreaterThan(0);
        done();
    }, 1500); // Duration of the animation + buffer time
});
