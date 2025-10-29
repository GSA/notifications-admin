const helpers = require('./support/helpers');

afterAll(() => {

  require('./support/teardown.js');

  // clear up methods in the global space
  navigator.clipboard = undefined;

});

describe('copy to clipboard', () => {

  let apiKey = '00000000-0000-0000-0000-000000000000';
  let component;
  let clipboardWriteTextMock;

  const setUpDOM = function (options) {

    // set up DOM
    document.body.innerHTML =`
      <div data-module="copy-to-clipboard" data-value="${apiKey}" data-thing="${options.thing}" data-name="${options.name}"></div>`;

  };

  beforeEach(() => {

    // Reset the clipboard mock for each test
    if (clipboardWriteTextMock) {
      clipboardWriteTextMock.mockClear();
    }

    // mock sticky JS
    window.NotifyModules.stickAtBottomWhenScrolling = {
      recalculate: jest.fn(() => {})
    }

  });

  test("If Clipboard API isn't available, nothing should happen", () => {

    // Remove clipboard API
    navigator.clipboard = undefined;

    require('../../app/assets/javascripts/copyToClipboard.js');

    setUpDOM({ 'thing': 'Some Thing', 'name': 'Some Thing' });

    component = document.querySelector('[data-module=copy-to-clipboard]');

    // start the module
    window.NotifyModules.start();

    expect(component.querySelector('button')).toBeNull();

  });

  describe("If Clipboard API is available", () => {

    beforeAll(() => {

      // Mock modern Clipboard API BEFORE loading the module
      clipboardWriteTextMock = jest.fn(() => Promise.resolve());
      navigator.clipboard = {
        writeText: clipboardWriteTextMock
      };

      // force module require to not come from cache
      jest.resetModules();

      require('../../app/assets/javascripts/copyToClipboard.js');

    });

    describe("On page load", () => {

      describe("For all variations of the initial HTML", () => {

        beforeEach(() => {

          setUpDOM({ 'thing': 'Some Thing', 'name': 'Some Thing' });

          component = document.querySelector('[data-module=copy-to-clipboard]');

          // start the module
          window.NotifyModules.start();

        });

        test("It should add a button for copying the thing to the clipboard", () => {

          expect(component.querySelector('button')).not.toBeNull();
          expect(component.querySelector('button').textContent.trim()).toContain('Copy Some Thing');

        });

        test("It should add the 'copy-to-clipboard' class", () => {

          expect(component.classList.contains('copy-to-clipboard')).toBe(true);

        });


        test("It should display the value", () => {

          expect(component.querySelector('.copy-to-clipboard__value')).not.toBeNull();
          expect(component.querySelector('.copy-to-clipboard__value').textContent).toBe(apiKey);

        });

        test("It should have an aria-live region for screen reader announcements", () => {

          const liveRegion = component.querySelector('[aria-live]');
          expect(liveRegion).not.toBeNull();
          expect(liveRegion.getAttribute('aria-live')).toBe('polite');
          expect(liveRegion.getAttribute('aria-atomic')).toBe('true');

        });

      });

      describe("If it's one of many in the page", () => {

        beforeEach(() => {

          setUpDOM({ 'thing': 'ID', 'name': 'Default' });

          component = document.querySelector('[data-module=copy-to-clipboard]');

          // start the module
          window.NotifyModules.start();

        });

        test("the button should have shorter label and hidden suffix", () => {

          const button = component.querySelector('button');
          expect(button.textContent).toContain('Copy ID');

          const buttonSuffix = button.querySelector('.usa-sr-only');
          expect(buttonSuffix).not.toBeNull();
          expect(buttonSuffix.textContent).toEqual(' for Default');

        });

      });

      describe("If it's the only one on the page", () => {

        beforeEach(() => {

          setUpDOM({ 'thing': 'Some Thing', 'name': 'Some Thing' });

          component = document.querySelector('[data-module=copy-to-clipboard]');

          // start the module
          window.NotifyModules.start();

        });

        test("the button should have full label without extra suffix", () => {

          const button = component.querySelector('button');
          expect(button.textContent).toContain('Copy Some Thing to clipboard');
          expect(button.textContent).not.toContain(' for ');

        })

      });

    });

    describe("If you click the 'Copy' button", () => {

      beforeEach(async () => {

        jest.useFakeTimers();

        setUpDOM({ 'thing': 'API key', 'name': 'API key' });

        component = document.querySelector('[data-module=copy-to-clipboard]');

        // start the module
        window.NotifyModules.start();

        const button = component.querySelector('button');
        helpers.triggerEvent(button, 'click');

        // Wait for async clipboard operation
        await Promise.resolve();

      });

      afterEach(() => {
        jest.useRealTimers();
      });

      test("The value should still be visible", () => {

        expect(component.querySelector('.copy-to-clipboard__value')).not.toBeNull();
        expect(component.querySelector('.copy-to-clipboard__value').textContent).toBe(apiKey);

      });

      test("The button text should change to 'Copied!'", () => {

        const button = component.querySelector('button');
        expect(button.textContent).toContain('Copied!');

      });

      test("The button should be disabled", () => {

        const button = component.querySelector('button');
        expect(button.disabled).toBe(true);

      });

      test("Screen reader announcement should confirm the copy", () => {

        const liveRegion = component.querySelector('[aria-live]');
        expect(liveRegion.textContent).toBe('API key copied to clipboard');

      });

      test("It should copy the value to clipboard using Clipboard API", () => {

        expect(clipboardWriteTextMock).toHaveBeenCalledWith(apiKey);

      });

      test("After 2 seconds, button should reset to original text", () => {

        const button = component.querySelector('button');

        jest.advanceTimersByTime(2000);

        expect(button.textContent).toContain('Copy API key');
        expect(button.textContent).not.toContain('Copied!');
        expect(button.disabled).toBe(false);

      });

      test("After 2 seconds, screen reader announcement should clear", () => {

        const liveRegion = component.querySelector('[aria-live]');

        jest.advanceTimersByTime(2000);

        expect(liveRegion.textContent).toBe('');

      });

    });

  });

});
