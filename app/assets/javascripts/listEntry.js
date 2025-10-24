(function (window) {
  'use strict';

  // This module creates dynamic add/remove input lists. It lets users add multiple entries
  // (like email addresses or domains) with "Add another" and "Remove" buttons. It handles
  // min/max entry limits, focus management, and preserves input attributes.
  // We're keeping this for now but it's not currently being used in the application.

  var Modules = window.NotifyModules;
  var lists = [],
      listEntry,
      ListEntry;

  ListEntry = function (elm) {
    var idPattern = elm.id;

    if (!idPattern) {
      return false;
    }
    this.idPattern = idPattern;
    this.elementSelector = '.list-entry, .input-list__button--remove, .input-list__button--add';
    this.entries = [];
    this.wrapper = elm;
    this.minEntries = 2;
    this.listItemName = this.wrapper.dataset.listItemName;
    this.getSharedAttributes();
    this.getOriginalClasses();

    this.getValues();
    this.maxEntries = this.entries.length;
    this.trimEntries();
    this.render();
    this.bindEvents();
  };
  ListEntry.escapeHtml = function(unsafe) {
    if (!unsafe) return '';
    return String(unsafe)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  };
  ListEntry.prototype.renderEntry = function(data) {
    var escapeHtml = ListEntry.escapeHtml;
    return `
      <div class="list-entry">
        <label for="${escapeHtml(data.id)}" class="usa-label">
          <span class="usa-sr-only">${escapeHtml(data.listItemName)} number </span>${escapeHtml(data.number)}.
        </label>
        <input
          class="usa-input ${escapeHtml(data.classes || '')}"
          name="${escapeHtml(data.name)}"
          id="${escapeHtml(data.id)}"
          ${data.value ? `value="${escapeHtml(data.value)}"` : ''}
          ${data.sharedAttributes}
        />
        ${data.button ? `
          <button type="button" class="usa-button usa-button--unstyled input-list__button--remove">
            Remove<span class="usa-sr-only"> ${escapeHtml(data.listItemName)} number ${escapeHtml(data.number)}</span>
          </button>
        ` : ''}
      </div>
    `;
  };
  ListEntry.prototype.renderAddButton = function(data) {
    var escapeHtml = ListEntry.escapeHtml;
    return `<button type="button" class="usa-button usa-button--outline input-list__button--add margin-top-4">Add another ${escapeHtml(data.listItemName)} (${escapeHtml(data.entriesLeft)} remaining)</button>`;
  };
  ListEntry.prototype.getSharedAttributes = function () {
    var inputs = this.wrapper.querySelectorAll('input'),
        generatedAttributes = ['id', 'name', 'value', 'class'],
        attributes = [],
        attrIdx,
        elmAttributes,
        getAttributesHTML;

    getAttributesHTML = function (attrsByElm) {
      var attrStr = '',
          elmIdx = attrsByElm.length,
          existingAttributes = [],
          elmAttrs,
          attrIdx,
          escapeHtml = ListEntry.escapeHtml;

      while (elmIdx--) {
        elmAttrs = attrsByElm[elmIdx];
        attrIdx = elmAttrs.length;
        while (attrIdx--) {
          // prevent duplicates
          if (existingAttributes.indexOf(elmAttrs[attrIdx].name) === -1) {
            attrStr += ` ${escapeHtml(elmAttrs[attrIdx].name)}="${escapeHtml(elmAttrs[attrIdx].value)}"`;
            existingAttributes.push(elmAttrs[attrIdx].name);
          }
        }
      }
      return attrStr;
    };

    inputs.forEach(function (elm) {
      attrIdx = elm.attributes.length;
      elmAttributes = [];
      while(attrIdx--) {
        if (generatedAttributes.indexOf(elm.attributes[attrIdx].name) === -1) {
          elmAttributes.push({
            'name': elm.attributes[attrIdx].name,
            'value': elm.attributes[attrIdx].value
          });
        }
      }
      if (elmAttributes.length) {
        attributes.push(elmAttributes);
      }
    });

    this.sharedAttributes = (attributes.length) ? getAttributesHTML(attributes) : '';
  };
  ListEntry.prototype.getOriginalClasses = function () {
    var firstInput = this.wrapper.querySelector('input');
    if (firstInput) {
      var classList = firstInput.getAttribute('class');
      if (classList) {
        // Preserve any additional classes from the original input
        this.additionalClasses = classList;
      } else {
        this.additionalClasses = '';
      }
    } else {
      this.additionalClasses = '';
    }
  };
  ListEntry.prototype.getValues = function () {
    this.entries = [];
    this.wrapper.querySelectorAll('input').forEach(function (elm) {
      var val = elm.value;

      this.entries.push(val);
    }.bind(this));
  };
  ListEntry.prototype.trimEntries = function () {
    var entryIdx = this.entries.length,
        newEntries = [];

    while (entryIdx--) {
      if (this.entries[entryIdx] !== '') {
        newEntries.push(this.entries[entryIdx]);
      } else {
        if (entryIdx < this.minEntries) {
          newEntries.push('');
        }
      }
    }
    this.entries = newEntries.reverse();
  };
  ListEntry.prototype.getId = function (num) {
    var pattern = this.idPattern.replace("list-entry-", "");
    if ("undefined" === typeof num) {
      return pattern;
    } else {
      return pattern + "-" + num;
    }
  };
  ListEntry.prototype.bindEvents = function () {
    this.wrapper.addEventListener('click', function (e) {
      if (e.target.closest('.input-list__button--remove')) {
        this.removeEntry(e.target);
      } else if (e.target.closest('.input-list__button--add')) {
        this.addEntry();
      }
    }.bind(this));
  };
  ListEntry.prototype.shiftFocus = function (opts) {
    var numberTargeted;

    if (opts.action === 'remove') {
      numberTargeted = (opts.entryNumberFocused > 1) ? opts.entryNumberFocused - 1 : 1;
    } else { // opts.action === 'add'
      numberTargeted = opts.entryNumberFocused + 1;
    }
    var entries = this.wrapper.querySelectorAll('.list-entry');
    if (entries[numberTargeted - 1]) {
      var input = entries[numberTargeted - 1].querySelector('input');
      if (input) {
        input.focus();
      }
    }
  };
  ListEntry.prototype.removeEntryFromEntries = function (entryNumber) {
    var idx,
        len,
        newEntries = [];

    for (idx = 0, len = this.entries.length; idx < len; idx++) {
      if ((entryNumber - 1) !== idx) {
        newEntries.push(this.entries[idx]);
      }
    }
    this.entries = newEntries;
  };
  ListEntry.prototype.addEntry = function () {
    var currentLastEntryNumber = this.entries.length;

    this.getValues();
    this.entries.push('');
    this.render();
    this.shiftFocus({ 'action' : 'add', 'entryNumberFocused' : currentLastEntryNumber });
  };
  ListEntry.prototype.removeEntry = function (removeButton) {
    var button = removeButton.closest('.input-list__button--remove');
    if (!button) {
      console.error('ListEntry: Remove button not found');
      return;
    }
    var span = button.querySelector('span');
    if (!span) {
      console.error('ListEntry: Entry number span not found in remove button');
      return;
    }
    var match = span.textContent.match(/\d+/);
    if (!match) {
      console.error('ListEntry: Could not find entry number in remove button');
      return;
    }
    var entryNumber = parseInt(match[0], 10);

    this.getValues();
    this.removeEntryFromEntries(entryNumber);
    this.render();
    this.shiftFocus({ 'action' : 'remove', 'entryNumberFocused' : entryNumber });
  };
  ListEntry.prototype.render = function () {
    this.wrapper.querySelectorAll(this.elementSelector).forEach(function(el) {
      el.remove();
    });
    this.entries.forEach(function (entry, idx) {
      var entryNumber = idx + 1,
          dataObj = {
            'id' : this.getId(entryNumber),
            'number' : entryNumber,
            'index': idx,
            'name' : this.getId(entryNumber),
            'value' : entry,
            'listItemName' : this.listItemName,
            'sharedAttributes': this.sharedAttributes,
            'classes': this.additionalClasses
          };

      if (entryNumber > 1) {
        dataObj.button = true;
      }
      this.wrapper.insertAdjacentHTML('beforeend', this.renderEntry(dataObj));
    }.bind(this));
    if (this.entries.length < this.maxEntries) {
      this.wrapper.insertAdjacentHTML('beforeend', this.renderAddButton({
        'listItemName' : this.listItemName,
        'entriesLeft' : (this.maxEntries - this.entries.length)
      }));
    }
  };

  Modules['list-entry'] = function () {

    this.start = component => lists.push(new ListEntry(component));

  };

})(window);
