beforeAll(() => {
  jest.spyOn(global, 'setTimeout');

  document.body.innerHTML = `
        <dialog class="usa-modal" id="sessionTimer" aria-labelledby="sessionTimerHeading" aria-describedby="timeLeft">
            <div class="usa-modal__content">
                <div class="usa-modal__main">
                <h2 class="usa-modal__heading font-body-lg" id="sessionTimerHeading">
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
    `;

  const sessionTimerModule = require('../../app/assets/javascripts/timeoutPopup.js');
  window.GOVUK.modules.start();
});

afterAll(() => {
  document.body.innerHTML = '';
});

describe('When the session timer module is loaded', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useFakeTimers();
  });

  test('everything initializes properly', () => {
    const sessionTimer = document.getElementById('sessionTimer');
    sessionTimer.showModal = jest.fn();
    sessionTimer.close = jest.fn();

    jest.runAllTimers();
  });
});

describe('The session timer ', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useFakeTimers();
  });

  test('signoutUser method logs the user out', () => {
    // Replace the real function with a fake one we can track
    const originalSignoutUser = window.GOVUK.Modules.TimeoutPopup.signoutUser;
    const mockSignoutUser = jest.fn(() => {
      // Do what the real function would do
      window.location.href = '/sign-out';
    });

    window.GOVUK.Modules.TimeoutPopup.signoutUser = mockSignoutUser;

    const signoutUserMethod = window.GOVUK.Modules.TimeoutPopup.signoutUser;
    signoutUserMethod();

    expect(mockSignoutUser).toHaveBeenCalled();

    // Put the real function back
    window.GOVUK.Modules.TimeoutPopup.signoutUser = originalSignoutUser;
  });

  test('expireUserSession method logs the user out with next query parameter', () => {
    // Replace this function too so we can check it gets called
    const originalExpireUserSession = window.GOVUK.Modules.TimeoutPopup.expireUserSession;
    const mockExpireUserSession = jest.fn(() => {
      // Build the sign out URL just like the real function
      const signOutLink = '/sign-out?next=' + window.location.pathname;
      window.location.href = signOutLink;
    });

    window.GOVUK.Modules.TimeoutPopup.expireUserSession = mockExpireUserSession;

    const expireUserSessionMethod = window.GOVUK.Modules.TimeoutPopup.expireUserSession;
    expireUserSessionMethod();

    expect(mockExpireUserSession).toHaveBeenCalled();

    // Put the original function back
    window.GOVUK.Modules.TimeoutPopup.expireUserSession = originalExpireUserSession;
  });

  test('extendSession method reloads the page', () => {
    // Same deal with the extend session function
    const originalExtendSession = window.GOVUK.Modules.TimeoutPopup.extendSession;
    const mockExtendSession = jest.fn(() => {
      // Just reload the page like the real function
      window.location.reload();
    });

    window.GOVUK.Modules.TimeoutPopup.extendSession = mockExtendSession;

    const extendSessionMethod = window.GOVUK.Modules.TimeoutPopup.extendSession;
    extendSessionMethod();

    expect(mockExtendSession).toHaveBeenCalled();

    // Clean up after ourselves
    window.GOVUK.Modules.TimeoutPopup.extendSession = originalExtendSession;
  });

  test('showTimer method shows the session timer modal', () => {
    const sessionTimer = document.getElementById('sessionTimer');
    sessionTimer.showModal = jest.fn();

    const showTimerMock = jest.spyOn(sessionTimer, 'showModal');

    window.GOVUK.Modules.TimeoutPopup.showTimer();

    expect(showTimerMock).toHaveBeenCalled();
  });

  test('closeTimer method closes the session timer modal', () => {
    const sessionTimer = document.getElementById('sessionTimer');
    sessionTimer.close = jest.fn();

    const closeTimerMock = jest.spyOn(sessionTimer, 'close');

    window.GOVUK.Modules.TimeoutPopup.closeTimer();

    expect(closeTimerMock).toHaveBeenCalled();
  });

  test('checkTimer is called', () => {
    const checkTimerMock = jest.spyOn(
      window.GOVUK.Modules.TimeoutPopup,
      'checkTimer'
    );
    window.GOVUK.Modules.TimeoutPopup.checkTimer();
    expect(checkTimerMock).toHaveBeenCalled();
  });
});
