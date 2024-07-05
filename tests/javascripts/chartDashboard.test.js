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

// beforeAll hook to set up the DOM and load D3.js script
beforeAll(done => {
  // Set up the DOM with the D3 script included
  document.body.innerHTML = `
    <div id="chartContainer" data-sms-sent="100" data-sms-allowance-remaining="200" style="width: 600px;">
      <h1 id="chartTitle">Total Messages</h1>
      <svg id="totalMessageChart"></svg>
    </div>
    <div id="totalMessageTable"></div>
    <div id="message"></div>
    <div class="tooltip hidden"></div>
  `;

  // Load the D3 script dynamically
  loadScript(d3ScriptContent);

  // Wait a bit to ensure the script is executed
  setTimeout(() => {
    // Require the actual JavaScript file you are testing
    require('../../app/assets/javascripts/chartDashboard.js');
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
  expect(svg.getAttribute('width')).toBe(svg.parentElement.clientWidth.toString());
  expect(svg.getAttribute('height')).toBe('64');
});

// Test to check if the table is created and populated correctly
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
  expect(secondRowCells[1].textContent).toBe('249,900');
});

// Test to check if the chart title is correctly set
test('Chart title is correctly set', () => {
  const chartTitle = document.getElementById('chartTitle').textContent;
  expect(chartTitle).toBe('Total Messages');
});

// Test to mimic the tooltip functionality
test('Tooltip displays correct content on mouseover', done => {
  setTimeout(() => {
    const svg = document.getElementById('totalMessageChart');
    const tooltip = document.querySelector('.tooltip');
    const rect = svg.querySelector('rect');

    // Simulate mouseover event on the first rect
    const event = new MouseEvent('mousemove', {
      bubbles: true,
      cancelable: true,
      view: window,
      clientX: 100, // Example x-coordinate
      clientY: 50   // Example y-coordinate
    });

    rect.dispatchEvent(event);

    // Check if the tooltip is displayed and has correct content
    expect(tooltip.classList.contains('hidden')).toBe(false);
    expect(tooltip.innerHTML).toBe('Messages Sent: 100');

    done();
  }, 1000); // Adjust the timeout if necessary
}, 10000); // Adjust the overall test timeout if necessary

// Test to mimic the tooltip functionality on mouseout
test('Tooltip hides on mouseout', done => {
  setTimeout(() => {
    const svg = document.getElementById('totalMessageChart');
    const tooltip = document.querySelector('.tooltip');
    const rect = svg.querySelector('rect');

    // Simulate mouseover event on the first rect to show the tooltip
    const mouseoverEvent = new MouseEvent('mousemove', {
      bubbles: true,
      cancelable: true,
      view: window,
      clientX: 100, // Example x-coordinate
      clientY: 50   // Example y-coordinate
    });

    rect.dispatchEvent(mouseoverEvent);

    // Simulate mouseout event on the first rect to hide the tooltip
    const mouseoutEvent = new MouseEvent('mouseout', {
      bubbles: true,
      cancelable: true,
      view: window
    });

    rect.dispatchEvent(mouseoutEvent);

    // Check if the tooltip is hidden
    setTimeout(() => {
      expect(tooltip.classList.contains('hidden')).toBe(true);
      done();
    }, 500); // Adjust the timeout if necessary
  }, 1000); // Initial wait for the chart to render
}, 10000); // Adjust the overall test timeout if necessary
