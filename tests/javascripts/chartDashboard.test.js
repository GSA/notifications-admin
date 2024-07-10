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
    <div id="chartContainer" data-sms-sent="100" data-sms-allowance-remaining="249900" style="width: 600px;">
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

test('Chart resizes correctly on window resize', done => {
  setTimeout(() => {
    const svg = document.getElementById('totalMessageChart');
    const chartContainer = document.getElementById('chartContainer');

    // Initial check
    expect(svg.getAttribute('width')).toBe(chartContainer.clientWidth.toString());

    // Set new container width
    chartContainer.style.width = '800px';

    // Trigger resize event
    window.dispatchEvent(new Event('resize'));

    setTimeout(() => {
      // Check if SVG width is updated
      expect(svg.getAttribute('width')).toBe(chartContainer.clientWidth.toString());
      done();
    }, 500); // Adjust the timeout if necessary
  }, 1000); // Initial wait for the chart to render
}, 10000); // Adjust the overall test timeout if necessary
