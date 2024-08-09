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
    <div id="activityChartContainer" data-daily-stats="{{ daily_stats }}" data-daily_stats_by_user="{{ daily_stats_by_user }}">
      <form class="usa-form">
        <label class="usa-label" for="options">Account</label>
        <select class="usa-select margin-bottom-2" name="options" id="options">
          <option value="">- Select -</option>
          <option value="service" selected>Service Name</option>
          <option value="individual">User Name</option>
        </select>
      </form>
      <div id="activityChart" >
        <div class="chart-header">
          <div class="chart-subtitle">Service Name - Last 7 Days</div>
          <div class="chart-legend" aria-label="Legend"></div>
        </div>
        <div class="chart-container" id="weeklyChart" data-service-id="12345" style="width: 600px;"></div>
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
    require('../../app/assets/javascripts/activityChart.js');
    done();
  }, 100);
}, 10000); // Increased timeout to 10 seconds

test('D3 is loaded correctly', () => {
  // Check if D3 is loaded by verifying the existence of the d3 object
  expect(window.d3).toBeDefined();
  expect(typeof window.d3.version).toBe('string');
});

test('Populates the accessible table for activity chart correctly', () => {
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

  const firstRowCells = rows[1].getElementsByTagName('td');
  expect(firstRowCells[0].textContent).toBe('07/01/24');
  expect(firstRowCells[1].textContent).toBe('50');
  expect(firstRowCells[2].textContent).toBe('5');
});

test('SVG element is correctly set up', () => {
  window.createChart('#weeklyChart', ['07/01/24', '07/02/24', '07/03/24', '07/04/24', '07/05/24', '07/06/24', '07/07/24'], [50, 60, 70, 80, 90, 100, 110], [5, 2, 1, 0, 3, 4, 2]);

  const svg = document.getElementById('weeklyChart').querySelector('svg');
  expect(svg).not.toBeNull();
  expect(svg.getAttribute('width')).toBe('0');
  expect(svg.getAttribute('height')).toBe('400');
});

test('Check HTML content after chart creation', () => {
  // Create sample data for the chart
  const labels = ['07/01/24', '07/02/24', '07/03/24', '07/04/24', '07/05/24', '07/06/24', '07/07/24'];
  const deliveredData = [50, 60, 70, 80, 90, 100, 110];
  const failedData = [5, 2, 1, 0, 3, 4, 2];

  // Ensure the container has the correct width
  const container = document.getElementById('weeklyChart');
  container.style.width = '600px'; // Force a specific width
  const containerWidth = container.clientWidth;
  expect(containerWidth).toBeGreaterThan(0);

  // Call the function to create the chart
  window.createChart('#weeklyChart', labels, deliveredData, failedData);

  // Optionally, you can add assertions to check for specific elements
  expect(container.querySelector('svg')).not.toBeNull();
  expect(container.querySelectorAll('rect').length).toBeGreaterThan(0);
});
