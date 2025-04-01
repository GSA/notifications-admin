const helpers = require('./support/helpers.js');

const { announceUploadStatusFromElement } = require('../../app/assets/javascripts/fileUpload.js');

afterAll(() => {
  require('./support/teardown.js');
});


describe('File upload', () => {

  let form;
  let fileUpload;

  beforeEach(() => {

    // set up DOM
    document.body.innerHTML = `
      <form method="post" enctype="multipart/form-data" class="" data-module="file-upload">
        <label class="file-upload-label" for="file">
          <span class="visually-hidden">Upload a PNG logo</span>
        </label>
        <input class="file-upload-field" id="file" name="file" type="file">
        <label class="file-upload-button" for="file">
          Upload logo
        </label>
        <label class="file-upload-filename" for="file"></label>
        <button type="submit" class="govuk-button file-upload-submit">Submit</button>
      </form>`;

    form = document.querySelector('form');
    uploadControl = form.querySelector('input[type=file]');

  });

  afterEach(() => {

    document.body.innerHTML = '';

  });

  test("If the page loads, from a new or existing navigation, the form should reset", () => {

    form.reset = jest.fn(() => {});

    // start module
    window.GOVUK.modules.start();

    helpers.triggerEvent(window, 'pageshow');

    expect(form.reset).toHaveBeenCalled();

  });

  describe("If the state of the upload form control changes", () => {

    beforeEach(() => {

      form.submit = jest.fn(() => {});

      // start module
      window.GOVUK.modules.start();

      helpers.triggerEvent(uploadControl, 'change', { eventInit: { bubbles: true } });

    });

    test("The form should submit", () => {

      expect(form.submit).toHaveBeenCalled();

    });

    test("It should display a disabled Uploading button", () => {
      const uploadingButton = form.querySelector("button.uploading-button");
      expect(uploadingButton).not.toBeNull();
      expect(uploadingButton.textContent).toMatch(/Uploading/);
      expect(uploadingButton.getAttribute('aria-disabled')).toBe("true");
    });

  });

});

describe('File upload "upload-trigger" click handler', () => {
  let form;

  beforeEach(() => {
    document.body.innerHTML = `
      <form method="post" enctype="multipart/form-data" data-module="file-upload">
        <button type="button" data-module="upload-trigger" data-file-input-id="test-file-input">Upload your file</button>
        <input type="file" id="test-file-input" style="display:none;">
      </form>
    `;

    form = document.querySelector('form');

    // Register the module
    window.GOVUK.modules.start();
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  test('clicking upload trigger simulates file input click', () => {
    const uploadButton = form.querySelector('[data-module="upload-trigger"]');
    const fileInput = document.getElementById('test-file-input');

    // Spy on fileInput.click
    const clickSpy = jest.spyOn(fileInput, 'click').mockImplementation(() => {});

    // Trigger the click
    helpers.triggerEvent(uploadButton, 'click');

    expect(clickSpy).toHaveBeenCalled();

    clickSpy.mockRestore();
  });
});

describe('announceUploadStatusFromElement', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    document.body.innerHTML = `
      <div id="upload-status-live" aria-live="assertive" role="status" class="usa-sr-only"></div>
    `;
  });

  afterEach(() => {
    jest.useRealTimers();
    document.body.innerHTML = '';
  });

  test('announces error message from #upload-error', () => {
    document.body.innerHTML += `
      <span id="upload-error" class="usa-sr-only">File upload failed</span>
    `;

    const srRegion = document.getElementById('upload-status-live');

    // Call the function
    announceUploadStatusFromElement();

    // Confirm it clears first
    expect(srRegion.textContent).toBe('');

    // Fast-forward the timer
    jest.advanceTimersByTime(50);

    // Confirm it updates after delay
    expect(srRegion.textContent).toBe('File upload failed');
  });

  test('announces success message from #upload-success if no error is present', () => {
    document.body.innerHTML += `
      <span id="upload-success" class="usa-sr-only">File upload successful</span>
    `;

    const srRegion = document.getElementById('upload-status-live');

    announceUploadStatusFromElement();

    expect(srRegion.textContent).toBe('');

    jest.advanceTimersByTime(50);

    expect(srRegion.textContent).toBe('File upload successful');
  });

  test('does nothing if neither success nor error is present', () => {
    const srRegion = document.getElementById('upload-status-live');

    srRegion.textContent = 'Old message';

    announceUploadStatusFromElement();

    // Should not clear or update if no message element is found
    expect(srRegion.textContent).toBe('Old message');

    jest.advanceTimersByTime(50);

    // Still unchanged
    expect(srRegion.textContent).toBe('Old message');
  });
});
