const sessionTimerWrapper = function() {
    "use strict";
    (function(global) {
    const sessionTimer = document.getElementById("sessionTimer");

    setTimeout(function() {
        var timeTillSessionEnd = new Date().getTime() + (5 * 60 * 1000);
        var x = setInterval(function() {
            var now = new Date().getTime();
            var difference = timeTillSessionEnd - now;
            var minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
            var seconds = Math.floor((difference % (1000 * 60)) / 1000);
            document.getElementById("timeLeft").innerHTML = + minutes + "m " + seconds + "s";
            showTimer();
            document.getElementById("logOutTimer").addEventListener("click", logoutUser);
            document.getElementById("extendSessionTimer").addEventListener("click", extendSession);
            if (difference < 0) {
                clearInterval(x);
                closeTimer();
                logoutUser();
            }
        }, 1000);
    }, 60 * 1000);

    function logoutUser() {
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
    })(window);
};

module.exports = sessionTimerWrapper;

(function(){
    sessionTimerWrapper();
})();
