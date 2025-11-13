(function (window) {
  "use strict";

  function Summary (module) {
    this.module = module;
    this.el = module.formGroup.querySelector('.selection-summary');
    this.fieldLabel = module.fieldLabel;
    this.total = module.total;
    this.addContent();
    this.update(module.getSelection());
  }
  Summary.prototype.templates = {
    all: (selection, total, field) => `All ${field}s`,
    some: (selection, total, field) => `${selection} of ${total} ${field}s`,
    none: (selection, total, field) => ({
        "folder": "No folders (only templates outside a folder)",
        "team member": "No team members (only you)"
    }[field] || `No ${field}s`)
  };
  Summary.prototype.addContent = function() {
    const hint = this.module.formGroup.querySelector('.usa-hint');
    this.text = document.createElement('p');
    this.text.className = 'selection-summary__text';

    if (this.fieldLabel === 'folder') { this.text.classList.add('selection-summary__text--folders'); }

    if (hint) {
      this.el.setAttribute('id', hint.getAttribute('id'));
      hint.remove();
    }
    this.el.appendChild(this.text);
  };
  Summary.prototype.update = function(selection) {
    let template;

    if (selection === this.total) {
      template = 'all';
    } else if (selection > 0) {
      template = 'some';
    } else {
      template = 'none';
    }

    this.text.innerHTML = this.templates[template](selection, this.total, this.fieldLabel);
  };
  Summary.prototype.bindEvents = function () {
    // take summary out of tab order when focus moves
    this.el.addEventListener('blur', (e) => e.target.setAttribute('tabindex', '-1'));
  };

  function Footer (module) {
    this.module = module;
    this.fieldLabel = module.fieldLabel;
    this.fieldsetId = module.fieldset.getAttribute('id');
    this.el = this.getEl(this.module.expanded);
    this.module.formGroup.appendChild(this.el);
  }
  Footer.prototype.buttonContent = {
    change: (fieldLabel) => `Choose ${fieldLabel}s`,
    done: (fieldLabel) => `Done<span class="usa-sr-only"> choosing ${fieldLabel}s</span>`
  };
  Footer.prototype.getEl = function (expanded) {
    const buttonState = expanded ? 'done' : 'change';
    const buttonContent = this.buttonContent[buttonState](this.fieldLabel);
    const stickyClass = expanded ? ' js-stick-at-bottom-when-scrolling' : '';

    const div = document.createElement('div');
    div.className = `selection-footer${stickyClass} margin-top-2`;
    div.innerHTML = `<button
                class="usa-button usa-button--outline selection-footer__button"
                aria-expanded="${expanded ? 'true' : 'false'}"
                aria-controls="${this.fieldsetId}">
              ${buttonContent}
              </button>`;
    return div;
  };
  Footer.prototype.update = function (expanded) {
    this.el.remove();
    this.el = this.getEl(expanded);

    this.module.formGroup.appendChild(this.el);

  };

  function CollapsibleCheckboxes () {}
  CollapsibleCheckboxes.prototype._focusTextElement = (el) => {
    el.setAttribute('tabindex', '-1');
    el.focus();
  };
  CollapsibleCheckboxes.prototype.start = function(component) {
    this.component = component;
    this.formGroup = component.querySelector('.usa-form-group');
    this.fieldset = this.formGroup.querySelector('fieldset');
    this.checkboxes = this.fieldset.querySelectorAll('input[type=checkbox]');
    this.fieldLabel = component.dataset.fieldLabel;
    this.total = this.checkboxes.length;
    this.legendText = this.fieldset.querySelector('legend').textContent.trim();
    this.expanded = false;
    this.checkUncheckButtonsAdded = false;

    this.addHeadingHideLegend();

    // generate summary and footer
    this.footer = new Footer(this);
    this.summary = new Summary(this);

    this.fieldset.insertAdjacentElement('beforebegin', this.summary.el);

    // add custom classes
    this.formGroup.classList.add('selection-wrapper');
    this.fieldset.classList.add('selection-content');

    // hide checkboxes
    this.fieldset.style.display = 'none';

    this.bindEvents();
  };
  CollapsibleCheckboxes.prototype.getSelection = function() {
    return Array.from(this.checkboxes).filter(cb => cb.checked).length;
  };
  CollapsibleCheckboxes.prototype.addHeadingHideLegend = function() {
    const headingLevel = this.component.dataset.headingLevel || '2';

    this.heading = document.createElement(`h${headingLevel}`);
    this.heading.className = 'heading-small';
    this.heading.textContent = this.legendText;
    this.fieldset.insertAdjacentElement('beforebegin', this.heading);

    this.fieldset.querySelector('legend').classList.add('usa-sr-only');
  };
  CollapsibleCheckboxes.prototype.addCheckUncheckAllButtons = function() {
    const buttonsContainer = document.createElement('div');
    buttonsContainer.className = 'check-uncheck-all-buttons margin-bottom-2';

    this.toggleAllButton = document.createElement('button');
    this.toggleAllButton.type = 'button';
    this.toggleAllButton.className = 'usa-button usa-button--outline usa-button--small';
    this.toggleAllButton.textContent = 'Select all';

    buttonsContainer.appendChild(this.toggleAllButton);

    this.summary.el.insertAdjacentElement('afterend', buttonsContainer);

    this.toggleAllButton.addEventListener('click', this.toggleAll.bind(this));

    this.updateToggleButtonText();
  };
  CollapsibleCheckboxes.prototype.toggleAll = function(e) {
    e.preventDefault();
    e.stopPropagation();
    const allChecked = Array.from(this.checkboxes).filter(cb => cb.checked).length === this.checkboxes.length;

    if (allChecked) {
      this.checkboxes.forEach(cb => cb.checked = false);
    } else {
      this.checkboxes.forEach(cb => cb.checked = true);
    }

    this.handleSelection();
    this.updateToggleButtonText();
  };
  CollapsibleCheckboxes.prototype.updateToggleButtonText = function() {
    if (!this.toggleAllButton) return;

    const checkedCount = Array.from(this.checkboxes).filter(cb => cb.checked).length;
    const allChecked = checkedCount === this.checkboxes.length;

    if (allChecked) {
      this.toggleAllButton.textContent = 'Deselect all';
    } else {
      this.toggleAllButton.textContent = 'Select all';
    }
  };
  CollapsibleCheckboxes.prototype.expand = function(e) {
    if (e !== undefined) { e.preventDefault(); }

    if (!this.expanded) {
      this.fieldset.style.display = '';
      this.expanded = true;
      this.summary.update(this.getSelection());
      this.footer.update(this.expanded);

      if (!this.checkUncheckButtonsAdded) {
        this.addCheckUncheckAllButtons();
        this.checkUncheckButtonsAdded = true;
      } else {
        if (this.toggleAllButton) {
          this.toggleAllButton.parentElement.style.display = '';
        }
      }
    }

    // shift focus whether expanded or not
    this._focusTextElement(this.fieldset);
  };
  CollapsibleCheckboxes.prototype.collapse = function(e) {
    if (e !== undefined) { e.preventDefault(); }

    if (this.expanded) {
      this.fieldset.style.display = 'none';
      this.expanded = false;
      this.summary.update(this.getSelection());
      this.footer.update(this.expanded);

      if (this.toggleAllButton) {
        this.toggleAllButton.parentElement.style.display = 'none';
      }
    }

    // shift focus whether expanded or not
    this._focusTextElement(this.summary.text);
  };
  CollapsibleCheckboxes.prototype.handleClick = function(e) {
    if (this.expanded) {
      this.collapse(e);
    } else {
      this.expand(e);
    }
  };
  CollapsibleCheckboxes.prototype.handleSelection = function(e) {
    this.summary.update(this.getSelection(), this.total, this.fieldLabel);
    this.updateToggleButtonText();
  };
  CollapsibleCheckboxes.prototype.bindEvents = function() {
    this.formGroup.addEventListener('click', (e) => {
      if (e.target.closest('.usa-button')) {
        this.handleClick.call(this, e);
      }
    });

    this.checkboxes.forEach(cb => {
      cb.addEventListener('click', this.handleSelection.bind(this));
    });

    this.summary.bindEvents(this);
  };

  NotifyModules['collapsible-checkboxes'] = function() {
    return new CollapsibleCheckboxes();
  };

}(window));
