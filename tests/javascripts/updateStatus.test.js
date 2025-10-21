const each = require('jest-each').default;

const helpers = require('./support/helpers.js');

const serviceNumber = '6658542f-0cad-491f-bec8-ab8457700ead';
const updatesURL = `/services/${serviceNumber}/templates/count-sms-length`;

let responseObj = {};

beforeAll(() => {

  // ensure all timers go through Jest
  jest.useFakeTimers();

  // mock fetch
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(responseObj)
    })
  );

  require('../../app/assets/javascripts/updateStatus.js');

});

afterAll(() => {
  require('./support/teardown.js');
});

describe('Update content', () => {

  beforeEach(() => {

    document.body.innerHTML = `
      <form>
        <input type="hidden" name="csrf_token" value="abc123" />
        <label for="template_content" id="template-content-label">Template content<label>
        <span id="example-hint-text">Example hint text</span>
        <textarea name="template_content" id="template_content" aria-describedby="example-hint-text">Content of message</textarea>
      </form>
      <div data-module="update-status" data-updates-url="${updatesURL}" data-target="template_content">
        Initial content
      </div>
    `;

  });

  afterEach(() => {

    document.body.innerHTML = '';

    // tidy up record of mocked fetch calls
    fetch.mockClear();

    // ensure any timers set by continually starting the module are cleared
    jest.clearAllTimers();

  });

  test("It should add attributes to the elements", () => {

    window.NotifyModules.start();

    expect(
      document.querySelectorAll('[data-module=update-status]')[0].id
    ).toEqual(
      "update-status"
    );

    expect(
      document.getElementById('template_content').getAttribute('aria-describedby')
    ).toEqual(
      "example-hint-text update-status"
    );

  });

  test("It should handle a textarea without an aria-describedby attribute", () => {

    document.getElementById('template_content').removeAttribute('aria-describedby');

    window.NotifyModules.start();

    expect(
      document.getElementById('template_content').getAttribute('aria-describedby')
    ).toEqual(
      "update-status"
    );

  });

  test("It should make requests to the URL specified in the data-updates-url attribute", () => {

    window.NotifyModules.start();

    expect(fetch.mock.calls[0][0]).toEqual(updatesURL);
    expect(fetch.mock.calls[0][1]).toMatchObject({
      method: 'POST',
      credentials: 'same-origin',
      body: expect.any(FormData)
    });

    // Verify FormData contents
    const formData = fetch.mock.calls[0][1].body;
    expect(formData.get('csrf_token')).toBe('abc123');
    expect(formData.get('template_content')).toBe('Content of message');

  });

  test("It should replace the content of the div with the returned HTML", async () => {

    responseObj = {'html': 'Updated content'}

    expect(
      document.querySelectorAll('[data-module=update-status]')[0].textContent.trim()
    ).toEqual(
      "Initial content"
    );

    // Use real timers for async operations
    jest.useRealTimers();

    window.NotifyModules.start();

    // Wait for the promise chain to complete
    await new Promise(resolve => setTimeout(resolve, 0));

    expect(
      document.querySelectorAll('[data-module=update-status]')[0].textContent.trim()
    ).toEqual(
      "Updated content"
    );

    // Restore fake timers
    jest.useFakeTimers();

  });

  test("It should fire when the content of the textarea changes", () => {

    let textarea = document.getElementById('template_content');

    // Initial update triggered
    window.NotifyModules.start();
    expect(fetch.mock.calls.length).toEqual(1);

    // 150ms of inactivity
    jest.advanceTimersByTime(150);
    helpers.triggerEvent(textarea, 'input');

    expect(fetch.mock.calls.length).toEqual(2);

  });

  test("It should fire only after 150ms of inactivity", () => {

    let textarea = document.getElementById('template_content');

    // Initial update triggered
    window.NotifyModules.start();
    expect(fetch.mock.calls.length).toEqual(1);

    helpers.triggerEvent(textarea, 'input');
    jest.advanceTimersByTime(149);
    expect(fetch.mock.calls.length).toEqual(1);

    helpers.triggerEvent(textarea, 'input');
    jest.advanceTimersByTime(149);
    expect(fetch.mock.calls.length).toEqual(1);

    helpers.triggerEvent(textarea, 'input');
    jest.advanceTimersByTime(149);
    expect(fetch.mock.calls.length).toEqual(1);

    // > 150ms of inactivity
    jest.advanceTimersByTime(1);
    expect(fetch.mock.calls.length).toEqual(2);

  });

});
