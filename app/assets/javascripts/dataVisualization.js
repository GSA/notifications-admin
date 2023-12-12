(function (window) {

    // Dummy data (replace with API data)
    const totalMessages = 1000;
    const delivered = 800;
    const pending = 100;
    const failed = 100;

    // Calculate percentages
    const deliveredPercentage = (delivered / totalMessages) * 100;
    const pendingPercentage = (pending / totalMessages) * 100;
    const failedPercentage = (failed / totalMessages) * 100;

    // Set width of bars
    document.getElementById("delivered").style.width = `${deliveredPercentage}%`;
    document.getElementById("pending").style.width = `${pendingPercentage}%`;
    document.getElementById("failed").style.width = `${failedPercentage}%`;

    // Update legend values
    document.getElementById("delivered-value").innerText = delivered;
    document.getElementById("pending-value").innerText = pending;
    document.getElementById("failed-value").innerText = failed;

})(window);
