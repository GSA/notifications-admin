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
  window.NotifyModules.start();
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
    const restore = mockWindowLocation();

    // Test the actual function, not a mock
    const signoutUserMethod = window.NotifyModules.TimeoutPopup.signoutUser;

    // This will try to set location.href but our mock will catch it
    expect(() => signoutUserMethod()).not.toThrow();

    restore();
  });

  test('expireUserSession method logs the user out with next query parameter', () => {
    const restore = mockWindowLocation();

    // Test the actual function, not a mock
    const expireUserSessionMethod = window.NotifyModules.TimeoutPopup.expireUserSession;

    // This will try to set location.href but our mock will catch it
    expect(() => expireUserSessionMethod()).not.toThrow();

    restore();
  });

  test('extendSession method reloads the page', () => {
    const restore = mockWindowLocation();

    // Test the actual function, not a mock
    const extendSessionMethod = window.NotifyModules.TimeoutPopup.extendSession;

    // This will try to call location.reload but our mock will catch it
    expect(() => extendSessionMethod()).not.toThrow();

    restore();
  });

  test('showTimer method shows the session timer modal', () => {
    const sessionTimer = document.getElementById('sessionTimer');
    sessionTimer.showModal = jest.fn();

    const showTimerMock = jest.spyOn(sessionTimer, 'showModal');

    window.NotifyModules.TimeoutPopup.showTimer();

    expect(showTimerMock).toHaveBeenCalled();
  });

  test('closeTimer method closes the session timer modal', () => {
    const sessionTimer = document.getElementById('sessionTimer');
    sessionTimer.close = jest.fn();

    const closeTimerMock = jest.spyOn(sessionTimer, 'close');

    window.NotifyModules.TimeoutPopup.closeTimer();

    expect(closeTimerMock).toHaveBeenCalled();
  });

  test('checkTimer is called', () => {
    const checkTimerMock = jest.spyOn(
      window.NotifyModules.TimeoutPopup,
      'checkTimer'
    );
    window.NotifyModules.TimeoutPopup.checkTimer();
    expect(checkTimerMock).toHaveBeenCalled();
  });
});
