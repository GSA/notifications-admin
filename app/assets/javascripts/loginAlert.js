const targetDate = new Date("April 16, 2024 00:00:00").getTime();

export function updateCountdown() {
  const countdownContainer = document.getElementById("countdown-container");

  if (countdownContainer) {
    const now = new Date().getTime();
    const difference = targetDate - now;
    const days = Math.floor(difference / (1000 * 60 * 60 * 24));

    if (days < 0 || days > 10) {
      countdownContainer.style.display = "none";
    } else {
      countdownContainer.style.display = "block";
      document.getElementById("countdown").innerHTML = days + " days ";
    }
  }
}

export function initLoginAlert() {
  window.updateCountdown = updateCountdown;
  updateCountdown();
  setInterval(updateCountdown, 1000);
}
