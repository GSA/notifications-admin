(function (window) {

    // Dummy data (replace with API data)
    const data = {
        messageStats: {
            totalMessages: 1000,
            delivered: 800,
            pending: 100,
            failed: 100
        },
        dailyUsage: {
            dailyUsage: 20,
            dailyUsageLimit: 100
        },
        yearlyUsage: {
            yearlyUsage: 2000,
            yearlyUsageLimit: 250000
        }
    };

     // Update total messages progress bar percentages
    const messageStats = data.messageStats;

    const messageBars = ["delivered", "pending", "failed"];
        for (const bar of messageBars) {
        const percentage = messageStats[bar] / messageStats.totalMessages * 100;
        const elementId = `${bar}-bar`;
        const element = document.getElementById(elementId);
        element.style.width = `${parseFloat(percentage)}%`;
    }

    // Update total messages progress bar percentages
    const dailyUsage = data.dailyUsage;
    const dailyUsageLimit = dailyUsage.dailyUsageLimit;
    const yearlyUsage = data.yearlyUsage;
    const yearlyUsageLimit = yearlyUsage.yearlyUsageLimit;

    function updateUsageBar(elementId, dailyUsage, dailyUsageLimit, yearlyUsage, yearlyUsageLimit) {
        // Ensure element exists
        if (!elementId || !document.getElementById(elementId)) {
            console.error(`Element with ID "${elementId}" not found`);
            return;
        }

        // Calculate percentage
        const percentage = dailyUsage / dailyUsageLimit * 100;

        // Update bar width
        const element = document.getElementById(elementId);
        element.style.width = `${parseFloat(percentage)}%`;
    }

    // Update usage bars
    updateUsageBar("dailyUsage-bar", dailyUsage.dailyUsage, dailyUsageLimit);
    updateUsageBar("dailyUsageRemaining-bar", dailyUsageLimit - dailyUsage.dailyUsage, dailyUsageLimit);
    updateUsageBar("yearlyUsage-bar", yearlyUsage.yearlyUsage, yearlyUsageLimit);
    updateUsageBar("yearlyUsageRemaining-bar", yearlyUsageLimit - yearlyUsage.yearlyUsage, yearlyUsageLimit);

    // Update total messages legend values
    document.getElementById("total-value").innerText = `Total: ${messageStats.totalMessages} messages`;
    document.getElementById("delivered-value").innerText = `Delivered: ${messageStats.delivered}`;
    document.getElementById("pending-value").innerText = `Pending: ${messageStats.pending}`;
    document.getElementById("failed-value").innerText = `Failed: ${messageStats.failed}`;

    // Update usage legend values
    document.getElementById("daily-usage-value").innerText = dailyUsage.dailyUsage;
    document.getElementById("daily-remaining-value").innerText = dailyUsage.dailyUsageLimit - dailyUsage.dailyUsage;
    document.getElementById("yearly-usage-value").innerText = yearlyUsage.yearlyUsage;
    document.getElementById("yearly-remaining-value").innerText = yearlyUsage.yearlyUsageLimit - yearlyUsage.yearlyUsage;

})(window);
