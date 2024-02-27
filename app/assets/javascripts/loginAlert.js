(function (window) {

// Set the target date (10 days before March 15th, 2024)
  const targetDate = new Date("April 9, 2024 00:00:00").getTime();

 // Function to update the countdown display
  function updateCountdown() {
    const now = new Date().getTime();
    const difference = targetDate - now;

    // Time calculations for days only
    const days = Math.floor(difference / (1000 * 60 * 60 * 24));

    // Visibility logic
    if (days < 0) {
      // Hide if more than 10 days away OR if already past the date
      document.getElementById("countdown-container").style.display = "none";
    } else {
      // Show if 10 days or less remaining
      document.getElementById("countdown-container").style.display = "block";
      document.getElementById("countdown").innerHTML = days + " days ";
    }

  }

    // Expose the updateCountdown function to the outside world
  window.updateCountdown = updateCountdown;

  // Initial display update
  updateCountdown();

  // Update the countdown every second (inside the IIFE)
  setInterval(updateCountdown, 1000);

})(window);
