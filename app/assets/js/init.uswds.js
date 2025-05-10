document.addEventListener("DOMContentLoaded", function () {
    if (window.uswds && typeof window.uswds.init === 'function') {
      console.log("Calling USWDS init");
      window.uswds.init();
    } else {
      console.error("USWDS not found or init is not a function");
    }
  });
