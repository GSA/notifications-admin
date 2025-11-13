const helpers = require('./support/helpers.js');

beforeAll(() => {
  jest.useFakeTimers();
});

afterAll(() => {
  require('./support/teardown.js');
});

describe('Prevent duplicate form submissions', () => {

  let form;
  let button;
  let formEventSpy;

  beforeEach(() => {

    // set up DOM
    document.body.innerHTML = `
      <form action="/" method="post">
        <button class="usa-button" type="submit">Continue</button>
      </form>`;

    form = document.querySelector('form');
    button = document.querySelector('button');

    // requires a helper due to JSDOM not implementing the submit method
    formEventSpy = helpers.spyOnFormSubmitEventPrevention(jest, form);

    require('../../app/assets/javascripts/preventDuplicateFormSubmissions.js');

  });

  afterEach(() => {

    document.body.innerHTML = '';

    // we run the previewPane.js script every test
    // the module cache needs resetting each time for the script to execute
    jest.resetModules();

    formEventSpy.mockClear();

  });

  test("It should prevent any clicks of the 'submit' button after the first one submitting the form", () => {

    helpers.triggerEvent(button, 'click');
    helpers.triggerEvent(button, 'click');

    expect(formEventSpy.mock.calls.length).toEqual(1);

  });

  test("It should allow clicks again after 1.5 seconds", () => {

    helpers.triggerEvent(button, 'click');

    jest.advanceTimersByTime(1600);

    helpers.triggerEvent(button, 'click');

    expect(formEventSpy.mock.calls.length).toEqual(0);

  });

  test("It should not error when form has no submit button", () => {

    document.body.innerHTML = `
      <form action="/" method="post">
        <input type="text" name="test">
      </form>`;

    form = document.querySelector('form');
    formEventSpy = helpers.spyOnFormSubmitEventPrevention(jest, form);

    jest.resetModules();
    require('../../app/assets/javascripts/preventDuplicateFormSubmissions.js');

    expect(() => {
      helpers.triggerEvent(form, 'submit');
    }).not.toThrow();

  });

  test("It should disable and add spinner to 'send' button", () => {

    document.body.innerHTML = `
      <form action="/" method="post">
        <button class="usa-button" type="submit" name="send">Send</button>
      </form>`;

    form = document.querySelector('form');
    button = document.querySelector('button');
    formEventSpy = helpers.spyOnFormSubmitEventPrevention(jest, form);

    jest.resetModules();
    require('../../app/assets/javascripts/preventDuplicateFormSubmissions.js');

    helpers.triggerEvent(button, 'click');

    jest.advanceTimersByTime(100);

    expect(button.disabled).toBe(true);
    expect(button.getAttribute('aria-busy')).toBe('true');
    expect(button.querySelector('.loading-spinner')).not.toBeNull();

  });

  test("It should disable and add spinner to 'schedule' button", () => {

    document.body.innerHTML = `
      <form action="/" method="post">
        <button class="usa-button" type="submit" name="schedule">Schedule</button>
      </form>`;

    form = document.querySelector('form');
    button = document.querySelector('button');
    formEventSpy = helpers.spyOnFormSubmitEventPrevention(jest, form);

    jest.resetModules();
    require('../../app/assets/javascripts/preventDuplicateFormSubmissions.js');

    helpers.triggerEvent(button, 'click');

    jest.advanceTimersByTime(100);

    expect(button.disabled).toBe(true);
    expect(button.getAttribute('aria-busy')).toBe('true');
    expect(button.querySelector('.loading-spinner')).not.toBeNull();

  });

  test("It should disable both send and cancel buttons when send is clicked", () => {

    document.body.innerHTML = `
      <form action="/" method="post">
        <button class="usa-button" type="submit" name="send">Send</button>
        <button class="usa-button" type="submit" name="cancel">Cancel</button>
      </form>`;

    form = document.querySelector('form');
    const sendButton = document.querySelector('button[name="send"]');
    const cancelButton = document.querySelector('button[name="cancel"]');
    formEventSpy = helpers.spyOnFormSubmitEventPrevention(jest, form);

    jest.resetModules();
    require('../../app/assets/javascripts/preventDuplicateFormSubmissions.js');

    helpers.triggerEvent(sendButton, 'click');

    jest.advanceTimersByTime(100);

    expect(sendButton.disabled).toBe(true);
    expect(cancelButton.disabled).toBe(true);

  });

  test("It should not add duplicate spinner if one already exists", () => {

    document.body.innerHTML = `
      <form action="/" method="post">
        <button class="usa-button" type="submit" name="send">Send<span class="loading-spinner"></span></button>
      </form>`;

    form = document.querySelector('form');
    button = document.querySelector('button');
    formEventSpy = helpers.spyOnFormSubmitEventPrevention(jest, form);

    jest.resetModules();
    require('../../app/assets/javascripts/preventDuplicateFormSubmissions.js');

    helpers.triggerEvent(button, 'click');

    jest.advanceTimersByTime(100);

    expect(button.querySelectorAll('.loading-spinner').length).toBe(1);

  });

  test("It should handle button with no name attribute", () => {

    document.body.innerHTML = `
      <form action="/" method="post">
        <button class="usa-button" type="submit">Submit</button>
      </form>`;

    form = document.querySelector('form');
    button = document.querySelector('button');
    formEventSpy = helpers.spyOnFormSubmitEventPrevention(jest, form);

    jest.resetModules();
    require('../../app/assets/javascripts/preventDuplicateFormSubmissions.js');

    expect(() => {
      helpers.triggerEvent(button, 'click');
      jest.advanceTimersByTime(1600);
    }).not.toThrow();

  });


});
