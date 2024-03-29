// helpers for generating patterns of HTML

function getRadios (fields, name) {
  const result = '';

  return fields.map((field, idx) => {
    const count = idx + 1;
    const id = field.id || `${name}-${count}`;

    return `
      <div class="usa-radio">
        <input class="usa-radio__input" id="${id}" name="${name}" type="radio" value="${field.value}" ${field.checked ? 'checked' : ''}>
        <label class="usa-radio__label" for="${id}">
          ${field.label}
        </label>
      </div>`;
  }).join("\n");
};

function getRadioGroup (data) {
  let radioGroup = document.createElement('div');

  radioGroup.classList.add('usa-form-group');
  if ('cssClasses' in data) {
    data.cssClasses.forEach(cssClass => radioGroup.classList.add(cssClass));
  }
  radioGroup.innerHTML = `
    <fieldset class="usa-fieldset" id="${data.name}">
      <legend class="usa-fieldset__legend${data.hideLegend ? " usa-sr-only" : ""}">
        ${data.label}
      </legend>
      <div class="usa-radios">
        ${getRadios(data.fields, data.name)}
      </div>
    </fieldset>`;

    return radioGroup;
};

function templatesAndFoldersCheckboxes (hierarchy) {
  let result = '';

  hierarchy.forEach((node, idx) => {

    result += `
      <div class="usa-checkbox template-list-item template-list-item-with-checkbox template-list-item-without-ancestors">
        <input class="usa-checkbox__input" id="templates-or-folder-${idx}" name="templates_and_folders" type="checkbox" value="templates-or-folder-${idx}">
        <label class="usa-checkbox__label template-list-item-label" for="templates-or-folder-${idx}">
          <span class="usa-sr-only">${node.label}</span>
          ${node.label}
        </label>
        <a href="/services/6658542f-0cad-491f-bec8-ab8457700ead/templates/all/folders/${idx}" class="usa-link template-list-${node.type === 'folder' ? 'folder' : 'template'}">
          <span class="live-search-relevant">${node.label}</span>
        </a>
        ${node.meta}
      </div>`;
  });

  return result;

};

exports.getRadios = getRadios;
exports.getRadioGroup = getRadioGroup;
exports.templatesAndFoldersCheckboxes = templatesAndFoldersCheckboxes;
