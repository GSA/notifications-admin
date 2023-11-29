(function (window) {
    "use strict";

    // Show the current year
    const currentYearElement = document.getElementById("current-year");

    if (currentYearElement) {
        currentYearElement.textContent = new Date().getFullYear();
    }
})(window);