// This will use the real function and listener
const {
  initUploadStatusAnnouncer
} = require('../../app/assets/javascripts/fileUpload.js');

jest.useFakeTimers();

test('writes upload message to the live region on DOMContentLoaded', () => {
  // Setup the DOM
  document.body.innerHTML = `
    <div id="upload-status-live" aria-live="assertive" role="status" class="usa-sr-only">Old message</div>
    <span id="upload-success" class="usa-sr-only">File upload successful</span>
  `;

  // Register the listener (same as page load does)
  initUploadStatusAnnouncer();

  // Simulate the page load event
  document.dispatchEvent(new Event('DOMContentLoaded'));

  // Live region will be cleared first, then updated
  jest.advanceTimersByTime(50);

  const srRegion = document.getElementById('upload-status-live');
  expect(srRegion.textContent).toBe('File upload successful');
});
