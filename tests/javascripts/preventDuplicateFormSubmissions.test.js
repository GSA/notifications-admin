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
        <button class="govuk-button" type="submit">Continue</button>
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

    jest.advanceTimersByTime(1500);

    helpers.triggerEvent(button, 'click');

    expect(formEventSpy.mock.calls.length).toEqual(0);

  });

});
