(function(window) {
  "use strict";

  window.NotifyModules['update-status'] = function() {

    const getRenderer = component => response => {
      component.innerHTML = response.html;
    };

    const throttle = (func, limit) => {

      let throttleOn = false;
      let callsHaveBeenThrottled = false;
      let timeout;

      return function() {

        const args = arguments;
        const context = this;

        if (throttleOn) {
          callsHaveBeenThrottled = true;
        } else {
          func.apply(context, args);
          throttleOn = true;
        }

        clearTimeout(timeout);

        timeout = setTimeout(() => {
          throttleOn = false;
          if (callsHaveBeenThrottled) func.apply(context, args);
          callsHaveBeenThrottled = false;
        }, limit);

      };

    };

    this.start = component => {

      let id = 'update-status';

      this.component = component;
      this.textbox = document.getElementById(this.component.dataset.target);

      this.component.setAttribute('id', id);

      const currentAriaDescribedBy = this.textbox.getAttribute('aria-describedby') || '';
      const newAriaDescribedBy = currentAriaDescribedBy + (currentAriaDescribedBy ? ' ' : '') + id;
      this.textbox.setAttribute('aria-describedby', newAriaDescribedBy);

      this.textbox.addEventListener('input', throttle(this.update, 150));
      this.textbox.dispatchEvent(new Event('input'));

    };

    this.update = () => {

      const form = this.textbox.closest('form');
      const formData = new FormData(form);

      fetch(this.component.dataset.updatesUrl, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
      })
        .then(response => {
          if (!response.ok) {
            throw new Error('HTTP error');
          }
          return response.json();
        })
        .then(getRenderer(this.component))
        .catch(() => {});

    };

  };

})(window);
