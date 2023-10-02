beforeAll(() => {
    jest.useFakeTimers();
    jest.spyOn(global, 'setTimeout');

    document.body.innerHTML = `
        <dialog class="usa-modal" id="sessionTimer" aria-labelledby="sessionTimerHeading" aria-describedby="timerWarning">
            <div class="usa-modal__content">
                <div class="usa-modal__main">
                <h2 class="usa-modal__heading" id="sessionTimerHeading">
                    Your session will end soon.
                    <span class="usa-sr-only">Please choose to extend your session or sign out. Your session will expire in 5 minutes or less.</span>
                </h2>
                <div class="usa-prose">
                    <p>You have been inactive for too long.
                    Your session will expire in <span id="timeLeft" role="timer"></span>.
                    </p>
                </div>
                <div class="usa-modal__footer">
                    <ul class="usa-button-group">
                    <li class="usa-button-group__item">
                        <button type="button" class="usa-button" id="extendSessionTimer" data-close-modal>
                        Extend Session
                        </button>
                    </li>
                    <li class="usa-button-group__item">
                        <button type="button" class="usa-button usa-button--unstyled padding-105 text-center" id="logOutTimer"
                        data-close-modal>
                        Sign out
                        </button>
                    </li>
                    </ul>
                </div>
                </div>
            </div>
        </dialog>
    `

        const sessionTimerModule = require('../../app/assets/javascripts/timeoutPopup.js');
        window.GOVUK.modules.start();
});

afterAll(() => {
    jest.useRealTimers();
    document.body.innerHTML = '';
});


describe('When an authenticated user', () => {
    test('does whatever', () => {
        jest.runAllTimers();
    });

});


describe('The session timer ', () => {
    test('logoutUser method logs the user out', () => {
        const logoutUserMethod = window.GOVUK.Modules.TimeoutPopup.logoutUser;

        expect(window.location.href).toEqual(expect.not.stringContaining('/sign-out'));

        logoutUserMethod();

        expect(window.location.href).toEqual(expect.stringContaining('/sign-out'));
    });

    test('extendSession method reloads the page', () => {
        const windowReload = jest.spyOn(window.location, 'reload');
        const extendSessionMethod = window.GOVUK.Modules.TimeoutPopup.extendSession;

        extendSessionMethod();

        expect(windowReload).toHaveBeenCalled();
    });

    test('showTimer method shows the session timer modal', () => {
        const sessionTimer = document.getElementById("sessionTimer");
        sessionTimer.showModal = jest.fn();

        const showTimerMock = jest.spyOn(sessionTimer, 'showModal');

        window.GOVUK.Modules.TimeoutPopup.showTimer();

        expect(showTimerMock).toHaveBeenCalled();
    });

    test('closeTimer method closes the session timer modal', () => {
        const sessionTimer = document.getElementById("sessionTimer");
        sessionTimer.close = jest.fn();

        const closeTimerMock = jest.spyOn(sessionTimer, 'close');

        window.GOVUK.Modules.TimeoutPopup.closeTimer();

        expect(closeTimerMock).toHaveBeenCalled();
    });

    test('checkTimer is called', () => {
        const checkTimerMock = jest.spyOn(window.GOVUK.Modules.TimeoutPopup, "checkTimer");
        window.GOVUK.Modules.TimeoutPopup.checkTimer();
        expect(checkTimerMock).toHaveBeenCalled();
    });
});
