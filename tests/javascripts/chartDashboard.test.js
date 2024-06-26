beforeAll(done => {
  // Set up the DOM
  document.body.innerHTML = `
    <div id="chartContainer" data-sms-sent="100" data-sms-allowance-remaining="200" style="width: 600px;">
      <h1 id="chartTitle">Total Messages</h1>
      <canvas id="totalMessageChart"></canvas>
    </div>
    <div id="totalMessageTable"></div>
    <div id="message"></div>
  `;

  // Mock the global Chart constructor
  global.Chart = jest.fn().mockImplementation((context, config) => {
    return {
      data: config.data,
      options: config.options,
      resize: jest.fn(),
      update: jest.fn(),
    };
  });

  // Ensure instances array is reset for each test
  global.Chart.mock.instances = [];

  // Trigger the script
  require('../../app/assets/javascripts/chartDashboard.js');

  // Delay to ensure DOMContentLoaded and script execution
  setTimeout(done, 100);
});

test('Canvas element is correctly set up', () => {
  const canvas = document.getElementById('totalMessageChart');
  expect(canvas.width).toBe(canvas.parentElement.clientWidth);
  expect(canvas.height).toBe(100);
});

test('Populates the accessible table correctly', () => {
  const table = document.getElementById('totalMessageTable').getElementsByTagName('table')[0];
  expect(table).toBeDefined();

  const rows = table.getElementsByTagName('tr');
  expect(rows.length).toBe(3); // Header + 2 data rows

  const headers = rows[0].getElementsByTagName('th');
  expect(headers[0].textContent).toBe('Label');
  expect(headers[1].textContent).toBe('Value');

  const firstRowCells = rows[1].getElementsByTagName('td');
  expect(firstRowCells[0].textContent).toBe('Messages Sent');
  expect(firstRowCells[1].textContent).toBe('100');

  const secondRowCells = rows[2].getElementsByTagName('td');
  expect(secondRowCells[0].textContent).toBe('Remaining');
  expect(secondRowCells[1].textContent).toBe('200');
});

test('Chart title is correctly set', () => {
  const chartTitle = document.getElementById('chartTitle').textContent;
  expect(chartTitle).toBe('Total Messages');
});
