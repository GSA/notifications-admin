(function(window) {
  "use strict";

  if (
    !('oninput' in document.createElement('input'))
  ) return;

  const tagPattern = /\(\(([^\)\((\?)]+)(\?\?)?([^\)\(]*)\)\)/g;

  window.NotifyModules['enhanced-textbox'] = function() {

    this.start = function(element) {

      let textarea = element;
      let visibleTextbox;

      this.highlightPlaceholders = (
        typeof textarea.dataset.highlightPlaceholders === 'undefined' ||
        textarea.dataset.highlightPlaceholders !== 'false'
      );

      // Create wrapper div
      const wrapper = document.createElement('div');
      wrapper.className = 'textbox-highlight-wrapper';

      // Insert wrapper before textarea and move textarea into it
      textarea.parentNode.insertBefore(wrapper, textarea);
      wrapper.appendChild(textarea);

      // Create background div
      this.background = document.createElement('div');
      this.background.className = 'textbox-highlight-background';
      this.background.setAttribute('aria-hidden', 'true');

      // Insert background after textarea
      textarea.parentNode.insertBefore(this.background, textarea.nextSibling);

      this.textbox = textarea;

      this.textbox.addEventListener("input", this.update);
      window.addEventListener("resize", this.resize);

      // Clone textbox to measure initial height
      visibleTextbox = this.textbox.cloneNode(true);
      visibleTextbox.style.position = 'absolute';
      visibleTextbox.style.visibility = 'hidden';
      visibleTextbox.style.display = 'block';
      document.body.appendChild(visibleTextbox);

      this.initialHeight = visibleTextbox.offsetHeight;

      const borderWidth = window.getComputedStyle(this.textbox).borderWidth;
      this.background.style.borderWidth = borderWidth;

      visibleTextbox.remove();

      this.textbox.dispatchEvent(new Event("input"));

    };

    this.resize = () => {

      const computedStyle = window.getComputedStyle(this.textbox);
      const width = parseFloat(computedStyle.width);
      this.background.style.width = width + 'px';

      const backgroundHeight = this.background.offsetHeight;

      this.textbox.style.height = Math.max(this.initialHeight, backgroundHeight) + 'px';

      if ('stickAtBottomWhenScrolling' in window.NotifyModules) {
        window.NotifyModules.stickAtBottomWhenScrolling.recalculate();
      }

    };

    this.contentEscaped = () => {
      const div = document.createElement('div');
      div.textContent = this.textbox.value;
      return div.innerHTML;
    };

    this.contentReplaced = () => this.contentEscaped().replace(
      tagPattern, (match, name, separator, value) => value && separator ?
        `<span class='placeholder-conditional'>((${name}??</span>${value}))` :
        `<span class='placeholder'>((${name}${value}))</span>`
    );

    this.update = () => {

      this.background.innerHTML =
        this.highlightPlaceholders ? this.contentReplaced() : this.contentEscaped();

      this.resize();

    };

  };

})(window);
