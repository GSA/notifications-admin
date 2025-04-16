/**
 * @jest-environment jsdom
 */

describe('Main init script', () => {
    beforeEach(() => {
        // Clear DOM
        document.body.innerHTML = '';
        jest.resetModules();
        jest.clearAllMocks();
    });

    it('calls GOVUK.Frontend.initAll if available', () => {
        const initAllMock = jest.fn();
        const showHideInitMock = jest.fn();

        global.GOVUK = {
            Frontend: { initAll: initAllMock },
            ShowHideContent: jest.fn().mockImplementation(() => ({
            init: showHideInitMock
            }))
        };

        require('../../app/assets/javascripts/main.js');

        expect(initAllMock).toHaveBeenCalled();
    });

    it('initializes GOVUK.ShowHideContent', () => {
        const initMock = jest.fn();
        const ShowHideContentMock = jest.fn().mockImplementation(() => ({
            init: initMock
        }));
        global.GOVUK = {
            ShowHideContent: ShowHideContentMock
        };

        require('../../app/assets/javascripts/main.js');

        expect(ShowHideContentMock).toHaveBeenCalled();
        expect(initMock).toHaveBeenCalled();
    });

    it('focuses input next to error message inside label', () => {
        document.body.innerHTML = `
            <form>
            <label>
                <span class="error-message">Required</span>
            </label>
            <input id="name" />
            </form>
        `;
        const focusMock = jest.fn();
        const input = document.querySelector('input');
        input.focus = focusMock;

        require('../../app/assets/javascripts/main.js');

        // simulate DOMContentLoaded
        document.dispatchEvent(new Event('DOMContentLoaded'));

        expect(focusMock).toHaveBeenCalled();
    });

    it('adds border color on header click', () => {
        document.body.innerHTML = `
          <div class="govuk-header__container"></div>
        `;

        global.GOVUK = {
          ShowHideContent: jest.fn().mockImplementation(() => ({ init: jest.fn() })),
          Frontend: { initAll: jest.fn() }
        };

        require('../../app/assets/javascripts/main.js');
        document.dispatchEvent(new Event('DOMContentLoaded'));

        const header = document.querySelector('.govuk-header__container');
        header.click();

        expect(header.style.borderColor).toBe('#005ea5');
    });

    it('adds and removes class on parent during focusin and focusout', () => {
        document.body.innerHTML = `
        <div class="js-mark-focus-on-parent">
          <input type="text" />
        </div>
      `;

        global.GOVUK = {
            ShowHideContent: jest.fn().mockImplementation(() => ({ init: jest.fn() })),
            Frontend: { initAll: jest.fn() }
        };

        require('../../app/assets/javascripts/main.js');
        document.dispatchEvent(new Event('DOMContentLoaded'));

        const container = document.querySelector('.js-mark-focus-on-parent');
        const input = container.querySelector('input');

        input.dispatchEvent(new FocusEvent('focusin', { bubbles: true }));
        expect(container.classList.contains('js-child-has-focus')).toBe(true);

        input.dispatchEvent(new FocusEvent('focusout', { bubbles: true }));
        expect(container.classList.contains('js-child-has-focus')).toBe(false);
    });
});
