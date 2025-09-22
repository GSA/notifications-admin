document.addEventListener('DOMContentLoaded', function () {
  const isJobPage = window.location.pathname.includes('/jobs/');
  if (!isJobPage) return;

  const jobEl = document.querySelector('[data-job-id]');
  const jobId = jobEl?.dataset?.jobId;
  const featureEnabled = jobEl?.dataset?.feature === 'true';
  const apiHost = jobEl?.dataset?.host;

  if (!jobId || !featureEnabled) return;

  const DEFAULT_INTERVAL_MS = 10000;
  const MIN_INTERVAL_MS = 1000;
  const MAX_INTERVAL_MS = 30000;

  let pollInterval;
  let currentInterval = DEFAULT_INTERVAL_MS;
  let isPolling = false;

  function calculateBackoff(responseTime) {
    return Math.min(
      MAX_INTERVAL_MS,
      Math.max(
        MIN_INTERVAL_MS,
        Math.floor((250 * Math.sqrt(responseTime)) - 1000)
      )
    );
  }

  async function updateAllJobSections(retryCount = 0) {
    if (isPolling || document.hidden) {
      return;
    }

    isPolling = true;
    const startTime = Date.now();

    const resourceEl = document.querySelector('[data-socket-update="status"]');
    const url = resourceEl?.dataset?.resource;

    if (!url) {
      isPolling = false;
      return;
    }

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();

      const sections = {
        status: document.querySelector('[data-socket-update="status"]'),
        counts: document.querySelector('[data-socket-update="counts"]'),
        notifications: document.querySelector('[data-socket-update="notifications"]'),
      };

      if (data.status && sections.status) {
        sections.status.innerHTML = data.status;
      }
      if (data.counts && sections.counts) {
        sections.counts.innerHTML = data.counts;
      }
      if (data.notifications && sections.notifications) {
        sections.notifications.innerHTML = data.notifications;
      }

      const responseTime = Date.now() - startTime;
      currentInterval = calculateBackoff(responseTime);

      if (data.stop === 1 || data.finished === true) {
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
        url: url,
        jobId: jobId,
        timestamp: new Date().toISOString()
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
