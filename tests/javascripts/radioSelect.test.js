const helpers = require('./support/helpers');

beforeAll(() => {
  window.Hogan = require('hogan.js');
  require('../../app/assets/javascripts/radioSelect.js');
});

afterAll(() => {
  require('./support/teardown.js');
});

describe('RadioSelect', () => {
  const CATEGORIES = [
    'Later today',
    'Tomorrow',
    'Friday',
    'Saturday'
  ];
  const HOURS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24];
  let originalOptionsForAllCategories;

  const getDataFromOption = (option) => {
    return {
              value: option.querySelector('input').getAttribute('value'),
              label: option.querySelector('label').textContent.trim()
           };
  };

  const clickButtonForCategory = (category) => {

    // click the button for this category
    const categoryButton = document.querySelector(`.radio-select__column:nth-child(2) input[value="${category}"]`);
    helpers.triggerEvent(categoryButton, 'click');

  };

  beforeEach(() => {
    const options = () => {
      let result = '';

      const getHourLabel = (hour) => {
        let label = hour;

        if (hour === 12) {
          return 'noon';
        }

        if (hour === 24) {
          return 'midnight';
        }

        return `${hour}${hour > 12 ? 'am' : 'pm'}`;
      };

      const hours = (day, start) => {
        let result = '';
        let hours = HOURS;
        let dayAsNumber = {
          'Later today': 22,
          'Tomorrow': 23,
          'Friday': 24,
          'Saturday': 25
        }[day];

        if (start !== undefined) {
          hours = hours.slice(start - 1);
        }

        hours.forEach((hour, idx) => {
          const hourLabel = getHourLabel(hour);
          const num = idx + 1;

          result +=
            `<div class="govuk-radios__item">
              <input class="govuk-radios__input" id="scheduled_for-${num}" name="scheduled_for" type="radio" value="2019-05-${dayAsNumber}T${hour}:00:00.459156">
              <label class="govuk-label govuk-radios__label" for="scheduled_for-${num}">
                ${day} at ${hourLabel}
              </label>
            </div>`;
        });

        return result;
      };

      CATEGORIES.forEach((day, idx) => {
        if (idx === 0) {
          result += hours(day, 11);
        } else {
          result += hours(day);
        }

        return result;
      });

      return result;
    };

    document.body.innerHTML = `
      <fieldset>
        <legend class="form-label">
          When should Notify send these messages?
        </legend>
        <div class="radio-select" data-module="radio-select" data-categories="${CATEGORIES.join(',')}" data-show-now-as-default="true">
          <div class="govuk-radios__item">
            <input class="govuk-radios__input" checked="" id="scheduled_for-0" name="scheduled_for" type="radio" value="">
            <label class="govuk-label govuk-radios__label" for="scheduled_for-0">
              Now
            </label>
          </div>
          ${options()}
        </div>
      </fieldset>`;

      originalOptionsForAllCategories = Array.from(document.querySelectorAll('.govuk-radios__item:not(:first-of-type)'))
                                          .map(option => getDataFromOption(option));
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  describe("when the page has loaded", () => {

    describe("if the 'data-show-now-as-default' attribute", () => {

      test("is set to true the module should have a 'Now' option", () => {

        // default is for it to be set to true

        // start module
        window.GOVUK.modules.start();

        expect(document.querySelectorAll('.radio-select__column').length).toEqual(2);

      });

      test("is set to false the module should not have a 'Now' option", () => {

        document.querySelector('.radio-select').setAttribute('data-show-now-as-default', 'false');

        // start module
        window.GOVUK.modules.start();

        expect(document.querySelectorAll('.radio-select__column').length).toEqual(1);

      });

    });

    describe("it should have a button for each category", () => {

      let categoryButtons;

      beforeEach(() => {

        // start module
        window.GOVUK.modules.start();

        categoryButtons = document.querySelectorAll('.radio-select__column:nth-child(2) .radio-select__button--category');

      });

      test("the number of buttons should match the categories", () => {

        expect(categoryButtons.length).toBe(CATEGORIES.length);

      });

      test("each button's text should match their category", () => {

        // check the buttons have the right text
        CATEGORIES.forEach((category, idx) => {
          expect(categoryButtons[idx].getAttribute('value')).toEqual(category);
        });

      });

      test("each button's semantics should show it controls another region and that region is collapsed", () => {

        categoryButtons.forEach(btn => {
          expect(btn.getAttribute('aria-expanded')).toEqual('false');
        });

      });

    });

  });

  describe("category buttons", () => {

    CATEGORIES.forEach((category, idx) => {

      describe(`clicking the button for ${category} should`, () => {

        const categoryRegExp = new RegExp('^' + category);
        let originalOptionsForcategory;

        beforeEach(() => {

          // get all the options in the original page for this category
          originalOptionsForCategory = originalOptionsForAllCategories.filter(option => categoryRegExp.test(option.label));

          // start module
          window.GOVUK.modules.start();

          clickButtonForCategory(category);

        });

        test("show the options for it, with the right label and value", () => {

          // check options this reveals against those originally in the page for this category
          const options = document.querySelectorAll('.radio-select__column:nth-child(2) .govuk-radios__item');

          const optionsThatMatchOriginals = Array.from(options).filter((option, idx) => {
            const optionData = getDataFromOption(option);
            const originalOption = originalOptionsForCategory[idx];

            return optionData.value === originalOption.value && optionData.label === originalOption.label;
          });

          expect(optionsThatMatchOriginals.length).toEqual(originalOptionsForCategory.length);

        });

        test("focus the first time slot", () => {

          expect(document.activeElement).toBe(document.getElementById('scheduled_for-1'));

        });

      });

    });

    test(`clicking the button for a category should add a 'Done' button below its options`, () => {

      // start module
      window.GOVUK.modules.start();

      clickButtonForCategory(CATEGORIES[0]);

      const button = document.querySelector('.radio-select__column:nth-child(2) input[type=button]');

      expect(button).not.toBeNull();
      expect(button.getAttribute('value')).toEqual('Done');
      expect(button.getAttribute('aria-expanded')).toEqual('true');

    });

  });

  describe("after clicking the button to select that category", () => {

    beforeEach(() => {

      // start module
      window.GOVUK.modules.start();

      clickButtonForCategory(CATEGORIES[0]);

    });

    describe("clicking on an option with the mouse/trackpad should", () => {

      let optionsColumn;
      let firstOptionPositionSpy;
      let firstOptionLabel;

      beforeEach(() => {

        optionsColumn = document.querySelector('.radio-select__column:nth-child(2)');

        const firstOption = optionsColumn.querySelector('input[type=radio]');
        firstOptionLabel = firstOption.parentNode.querySelector('label').textContent.trim();

        helpers.clickElementWithMouse(firstOption);

      });

      test("remove all the other options", () => {

        // module replaces the column node so this needs querying again
        optionsColumn = document.querySelector('.radio-select__column:nth-child(2)');

        expect(optionsColumn.querySelectorAll('input[type=radio]').length).toEqual(1);
        expect(optionsColumn.querySelector('label').textContent.trim()).toEqual(firstOptionLabel);

      });

      test("add a button for choosing a different time", () => {

        const button = document.querySelector('.radio-select__column:nth-child(3) input[type=button]');

        expect(button).not.toBeNull();
        expect(button.getAttribute('value')).toEqual('Choose a different time');

      })

      test("focus the selected option", () => {

        selectedOption = document.querySelector('.radio-select__column input[checked=checked]');

        expect(document.activeElement).toBe(selectedOption);

      });

    });

    describe("selecting an option with the space key should", () => {

      let optionsColumn;
      let secondOptionLabel;

      beforeEach(() => {

        optionsColumn = document.querySelector('.radio-select__column:nth-child(2)');

        const options = optionsColumn.querySelectorAll('input[type=radio]');
        secondOptionLabel = options[1].parentNode.querySelector('label').textContent.trim();

        helpers.moveSelectionToRadio(options[1], { 'direction': 'down' });
        helpers.activateRadioWithSpace(options[1]);
      });

      test("remove all the other options", () => {

        // module replaces the column node so this needs querying again
        optionsColumn = document.querySelector('.radio-select__column:nth-child(2)');

        expect(optionsColumn.querySelectorAll('input[type=radio]').length).toEqual(1);
        expect(optionsColumn.querySelector('label').textContent.trim()).toEqual(secondOptionLabel);

      });

      test("add a button for choosing a different time", () => {

        const button = document.querySelector('.radio-select__column:nth-child(3) input[type=button]');

        expect(button).not.toBeNull();
        expect(button.getAttribute('value')).toEqual('Choose a different time');

      })

      test("focus the selected option", () => {

        selectedOption = document.querySelector('.radio-select__column input[checked=checked]');

        expect(document.activeElement).toBe(selectedOption);

      });

    });

    describe("selecting an option with the enter key should", () => {

      let optionsColumn;
      let secondOptionLabel;

      beforeEach(() => {

        optionsColumn = document.querySelector('.radio-select__column:nth-child(2)');

        const options = optionsColumn.querySelectorAll('input[type=radio]');
        secondOptionLabel = options[1].parentNode.querySelector('label').textContent.trim();

        // simulate events for arrow key press moving selection to 2nd option
        // event for down arrow key press
        helpers.triggerEvent(options[1], 'keydown', {
          eventInit: { which: 40 }
        });
        // click event fired from option radio being activated
        helpers.triggerEvent(options[1], 'click', {
          eventInit: { pageX: 0 }
        });

        // simulate events for enter key press to confirm selection
        // event for enter key press
        helpers.triggerEvent(options[1], 'keydown', {
          eventInit: { which: 13 }
        });

      });

      test("remove all the other options", () => {

        // module replaces the column node so this needs querying again
        optionsColumn = document.querySelector('.radio-select__column:nth-child(2)');

        expect(optionsColumn.querySelectorAll('input[type=radio]').length).toEqual(1);
        expect(optionsColumn.querySelector('label').textContent.trim()).toEqual(secondOptionLabel);

      });

      test("add a button for choosing a different time", () => {

        const button = document.querySelector('.radio-select__column:nth-child(3) input[type=button]');

        expect(button).not.toBeNull();
        expect(button.getAttribute('value')).toEqual('Choose a different time');

      })

      test("focus the selected option", () => {

        selectedOption = document.querySelector('.radio-select__column input[checked=checked]');

        expect(document.activeElement).toBe(selectedOption);

      });

    });

    test("clicking the 'Done' button should choose whatever time is selected", () => {

      let optionsColumn = document.querySelector('.radio-select__column:nth-child(2)');
      const secondOption = optionsColumn.querySelectorAll('input[type=radio]')[1];
      const secondOptionLabel = document.querySelector('label[for=' + secondOption.getAttribute('id')).textContent.trim();
      const doneButton = document.querySelector('.radio-select__column:nth-child(2) input[type=button]');

      // select second option
      secondOption.checked = true;
      secondOption.setAttribute('checked', '');

      helpers.triggerEvent(doneButton, 'click');

      optionsColumn = document.querySelector('.radio-select__column:nth-child(2)');

      expect(optionsColumn.querySelectorAll('input[type=radio]').length).toEqual(1);
      expect(optionsColumn.querySelector('label').textContent.trim()).toEqual(secondOptionLabel);

    });

    describe("after selecting an option clicking the 'Choose a different time' button should", () => {

      beforeEach(() => {

        // select the first option
        const firstOption = document.querySelector('.radio-select__column:nth-child(2) input[type=radio]');

        helpers.clickElementWithMouse(firstOption);

        // click the 'Choose a different time' button
        const resetButton = document.querySelector('.radio-select__column:nth-child(3) input[type=button]');
        helpers.triggerEvent(resetButton, 'click');

      });

      test("reset the module", () => {

        categoryButtons = document.querySelectorAll('.radio-select__column:nth-child(2) .radio-select__button--category');

        expect(categoryButtons.length).toEqual(CATEGORIES.length);

      });

      test("focus the default option", () => {

        expect(document.activeElement).toBe(document.getElementById('scheduled_for-0'));

      });

    });

  });

});
