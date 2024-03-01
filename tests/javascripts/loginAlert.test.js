beforeAll(() => {
    jest.spyOn(global, 'setTimeout');

     document.body.innerHTML = `
         <div id="countdown-container" class="usa-alert usa-alert--warning width-full margin-bottom-4">
            <div class="usa-alert__body">
            <h4 class="usa-alert__heading">Login.gov is required by April 9, 2024</h4>
            <p class="usa-alert__text">
                You have <span id="countdown"></span> left to use Login.gov to sign in
            </p>
            </div>
        </div>
    `

    const sessionTimerModule = require('../../app/assets/javascripts/loginAlert.js');
    window.GOVUK.modules.start();
});

jest.useFakeTimers();
const targetDate = new Date("April 9, 2024 00:00:00"); // Reference point

test('Hides the countdown if more than 10 days away', () => {
    jest.setSystemTime(targetDate.getTime() - 12 * 24 * 60 * 60 * 1000); // 12 days before

    window.updateCountdown(); // Update the countdown display

    expect(document.getElementById("countdown-container").style.display).toBe("none");
});

test('Shows the countdown if 10 days or less away', () => {
    jest.setSystemTime(targetDate.getTime() - 8 * 24 * 60 * 60 * 1000);

    window.updateCountdown();

    expect(document.getElementById("countdown-container").style.display).toBe("block");
});

test('Displays the correct number of days', () => {
    jest.setSystemTime(targetDate.getTime() - 5 * 24 * 60 * 60 * 1000);

    window.updateCountdown();

    expect(document.getElementById("countdown").textContent).toBe("5 days ");
});

test('Hides the countdown if the target date has passed', () => {
    jest.setSystemTime(targetDate.getTime() + 2 * 24 * 60 * 60 * 1000);

    window.updateCountdown();

    expect(document.getElementById("countdown-container").style.display).toBe("none");
});
