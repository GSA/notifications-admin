window.GOVUK = window.GOVUK || {};
window.GOVUK.Modules = window.GOVUK.Modules || {};
window.GOVUK.Modules.TimeoutPopup = window.GOVUK.Modules.TimeoutPopup || {};

(function(global) {
    "use strict";

    const sessionTimer = document.getElementById("sessionTimer");
    let intervalId = null;

    function checkTimer(timeTillSessionEnd) {
        var now = new Date().getTime();
        var difference = timeTillSessionEnd - now;
        var minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
        var seconds = Math.floor((difference % (1000 * 60)) / 1000);
        document.getElementById("timeLeft").innerHTML = + minutes + "m " + seconds + "s";
        showTimer();
        document.getElementById("logOutTimer").addEventListener("click", signoutUser);
        document.getElementById("extendSessionTimer").addEventListener("click", extendSession);
        if (difference < 0) {
            clearInterval(intervalId);
            intervalId = null;
            closeTimer();
            expireUserSession();
        }
    }

    function expireUserSession() {
        var signOutLink = '/sign-out?next=' + window.location.pathname;
        window.location.href = signOutLink;

    }

    function signoutUser() {
        window.location.href = '/sign-out';
    }

    function extendSession() {
        window.location.reload();
    }

    function showTimer() {
        sessionTimer.showModal();
    }

    function closeTimer() {
        sessionTimer.close();
    }

    function setSessionTimer() {
        var timeTillSessionEnd = new Date().getTime() + (5 * 60 * 1000);
        intervalId = setInterval(checkTimer, 1000, timeTillSessionEnd);
    }

    if (document.getElementById("timeLeft") !== null) {
        setTimeout(setSessionTimer, 25 * 60 * 1000);
    }

    global.GOVUK.Modules.TimeoutPopup.checkTimer = checkTimer;
    global.GOVUK.Modules.TimeoutPopup.expireUserSession = expireUserSession;
    global.GOVUK.Modules.TimeoutPopup.signoutUser = signoutUser;
    global.GOVUK.Modules.TimeoutPopup.extendSession = extendSession;
    global.GOVUK.Modules.TimeoutPopup.showTimer = showTimer;
    global.GOVUK.Modules.TimeoutPopup.closeTimer = closeTimer;
})(window);
