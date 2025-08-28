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
beforeAll(() => {
  jest.spyOn(Intl, 'DateTimeFormat').mockImplementation(() => ({
    resolvedOptions: () => ({ timeZone: 'UTC' })
  }));
});

beforeAll(done => {
  // Set up the DOM with the D3 script included
  document.body.innerHTML = `
    <div id="activityChartContainer">
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
          <div class="chart-subtitle">Service Name - last 8 days</div>
          <div class="chart-legend" role="region" aria-label="Legend"></div>
        </div>
        <div class="chart-container" id="weeklyChart" data-service-id="12345" style="width: 600px;"></div>
        <table id="weeklyTable" class="usa-sr-only usa-table"></table>
      </div>
    </div>
    <div id="aria-live-account" class="usa-sr-only" aria-live="polite"></div>
    <div id="activityContainer" data-currentUserName="Test User" data-currentServiceId="12345"></div>

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
    '2024-07-01': { sms: { delivered: 50, failed: 5, pending: 10 } },
    '2024-07-02': { sms: { delivered: 60, failed: 2, pending: 5 } },
    '2024-07-03': { sms: { delivered: 70, failed: 1, pending: 3 } },
    '2024-07-04': { sms: { delivered: 80, failed: 0, pending: 0 } },
    '2024-07-05': { sms: { delivered: 90, failed: 3, pending: 8 } },
    '2024-07-06': { sms: { delivered: 100, failed: 4, pending: 7 } },
    '2024-07-07': { sms: { delivered: 110, failed: 2, pending: 6 } },
  };

  const labels = Object.keys(sampleData).map(dateString => {
    const dateParts = dateString.split('-');
    return `${dateParts[1]}/${dateParts[2]}/${dateParts[0].slice(2)}`; // Format to MM/DD/YY
  });
  const deliveredData = Object.values(sampleData).map(d => d.sms.delivered);
  const failedData = Object.values(sampleData).map(d => d.sms.failed);
  const pendingData = Object.values(sampleData).map(d => d.sms.pending);

  window.createTable('weeklyTable', 'activityChart', labels, deliveredData, failedData, pendingData);

  const table = document.getElementById('weeklyTable');
  expect(table).toBeDefined();

  const rows = table.getElementsByTagName('tr');
  expect(rows.length).toBe(8); // Header + 7 data rows

  const headers = rows[0].getElementsByTagName('th');
  expect(headers[0].textContent).toBe('Day');
  expect(headers[1].textContent).toBe('Delivered');
  expect(headers[2].textContent).toBe('Failed');
  expect(headers[3].textContent).toBe('Pending');

  const firstRowCells = rows[1].getElementsByTagName('td');
  expect(firstRowCells[0].textContent).toBe('07/01/24');
  expect(firstRowCells[1].textContent).toBe('50');
  expect(firstRowCells[2].textContent).toBe('5');
});

test('SVG element is correctly set up', () => {
  window.createChart(
    '#weeklyChart',
    ['07/01/24', '07/02/24', '07/03/24', '07/04/24', '07/05/24', '07/06/24', '07/07/24'],
    [50, 60, 70, 80, 90, 100, 110],
    [5, 2, 1, 0, 3, 4, 2],
    [10, 5, 3, 0, 8, 7, 6]
  );

  const svg = document.getElementById('weeklyChart').querySelector('svg');
  expect(svg).not.toBeNull();
  expect(svg.querySelectorAll('.bar-group').length).toBe(3);
});

test('Check HTML content after chart creation', () => {
  const labels = ['07/01/24', '07/02/24', '07/03/24', '07/04/24', '07/05/24', '07/06/24', '07/07/24'];
  const deliveredData = [50, 60, 70, 80, 90, 100, 110];
  const failedData = [5, 2, 1, 0, 3, 4, 2];
  const pendingData = [10, 5, 8, 3, 6, 7, 4];

  const container = document.getElementById('weeklyChart');
  container.style.width = '600px';
  const containerWidth = container.clientWidth;
  expect(containerWidth).toBeGreaterThan(0);

  window.createChart('#weeklyChart', labels, deliveredData, failedData, pendingData);

  const svg = container.querySelector('svg');
  expect(svg).not.toBeNull();

  const bars = container.querySelectorAll('rect');
  expect(bars.length).toBeGreaterThan(0);

  const barGroups = svg.querySelectorAll('.bar-group');
  expect(barGroups.length).toBe(3);

  const pendingBars = Array.from(bars).filter(bar =>
    bar.parentNode.getAttribute('fill') === '#C7CACE'
  );
  expect(pendingBars.length).toBe(labels.length);
});

test('Legend includes pending when data exists', () => {
  const labels = ['Day 1', 'Day 2'];
  const deliveredData = [10, 20];
  const failedData = [5, 0];
  const pendingData = [3, 2];

  window.createChart('#weeklyChart', labels, deliveredData, failedData, pendingData);

  const legendContainer = document.querySelector('.chart-legend');
  const legendItems = legendContainer.querySelectorAll('.legend-item');
  expect(legendItems.length).toBe(3);

  const pendingLegend = Array.from(legendItems).find(item =>
    item.textContent.includes('Pending')
  );
  expect(pendingLegend).not.toBeNull();
});

test('Legend is hidden when there are no delivered, failed, or pending messages', () => {
  const labels = ['Day 1', 'Day 2'];
  const deliveredData = [0, 0];
  const failedData = [0, 0];
  const pendingData = [0, 0];

  // Call the createChart function
  window.createChart('#weeklyChart', labels, deliveredData, failedData, pendingData);

  // Check if the legend is hidden using computed style
  const legendContainer = document.querySelector('.chart-legend');
  const legendDisplayStyle = window.getComputedStyle(legendContainer).display;
  expect(legendDisplayStyle).toBe('none');
});

test('Fetches data and creates chart and table correctly', async () => {
  const mockResponse = {
    '2024-07-01': { sms: { delivered: 50, failed: 5, pending: 10 } },
    '2024-07-02': { sms: { delivered: 60, failed: 2, pending: 8 } },
    '2024-07-03': { sms: { delivered: 70, failed: 1, pending: 6 } },
    '2024-07-04': { sms: { delivered: 80, failed: 0, pending: 4 } },
    '2024-07-05': { sms: { delivered: 90, failed: 3, pending: 7 } },
    '2024-07-06': { sms: { delivered: 100, failed: 4, pending: 5 } },
    '2024-07-07': { sms: { delivered: 110, failed: 2, pending: 3 } },
  };
  const tableContainer = document.getElementById('activityContainer');
  const currentServiceId = tableContainer.getAttribute('data-currentServiceId');


  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    })
  );

  const data = await fetchData('service');

  expect(global.fetch).toHaveBeenCalledWith(`/services/${currentServiceId}/daily-stats.json?timezone=UTC`);
  expect(data).toEqual(mockResponse);

  const labels = Object.keys(mockResponse).map(dateString => {
    const dateParts = dateString.split('-');
    return `${dateParts[1]}/${dateParts[2]}/${dateParts[0].slice(2)}`;
  });
  const deliveredData = Object.values(mockResponse).map(d => d.sms.delivered);
  const failedData = Object.values(mockResponse).map(d => d.sms.failed);
  const pendingData = Object.values(mockResponse).map(d => d.sms.pending);

  window.createChart('#weeklyChart', labels, deliveredData, failedData, pendingData);
  window.createTable('weeklyTable', 'activityChart', labels, deliveredData, failedData, pendingData);

  const chart = document.getElementById('weeklyChart').querySelector('svg');
  expect(chart).not.toBeNull();

  const table = document.getElementById('weeklyTable');
  expect(table).toBeDefined();
  const rows = table.getElementsByTagName('tr');
  expect(rows.length).toBe(8);
});

test('handleDropdownChange updates DOM for individual selection', () => {
  document.body.innerHTML = `
    <div id="activityChartContainer">
      <div class="chart-subtitle"></div>
    </div>
    <div id="aria-live-account"></div>
    <div id="activityContainer" data-currentUserName="Test User" data-currentServiceId="12345"></div>
    <div id="tableActivity">
      <h2 id="table-heading"></h2>
      <table id="activity-table">
        <caption id="caption"></caption>
        <thead>
          <tr>
            <th data-column="sender">Sender</th>
          </tr>
        </thead>
        <tbody>
          <tr><td data-sender="Test User">Test User</td></tr>
          <tr><td data-sender="Other User">Other User</td></tr>
          <tr><td data-sender="Test User">Test User</td></tr>
          <tr><td data-sender="Test User">Test User</td></tr>
          <tr><td data-sender="Other User">Other User</td></tr>
          <tr><td data-sender="Test User">Test User</td></tr>
          <tr><td data-sender="Test User">Test User</td></tr>
        </tbody>
      </table>
    </div>
    <select id="options">
      <option value="service">Service</option>
      <option value="individual">Individual</option>
    </select>
  `;

  window.currentUserName = "Test User";

  jest.spyOn(window, 'fetchData').mockImplementation(() => {});

  const selectElement = document.getElementById('options');
  selectElement.value = 'individual';
  const event = { target: selectElement };

  window.handleDropdownChange(event);

  expect(document.getElementById('table-heading').textContent).toBe('My activity');
  expect(document.getElementById('caption').textContent).toContain('Test User');

  const senderHeader = document.querySelector('[data-column="sender"]');
  expect(senderHeader.style.display).toBe('none');

  document.querySelectorAll('[data-sender]').forEach(cell => {
    expect(cell.style.display).toBe('none');
  });

  const rows = Array.from(document.querySelectorAll('#activity-table tbody tr'));
  const visibleRows = rows.filter(row => row.style.display !== 'none');
  expect(visibleRows.length).toBeLessThanOrEqual(5);
  visibleRows.forEach(row => {
    const sender = row.querySelector('[data-sender]').dataset.sender;
    expect(sender).toBe('Test User');
  });

  window.fetchData.mockRestore();
});

test('handleDropdownChange shows empty message when user has no jobs', () => {
  document.body.innerHTML = `
    <div id="activityChartContainer">
      <div class="chart-subtitle"></div>
    </div>
    <div id="aria-live-account"></div>
    <div id="activityContainer" data-currentUserName="Test User" data-currentServiceId="12345"></div>
    <div id="tableActivity">
      <h2 id="table-heading"></h2>
      <table id="activity-table">
        <caption id="caption"></caption>
        <thead>
          <tr>
            <th data-column="sender">Sender</th>
          </tr>
        </thead>
        <tbody>
          <tr><td data-sender="Other User">Other User</td></tr>
          <tr><td data-sender="Another User">Another User</td></tr>
          <tr><td data-sender="Different User">Different User</td></tr>
          <tr class="table-row">
            <td class="table-empty-message" colspan="10">No batched job messages found (messages are kept for 8 days).</td>
          </tr>
        </tbody>
      </table>
    </div>
    <select id="options">
      <option value="service">Service</option>
      <option value="individual">Individual</option>
    </select>
  `;

  window.currentUserName = "Test User";

  jest.spyOn(window, 'fetchData').mockImplementation(() => {});

  const selectElement = document.getElementById('options');
  selectElement.value = 'individual';
  const event = { target: selectElement };

  window.handleDropdownChange(event);

  expect(document.getElementById('table-heading').textContent).toBe('My activity');
  expect(document.getElementById('caption').textContent).toContain('Test User');

  const senderHeader = document.querySelector('[data-column="sender"]');
  expect(senderHeader.style.display).toBe('none');

  document.querySelectorAll('[data-sender]').forEach(cell => {
    expect(cell.style.display).toBe('none');
  });

  const emptyMessageRow = document.querySelector('.table-empty-message').closest('tr');
  expect(emptyMessageRow.style.display).toBe('');

  const allRows = Array.from(document.querySelectorAll('#activity-table tbody tr'));
  const visibleRows = allRows.filter(row => row.style.display !== 'none');
  expect(visibleRows.length).toBe(1);
  expect(visibleRows[0].querySelector('.table-empty-message')).not.toBeNull();

  window.fetchData.mockRestore();
});
