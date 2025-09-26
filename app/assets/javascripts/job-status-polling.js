document.addEventListener('DOMContentLoaded', function () {
  // Verify we are on the job page
  const isJobPage = window.location.pathname.includes('/jobs/');
  if (!isJobPage) return;

  // Check if polling elements exist
  const hasPollingElements = document.querySelector('[data-key="counts"]');
  if (!hasPollingElements) return;

  // Extract job info from URL path: /services/{serviceId}/jobs/{jobId}
  const pathParts = window.location.pathname.split('/');
  if (
    pathParts.length < 5 ||
    pathParts[1] !== 'services' ||
    pathParts[3] !== 'jobs'
  )
    return;

  const serviceId = pathParts[2];
  const jobId = pathParts[4];

  // Validate service and job IDs to prevent path injection
  function isValidUuid(id) {
    const uuidRegex =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    return uuidRegex.test(id);
  }

  // Validate both IDs are UUIDs to prevent path injection attacks
  if (!isValidUuid(serviceId) || !isValidUuid(jobId)) {
    console.warn('Invalid service or job ID format detected');
    return;
  }

  const DEFAULT_INTERVAL_MS = 10000;
  const MIN_INTERVAL_MS = 1000;
  const MAX_INTERVAL_MS = 30000;

  let pollInterval;
  let currentInterval = DEFAULT_INTERVAL_MS;
  let isPolling = false;
  let lastProcessedCount = 0;

  function calculateBackoff(responseTime) {
    return Math.min(
      MAX_INTERVAL_MS,
      Math.max(
        MIN_INTERVAL_MS,
        Math.floor(250 * Math.sqrt(responseTime) - 1000),
      ),
    );
  }

  async function updateNotifications() {
    const notificationsUrl = `/services/${serviceId}/jobs/${jobId}.json`;

    try {
      const response = await fetch(notificationsUrl);
      if (!response.ok) {
        throw new Error(`Failed to fetch notifications: ${response.status}`);
      }

      const data = await response.json();

      // Update notifications container if it exists
      const notificationsContainer = document.querySelector(
        '[data-key="notifications"]',
      );
      if (notificationsContainer && data.notifications) {
        notificationsContainer.innerHTML = data.notifications;
      }
    } catch (error) {
      console.warn('Failed to update notifications:', error.message);
    }
  }

  async function updateAllJobSections(retryCount = 0) {
    if (isPolling || document.hidden) {
      return;
    }

    isPolling = true;

    const pollStatusUrl = `/services/${serviceId}/jobs/${jobId}/status.json`;

    try {
      const response = await fetch(pollStatusUrl);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      const countsContainer = document.querySelector('[data-key="counts"]');
      if (countsContainer) {
        // Get all big-number elements in order: total, pending, delivered, failed
        const countElements =
          countsContainer.querySelectorAll('.big-number-number');

        if (countElements.length >= 4) {
          if (data.total_count !== undefined) {
            countElements[0].textContent = data.total_count.toLocaleString();
          }

          if (data.pending_count !== undefined) {
            countElements[1].textContent = data.pending_count.toLocaleString();
          }

          if (data.sent_count !== undefined) {
            countElements[2].textContent = data.sent_count.toLocaleString();
          }

          if (data.failed_count !== undefined) {
            countElements[3].textContent = data.failed_count.toLocaleString();
          }
        }
      }

      currentInterval = calculateBackoff(DEFAULT_INTERVAL_MS);

      // Calculate how many messages have been processed
      const processedCount = (data.sent_count || 0) + (data.failed_count || 0);

      // Update notifications conditionally:
      // 1. If we have new messages and still under 50 total
      // 2. Always when job is finished
      if (
        processedCount > lastProcessedCount &&
        processedCount <= 50 &&
        !data.finished
      ) {
        // Update notifications for first 50 messages to show early results
        await updateNotifications();
        lastProcessedCount = processedCount;
      }

      if (data.finished === true) {
        await updateNotifications();
        stopPolling();
      }
    } catch (error) {
      if (retryCount < 3) {
        console.debug(`Job polling retry ${retryCount}`, error.message);
        isPolling = false;

        const retryDelay = Math.pow(2, retryCount) * 1000;
        setTimeout(() => {
          updateAllJobSections(retryCount + 1);
        }, retryDelay);
        return;
      }

      console.warn('Job polling failed after 3 retries:', {
        error: error.message,
        url: pollStatusUrl,
        jobId: jobId,
        timestamp: new Date().toISOString(),
      });
      currentInterval = Math.min(currentInterval * 2, MAX_INTERVAL_MS);
    } finally {
      isPolling = false;
    }
  }

  function startPolling() {
    updateAllJobSections();

    function scheduleNext() {
      if (pollInterval) clearTimeout(pollInterval);
      pollInterval = setTimeout(() => {
        updateAllJobSections();
        scheduleNext();
      }, currentInterval);
    }

    scheduleNext();
  }

  function stopPolling() {
    if (pollInterval) {
      clearTimeout(pollInterval);
      pollInterval = null;
    }
  }

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      stopPolling();
    } else {
      startPolling();
    }
  });

  window.addEventListener('beforeunload', stopPolling);

  startPolling();
});
