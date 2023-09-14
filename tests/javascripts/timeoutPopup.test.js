const sessionTimerWrapper = require('../../app/assets/javascripts/timeoutPopup.js');


describe('Test popup process', () => {
    beforeEach(() => {
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    it('Test timers work', () => {
        jest.runAllTimers();
        sessionTimerWrapper();
    });

}); 

