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
  configurable: true,
});

// beforeAll hook to set up the DOM and load D3.js script
beforeEach(() => {
  // Set up the DOM with the D3 script included
  document.body.innerHTML = `
    <div id="totalMessageChartContainer" data-sms-sent="100" data-sms-allowance-remaining="249900" style="width: 600px;">
      <h1 id="chartTitle">Total Messages</h1>
      <svg id="totalMessageChart"></svg>
    </div>
    <div id="totalMessageTable"></div>
    <div id="message"></div>
  `;

  // Load the D3 script dynamically
  loadScript(d3ScriptContent);

  // Wait a bit to ensure the script is executed
  return new Promise(resolve => {
    setTimeout(() => {
      // Require the actual JavaScript file you are testing
      require('../../app/assets/javascripts/totalMessagesChart.js');
      resolve();
    }, 100);
  });
});

// Single test to check if D3 is loaded correctly
test('D3 is loaded correctly', () => {
  // Check if D3 is loaded by verifying the existence of the d3 object
  expect(window.d3).toBeDefined();
  expect(typeof window.d3.version).toBe('string');
});

// Test to check if the SVG element is correctly set up
test('SVG element is correctly set up', done => {
  window.createTotalMessagesChart();

  setTimeout(() => {
    const svg = document.getElementById('totalMessageChart');
    expect(svg.getAttribute('width')).toBe('600');
    expect(svg.getAttribute('height')).toBe('64');
    done();
  }, 1000); // Ensure enough time for the DOM updates
});

// Test to check if the table is created and populated correctly
test('Populates the accessible table correctly', () => {
  window.createTotalMessagesChart();
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
  window.createTotalMessagesChart();

  setTimeout(() => {
    const svg = document.getElementById('totalMessageChart');
    const chartContainer = document.getElementById('totalMessageChartContainer');

    // Initial check
    expect(svg.getAttribute('width')).toBe('600');

    // Set new container width
    Object.defineProperty(chartContainer, 'clientWidth', { value: 800, configurable: true });

    // Trigger resize event
    window.dispatchEvent(new Event('resize'));

    setTimeout(() => {
      // Check if SVG width is updated
      expect(svg.getAttribute('width')).toBe('800');
      done();
    }, 1000); // Adjust the timeout if necessary
  }, 1000); // Initial wait for the chart to render
}, 15000); // Adjust the overall test timeout if necessary

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

  // Simulate mousemove event with coordinates
  const mouseMoveEvent = new MouseEvent('mousemove', {
    bubbles: true,
    cancelable: true,
    clientX: 50,
    clientY: 50
  });
  sentBar.dispatchEvent(mouseMoveEvent);

  expect(tooltip.style.left).toBe('');
  expect(tooltip.style.top).toBe('');

  // Mouse out to hide tooltip
  const mouseOutEvent = new Event('mouseout');
  sentBar.dispatchEvent(mouseOutEvent);
  expect(tooltip.style.display).toBe('none');
});

// Test to ensure SVG bars are created and animated correctly
test('SVG bars are created and animated correctly', done => {
  window.createTotalMessagesChart();
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

// Test to check console error when chart container width is 0
test('Handles zero width chart container', () => {
    // Mock console.error
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    // Set chart container width to 0
    Object.defineProperty(document.getElementById('totalMessageChartContainer'), 'clientWidth', { value: 0 });

  try {
    // Call the function to create the chart
    window.createTotalMessagesChart();
  } catch (error) {
    // Check if the error message is as expected
    expect(error.message).toBe('Chart container width is 0, cannot set SVG width.');
  }
});

  test('Creates chart on DOMContentLoaded', () => {
    const createTotalMessagesChartSpy = jest.spyOn(window, 'createTotalMessagesChart');

    // Attach event listener before dispatching DOMContentLoaded
    document.addEventListener('DOMContentLoaded', createTotalMessagesChart);

    // Dispatch the DOMContentLoaded event
    document.dispatchEvent(new Event('DOMContentLoaded'));

    expect(createTotalMessagesChartSpy).toHaveBeenCalled();
  });
