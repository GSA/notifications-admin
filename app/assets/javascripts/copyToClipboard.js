(function(window) {
  "use strict";

  // Only initialize if modern Clipboard API is available
  if (!navigator.clipboard) return;

  window.NotifyModules['copy-to-clipboard'] = function() {

    /**
     * Copy text to clipboard using modern Clipboard API
     * @param {string} text - The text to copy
     * @param {Function} callback - Called after successful copy
     */
    this.copyValueToClipboard = async function(text, callback) {
      try {
        await navigator.clipboard.writeText(text);
        callback();
      } catch (err) {
        console.error('Failed to copy to clipboard:', err);
      }
    };

    this.start = function(component) {

      const value = component.dataset.value;
      const thing = component.dataset.thing;
      const name = component.dataset.name;

      // Determine button label
      const isMultiple = name !== thing;
      const buttonLabel = isMultiple
        ? `Copy ${thing}`
        : `Copy ${thing} to clipboard`;
      const srSuffix = isMultiple ? ` for ${name}` : '';

      // Create simple HTML structure
      component.classList.add('copy-to-clipboard');
      component.innerHTML = `
        <div class="copy-to-clipboard__value">${value}</div>
        <button class="usa-button usa-button--outline copy-to-clipboard__button" type="button">
          ${buttonLabel}<span class="usa-sr-only">${srSuffix}</span>
        </button>
        <span class="usa-sr-only" aria-live="polite" aria-atomic="true"></span>
      `;

      const button = component.querySelector('.copy-to-clipboard__button');
      const srAnnouncement = component.querySelector('[aria-live]');

      // Handle copy button click
      button.addEventListener('click', () => {
        this.copyValueToClipboard(value, () => {
          // Change button text to "Copied!"
          const originalText = button.innerHTML;
          button.innerHTML = `Copied!<span class="usa-sr-only">${srSuffix}</span>`;
          button.disabled = true;

          // Announce to screen readers
          srAnnouncement.textContent = `${thing} copied to clipboard`;

          // Reset button after 2 seconds
          setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
            srAnnouncement.textContent = '';
          }, 2000);
        });
      });

    };
  };

})(window);
