(function(window) {
  "use strict";

  // HTML escaping utility to prevent XSS
  const escapeHtml = (unsafe) => {
    if (!unsafe) return '';
    return String(unsafe)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  };

  window.NotifyModules['template-folder-form'] = function() {

    this.start = function(templateFolderForm) {
      this.form = templateFolderForm;

      // remove the hidden unknown button - if you've got JS enabled then the action you want to do is implied by
      // which field is visible.
      const unknownButton = this.form.querySelector('button[value=unknown]');
      if (unknownButton) {
        unknownButton.remove();
      }

      this.liveRegionCounter = this.form.querySelector('.selection-counter');

      // Critical: Verify live region counter exists before proceeding
      if (!this.liveRegionCounter) {
        console.error('templateFolderForm: .selection-counter element not found');
        return;
      }

      // Get single channel data from DOM (must happen after DOM is ready)
      const addNewTemplateForm = document.querySelector('div[id=add_new_template_form]');
      this.singleNotificationChannel = addNewTemplateForm ? addNewTemplateForm.getAttribute("data-channel") : null;
      this.singleChannelService = addNewTemplateForm ? addNewTemplateForm.getAttribute("data-service") : null;

      this.liveRegionCounter.insertAdjacentElement('beforebegin', this.nothingSelectedButtons);
      this.liveRegionCounter.insertAdjacentElement('beforebegin', this.itemsSelectedButtons);

      // all the diff states that we want to show or hide - using Map for better performance
      this.states = [
        {
          key: 'nothing-selected-buttons',
          el: this.form.querySelector('#nothing_selected'),
          cancellable: false
        },
        {
          key: 'items-selected-buttons',
          el: this.form.querySelector('#items_selected'),
          cancellable: false
        },
        {
          key: 'move-to-existing-folder',
          el: this.form.querySelector('#move_to_folder_radios'),
          cancellable: true,
          setFocus: () => {
            const el = document.getElementById('move_to_folder_radios');
            if (el) el.focus();
          },
          action: 'move to folder',
          description: 'Press move to confirm or cancel to close'
        },
        {
          key: 'move-to-new-folder',
          el: this.form.querySelector('#move_to_new_folder_form'),
          cancellable: true,
          setFocus: () => {
            const el = document.getElementById('move_to_new_folder_form');
            if (el) el.focus();
          },
          action: 'move to new folder',
          description: 'Press add to new folder to confirm name or cancel to close'
        },
        {
          key: 'add-new-folder',
          el: this.form.querySelector('#add_new_folder_form'),
          cancellable: true,
          setFocus: () => {
            const el = document.getElementById('add_new_folder_form');
            if (el) el.focus();
          },
          action: 'new folder',
          description: 'Press add new folder to confirm name or cancel to close'
        },
        {
          key: 'add-new-template',
          el: this.form.querySelector('#add_new_template_form'),
          cancellable: true,
          setFocus: () => {
            const el = document.getElementById('add_new_template_form');
            if (el) el.focus();
          },
          action: 'new template',
          description: 'Press continue to confirm selection or cancel to close'
        }
      ];

      // cancel/clear buttons only relevant if JS enabled, so
      this.states.filter(state => state.cancellable).forEach((x) => this.addCancelButton(x));
      this.states.filter(state => state.key === 'items-selected-buttons').forEach(x => this.addClearButton(x));

      // make elements focusable
      this.states.filter(state => state.setFocus).forEach(x => {
        if (x.el) {
          x.el.setAttribute('tabindex', '0');
        }
      });

      this.addDescriptionsToStates();

      // activate stickiness of elements in each state
      this.activateStickyElements();

      // first off show the new template / new folder buttons
      this._lastState = this.form.dataset.prevState;
      if (this._lastState === undefined) {
        this.selectActionButtons();
      } else {
        this.currentState = this._lastState;
        this.render();
      }

      this.form.addEventListener('click', (event) => {
        const button = event.target.closest('button.usa-button');
        if (button) {
          this.actionButtonClicked(event);
        }
      });
      this.form.addEventListener('change', (event) => {
        if (event.target.matches('input[type=checkbox]')) {
          this.templateFolderCheckboxChanged();
        } else if (event.target.matches('input[name="add_template_by_template_type"]')) {
          this.templateTypeChanged();
        }
      });
    };

    this.addDescriptionsToStates = function () {
      this.states.filter(state => 'description' in state).forEach(state => {
        const id = `${escapeHtml(state.key)}__description`;
        const description = `<p class="usa-sr-only" id="${id}">${escapeHtml(state.description)}</p>`;
        if (state.el) {
          state.el.insertAdjacentHTML('afterbegin', description);
          state.el.setAttribute('aria-describedby', id);
        }
      });
    };

    this.activateStickyElements = function() {
      const oldClass = 'js-will-stick-at-bottom-when-scrolling';
      const newClass = 'js-stick-at-bottom-when-scrolling';

      this.states.forEach(state => {
        if (state.el) {
          state.el.querySelectorAll('.' + oldClass).forEach(el => {
            el.classList.remove(oldClass);
            el.classList.add(newClass);
          });
        }
      });
    };

    this.addCancelButton = function(state) {
      const selector = `[value=${state.key}]`;
      const cancel = this.makeButton('Cancel', {
        'onclick': () => {
          // clear existing data
          if (state.el) {
            state.el.querySelectorAll('input[type="radio"]').forEach(input => input.checked = false);
            state.el.querySelectorAll('input[type="text"]').forEach(input => input.value = '');
          }

          // go back to action buttons
          this.selectActionButtons(selector);
        },
        'cancelSelector': selector,
        'nonvisualText': state.action
      });

      if (state.el) {
        const submitButton = state.el.querySelector('[type=submit]');
        if (submitButton) {
          submitButton.insertAdjacentElement('afterend', cancel);
        }
      }
    };

    this.addClearButton = function(state) {
      const selector = 'button[value=add-new-template]';
      const clear = this.makeButton('Clear', {
        'onclick': () => {
          // uncheck all templates and folders
          this.form.querySelectorAll('input[type="checkbox"]').forEach(input => input.checked = false);

          // go back to action buttons
          this.selectActionButtons(selector);
        },
        'nonvisualText': "selection"
      });

      if (state.el) {
        const counter = state.el.querySelector('.template-list-selected-counter');
        if (counter) {
          counter.appendChild(clear);
        }
      }
    };

    this.makeButton = (text, opts) => {
      const btn = document.createElement('a');
      btn.href = '';
      btn.textContent = text;
      btn.classList.add('usa-link', 'js-cancel');

      // isn't set if cancelSelector is undefined
      if (opts.cancelSelector) {
        btn.dataset.target = opts.cancelSelector;
      }
      btn.setAttribute('tabindex', '0');

      const handler = event => {
        // space, enter or no keyCode (must be mouse input)
        if ([13, 32, undefined].indexOf(event.keyCode) > -1) {
          event.preventDefault();
          if (opts.hasOwnProperty('onclick')) {
            opts.onclick();
          }
        }
      };

      btn.addEventListener('click', handler);
      btn.addEventListener('keydown', handler);

      if (opts.hasOwnProperty('nonvisualText')) {
        const span = document.createElement('span');
        span.className = 'usa-sr-only';
        span.textContent = ' ' + opts.nonvisualText;
        btn.appendChild(span);
      }

      return btn;
    };

    this.selectActionButtons = function (targetSelector) {
      // If we want to show one of the grey choose actions state, we can pretend we're in the choose actions state,
      // and then pretend a checkbox was clicked to work out whether to show zero or non-zero options.
      // This calls a render at the end
      this.currentState = 'nothing-selected-buttons';
      this.templateFolderCheckboxChanged();
      if (targetSelector) {
        const target = document.querySelector(targetSelector);
        if (target) {
          target.focus();
        }
      }
    };

    // method that checks the state against the last one, used prior to render() to see if needed
    this.stateChanged = function() {
      let changed = this.currentState !== this._lastState;

      this._lastState = this.currentState;
      return changed;
    };

    this.actionButtonClicked = function(event) {
      const button = event.target.closest('button.usa-button') || event.target;
      this.currentState = button.value;

      if (this.currentState === 'add-new-template' && this.singleNotificationChannel) {
        event.preventDefault();
        window.location = "/services/" + encodeURIComponent(this.singleChannelService) + "/templates/add-" + encodeURIComponent(this.singleNotificationChannel);
      } else if (this.currentState === 'add-new-template') {
        // Check if a template type is selected
        const selectedInput = this.form.querySelector('input[name="add_template_by_template_type"]:checked');
        const selectedTemplateType = selectedInput ? selectedInput.value : null;

        if (selectedTemplateType) {
          // Template type is selected, let the form submit normally
          return true;
        } else {
          // No template type selected, show the selection UI
          event.preventDefault();
          this.form.querySelectorAll('input[type=checkbox]').forEach(input => input.checked = false);
          this.selectionStatus.update({ total: 0, templates: 0, folders: 0 });

          if (this.stateChanged()) {
            this.render();
          }
        }
      } else {
        // If state is not changing, this is a submit button - allow form submission
        if (this.currentState === this._lastState) {
          return true;
        }

        // Otherwise, show the form UI
        event.preventDefault();
        if (this.stateChanged()) {
          this.render();
        }
      }
    };

    this.selectionStatus = {
      'default': 'Nothing selected',
      'selected': numSelected => {
        const getString = key => {
          if (numSelected[key] === 0) {
            return '';
          } else if (numSelected[key] === 1) {
            return `1 ${key.substring(0, key.length - 1)}`;
          } else {
            return `${numSelected[key]} ${key}`;
          }
        };

        const results = [];

        if (numSelected.templates > 0) {
          results.push(getString('templates'));
        }
        if (numSelected.folders > 0) {
          results.push(getString('folders'));
        }
        return results.join(', ') + ' selected';
      },
      'update': numSelected => {
        const message = (numSelected.total > 0) ? this.selectionStatus.selected(numSelected) : this.selectionStatus.default;

        const counters = document.querySelectorAll('.template-list-selected-counter__count');
        counters.forEach(counter => counter.textContent = message);

        if (this.liveRegionCounter) {
          this.liveRegionCounter.textContent = message;
        }
      }
    };

    this.templateFolderCheckboxChanged = function() {
      const numSelected = this.countSelectedCheckboxes();

      if (this.currentState === 'nothing-selected-buttons' && numSelected.total !== 0) {
        // user has just selected first item
        this.currentState = 'items-selected-buttons';
      } else if (this.currentState === 'items-selected-buttons' && numSelected.total === 0) {
        // user has just deselected last item
        this.currentState = 'nothing-selected-buttons';
      }

      if (this.stateChanged()) {
        this.render();
      }

      this.selectionStatus.update(numSelected);

      const counters = document.querySelectorAll('.template-list-selected-counter');
      const shouldShow = this.hasCheckboxes();
      counters.forEach(counter => {
        counter.style.display = shouldShow ? '' : 'none';
      });
    };

    this.templateTypeChanged = function() {
      this.updateContinueButtonState();
    };

    this.updateContinueButtonState = function() {
      const selectedInput = this.form.querySelector('input[name="add_template_by_template_type"]:checked');
      const selectedTemplateType = selectedInput ? selectedInput.value : null;
      const continueButton = this.form.querySelector('#add_new_template_form button[value="add-new-template"]');

      if (continueButton) {
        continueButton.disabled = !selectedTemplateType;
      }
    };

    this.hasCheckboxes = function() {
      return this.form.querySelectorAll('input[type="checkbox"]').length > 0;
    };

    this.countSelectedCheckboxes = function() {
      const allSelected = Array.from(this.form.querySelectorAll('input[type="checkbox"]:checked'));
      // Check for sibling elements to determine if checkbox is for template or folder
      // This matches the original jQuery logic: $(el).siblings('.template-list-template')
      const templates = allSelected.filter(el => {
        if (!el.parentElement) return false;
        return el.parentElement.querySelector('.template-list-template') !== null;
      }).length;
      const folders = allSelected.filter(el => {
        if (!el.parentElement) return false;
        return el.parentElement.querySelector('.template-list-folder') !== null;
      }).length;
      const results = {
        'templates': templates,
        'folders': folders,
        'total': allSelected.length
      };
      return results;
    };

    this.render = function() {
      const currentStateObj = this.states.find(state => state.key === this.currentState);
      let scrollTop;

      // detach everything, unless they are the currentState
      this.states.forEach(state => {
        if (state.key === this.currentState) {
          if (state.el) {
            this.liveRegionCounter.insertAdjacentElement('beforebegin', state.el);
          }
        } else {
          if (state.el && state.el.parentElement) {
            state.el.remove();
          }
        }
      });

      if (this.currentState === 'add-new-template') {
        this.form.querySelectorAll('.template-list-item').forEach(el => el.classList.add('js-hidden'));

        const liveSearch = document.querySelector('.live-search');
        if (liveSearch) liveSearch.classList.add('js-hidden');

        const breadcrumb = document.getElementById('breadcrumb-template-folders');
        if (breadcrumb) breadcrumb.classList.add('js-hidden');

        const templateList = document.getElementById('template-list');
        if (templateList) templateList.classList.add('js-hidden');

        this.form.querySelectorAll('input[type=checkbox]').forEach(input => input.checked = false);
        this.selectionStatus.update({ total: 0, templates: 0, folders: 0 });

        const pageTitle = document.getElementById('page-title');
        if (pageTitle) pageTitle.textContent = 'New Template';

        const pageDescription = document.getElementById('page-description');
        if (pageDescription) pageDescription.textContent = 'Every message starts with a template. Choose to start with a blank template or copy an existing template.';

        document.title = 'New Templates';

        // Disable Continue button initially and update based on selection
        this.updateContinueButtonState();
      } else {
        this.form.querySelectorAll('.template-list-item').forEach(el => el.classList.remove('js-hidden'));

        const liveSearch = document.querySelector('.live-search');
        if (liveSearch) liveSearch.classList.remove('js-hidden');

        const breadcrumb = document.getElementById('breadcrumb-template-folders');
        if (breadcrumb) breadcrumb.classList.remove('js-hidden');

        const templateList = document.getElementById('template-list');
        if (templateList) templateList.classList.remove('js-hidden');

        const pageTitle = document.getElementById('page-title');
        if (pageTitle) pageTitle.textContent = 'Select or create a template';

        const pageDescription = document.getElementById('page-description');
        if (pageDescription) pageDescription.textContent = 'Every message starts with a template. To send, choose or create a template.';

        document.title = 'Select or create a template';
      }

      if (currentStateObj && 'setFocus' in currentStateObj) {
        scrollTop = window.scrollY;
        currentStateObj.setFocus();
        window.scrollTo(window.scrollX, scrollTop);
      }
    };

    const createNothingSelectedButtons = () => {
      const div = document.createElement('div');
      div.id = 'nothing_selected';
      div.innerHTML = `
        <div class="js-stick-at-bottom-when-scrolling">
          <div class="usa-button-group">
            <button class="usa-button" value="add-new-template" aria-expanded="false" role="button">
              New template
            </button>
            <button class="usa-button usa-button--outline" value="add-new-folder" aria-expanded="false" role="button">
              New folder
            </button>
          </div>
          <div class="template-list-selected-counter">
            <span class="template-list-selected-counter__count" aria-hidden="true">
              ${this.selectionStatus.default}
            </span>
          </div>
        </div>
      `;
      return div;
    };

    const createItemsSelectedButtons = () => {
      const div = document.createElement('div');
      div.id = 'items_selected';
      div.innerHTML = `
        <div class="js-stick-at-bottom-when-scrolling">
          <div class="usa-button-group">
            <button class="usa-button" value="move-to-existing-folder" aria-expanded="false" role="button">
              Move<span class="usa-sr-only"> selection to folder</span>
            </button>
            <button class="usa-button usa-button--outline" value="move-to-new-folder" aria-expanded="false" role="button">
              Add to new folder
            </button>
          </div>
          <div class="template-list-selected-counter" aria-hidden="true">
            <span class="template-list-selected-counter__count text-base" aria-hidden="true">
              ${this.selectionStatus.selected({ templates: 1, folders: 0, total: 1 })}
            </span>
          </div>
        </div>
      `;
      return div;
    };

    this.nothingSelectedButtons = createNothingSelectedButtons();
    this.itemsSelectedButtons = createItemsSelectedButtons();
  };

})(window);
