(function(window) {

  "use strict";

  var Modules = window.NotifyModules;

  // Template functions for rendering component states
  let renderStates = {
    'initial': function(data) {
      return `
        ${data.showNowAsDefault ? `
          <div class="radio-select__column margin-y-2">
            <div class="usa-radio">
              <input class="usa-radio__input" checked="checked" id="${data.name}-0" name="${data.name}" type="radio" value="">
              <label class="usa-radio__label" for="${data.name}-0">Now</label>
            </div>
          </div>
        ` : ''}
        <div class="radio-select__column margin-y-2">
          ${data.categories.map(category =>
            `<input type='button' class='usa-button usa-button--outline radio-select__button--category' aria-expanded="false" value='${category}' />`
          ).join('')}
        </div>
      `;
    },
    'choose': function(data) {
      return `
        ${data.showNowAsDefault ? `
          <div class="radio-select__column margin-y-2">
            <div class="usa-radio">
              <input class="usa-radio__input" checked="checked" id="${data.name}-0" name="${data.name}" type="radio" value="">
              <label class="usa-radio__label" for="${data.name}-0">Now</label>
            </div>
          </div>
        ` : ''}
        <div class="radio-select__column margin-y-2">
          ${data.choices.map(choice => `
            <div class="usa-radio js-option">
              <input class="usa-radio__input" type="radio" value="${choice.value}" id="${choice.id}" name="${data.name}" />
              <label class="usa-radio__label" for="${choice.id}">${choice.label}</label>
            </div>
          `).join('')}
          <input type='button' class='usa-button usa-button--outline radio-select__button--done margin-top-4' aria-expanded='true' value='Back to select a new time' />
        </div>
      `;
    },
    'chosen': function(data) {
      return `
        ${data.showNowAsDefault ? `
          <div class="radio-select__column margin-y-2">
            <div class="usa-radio">
              <input class="usa-radio__input" id="${data.name}-0" name="${data.name}" type="radio" value="">
              <label class="usa-radio__label" for="${data.name}-0">Now</label>
            </div>
          </div>
        ` : ''}
        <div class="radio-select__column margin-y-2">
          ${data.choices.map(choice => `
            <div class="usa-radio">
              <input class="usa-radio__input" checked="checked" type="radio" value="${choice.value}" id="${choice.id}" name="${data.name}" />
              <label class="usa-radio__label" for="${choice.id}">${choice.label}</label>
            </div>
          `).join('')}
        </div>
        <div class="radio-select__column margin-y-2">
          <input type='button' class='usa-button usa-button--outline radio-select__button--reset' aria-expanded='false' value='Choose a different time' />
        </div>
      `;
    }
  };

  let shiftFocus = function(elementToFocus, component) {
    const radios = component.querySelectorAll('[type=radio]');
    // The first option is always the default
    if (elementToFocus === 'default' && radios[0]) {
      radios[0].focus();
    }
    if (elementToFocus === 'option' && radios[1]) {
      radios[1].focus();
    }
  };

  Modules['radio-select'] = function() {

    this.start = function(component) {

      let render = (state, data) => {
        component.innerHTML = renderStates[state](data);
      };
      // store array of all options in component
      let choices = Array.from(component.querySelectorAll('label')).map(function(element) {
        return {
          'id': element.htmlFor,
          'label': element.textContent.trim(),
          'value': element.previousElementSibling.value
        };
      });
      let categories = component.dataset.categories.split(',');
      let name = component.querySelector('input').name;
      let mousedownOption = null;
      let showNowAsDefault = (
        component.dataset.showNowAsDefault === 'true' ?
        {'name': name} : false
      );

      // functions for changing the state of the component's HTML
      const reset = () => {
        render('initial', {
          'categories': categories,
          'name': name,
          'showNowAsDefault': showNowAsDefault
        });
        shiftFocus('default', component);
      };
      const selectOption = (value) => {
        render('chosen', {
          'choices': choices.filter(
            element => element.value == value
          ),
          'name': name,
          'showNowAsDefault': showNowAsDefault
        });
        shiftFocus('option', component);
      };

      // use mousedown + mouseup event sequence to confirm option selection
      const trackMouseup = (event) => {
        const parentNode = event.target.parentNode;

        if (parentNode === mousedownOption) {
          const input = parentNode.querySelector('input');
          const value = input ? input.value : '';

          selectOption(value);

          // clear tracking
          mousedownOption = null;
          document.removeEventListener('mouseup', trackMouseup);
        }
      };

      // set events using event delegation
      component.addEventListener('click', function(event) {
        // Handle category button clicks
        if (event.target.classList.contains('radio-select__button--category')) {
          event.preventDefault();
          let wordsInDay = event.target.value.split(' ');
          let day = wordsInDay[wordsInDay.length - 1].toLowerCase();
          render('choose', {
            'choices': choices.filter(
              element => element.label.toLowerCase().indexOf(day) > -1
            ),
            'name': name,
            'showNowAsDefault': showNowAsDefault
          });
          shiftFocus('option', component);
        }

        // Handle done button clicks
        if (event.target.classList.contains('radio-select__button--done')) {
          event.preventDefault();
          let selection = event.target.parentNode.querySelector('input[type=radio]:checked');
          if (selection) {
            render('chosen', {
              'choices': choices.filter(
                element => element.value == selection.value
              ),
              'name': name,
              'showNowAsDefault': showNowAsDefault
            });
            shiftFocus('option', component);
          } else {
            reset();
            shiftFocus('default', component);
          }
        }

        // Handle reset button clicks
        if (event.target.classList.contains('radio-select__button--reset')) {
          event.preventDefault();
          reset();
          shiftFocus('default', component);
        }
      });

      component.addEventListener('mousedown', function(event) {
        // Handle option mousedown
        const option = event.target.closest('.js-option');
        if (option) {
          mousedownOption = option;
          // mouseup on the same option completes the click action
          document.addEventListener('mouseup', trackMouseup);
        }
      });

      component.addEventListener('keydown', function(event) {
        // Handle radio keydown (space and enter)
        if (event.target.type === 'radio') {
          // allow keypresses which aren't enter or space through
          if (event.which !== 13 && event.which !== 32) {
            return true;
          }

          event.preventDefault();
          let value = event.target.value;
          selectOption(value);
        }
      });

      // set HTML to initial state
      render('initial', {
        'categories': categories,
        'name': name,
        'showNowAsDefault': showNowAsDefault
      });

      component.style.height = 'auto';

    };

  };

})(window);
