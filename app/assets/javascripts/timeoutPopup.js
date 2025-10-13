window.NotifyModules = window.NotifyModules || {};
window.NotifyModules.TimeoutPopup = window.NotifyModules.TimeoutPopup || {};

(function(window) {
    "use strict";

    const sessionTimer = document.getElementById("sessionTimer");
    let intervalId = null;

    function checkTimer(timeTillSessionEnd) {
        var now = new Date().getTime();
        var difference = timeTillSessionEnd - now;
        var minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
        var seconds = Math.floor((difference % (1000 * 60)) / 1000);
        document.getElementById("timeLeft").textContent = minutes + "m " + seconds + "s";
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

    window.NotifyModules.TimeoutPopup.checkTimer = checkTimer;
    window.NotifyModules.TimeoutPopup.expireUserSession = expireUserSession;
    window.NotifyModules.TimeoutPopup.signoutUser = signoutUser;
    window.NotifyModules.TimeoutPopup.extendSession = extendSession;
    window.NotifyModules.TimeoutPopup.showTimer = showTimer;
    window.NotifyModules.TimeoutPopup.closeTimer = closeTimer;
})(window);
