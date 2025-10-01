(function() {
  'use strict';

  const POLLING_CONFIG = {
    POLL_INTERVAL_MS: 5000,
    MAX_RETRY_ATTEMPTS: 3,
    MAX_BACKOFF_MS: 60000
  };

  const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;


  class StatusPoller {
    constructor(serviceId, jobId, countsContainer) {
      this.serviceId = serviceId;
      this.jobId = jobId;
      this.countsContainer = countsContainer;
      this.pollInterval = null;
      this.isPolling = false;
      this.abortController = null;
      this.lastFinishedState = false;
      this.lastResponse = null;
      this.currentInterval = POLLING_CONFIG.POLL_INTERVAL_MS;
    }

    async poll(retryCount = 0) {
      if (this.isPolling || document.hidden || this.lastFinishedState) {
        return;
      }

      this.isPolling = true;

      if (this.abortController) {
        this.abortController.abort();
      }

      this.abortController = new AbortController();

      try {
        const response = await fetch(
          `/services/${this.serviceId}/jobs/${this.jobId}/status.json`,
          { signal: this.abortController.signal }
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        const responseChanged = this.lastResponse === null ||
          JSON.stringify(data) !== JSON.stringify(this.lastResponse);

        if (responseChanged) {
          const wasBackedOff = this.currentInterval !== POLLING_CONFIG.POLL_INTERVAL_MS;
          this.currentInterval = POLLING_CONFIG.POLL_INTERVAL_MS;
          if (wasBackedOff) {
            this.reschedulePolling();
          }
        } else {
          const oldInterval = this.currentInterval;
          this.currentInterval = Math.min(
            this.currentInterval * 2,
            POLLING_CONFIG.MAX_BACKOFF_MS
          );
          if (this.currentInterval !== oldInterval) {
            this.reschedulePolling();
          }
        }

        this.lastResponse = data;
        this.updateStatusCounts(data);

        if (data.finished === true && !this.lastFinishedState) {
          this.lastFinishedState = true;
          this.stop();

          setTimeout(() => {
            this.loadNotificationsTable();
          }, 1000);
        }

        return 0;
      } catch (error) {
        return this.handleError(error, retryCount);
      } finally {
        this.isPolling = false;
        this.abortController = null;
      }
    }

    handleError(error, retryCount) {
      if (error.name === 'AbortError') {
        console.debug('Status poll aborted');
        return;
      }

      const nextRetryCount = retryCount + 1;
      const backoffDelay = Math.min(
        Math.pow(2, retryCount) * 1000,
        POLLING_CONFIG.MAX_BACKOFF_MS
      );

      if (retryCount < POLLING_CONFIG.MAX_RETRY_ATTEMPTS) {
        console.debug(
          `Status polling retry ${nextRetryCount}/${POLLING_CONFIG.MAX_RETRY_ATTEMPTS}`,
          error.message
        );
      } else {
        console.debug(
          `Status polling retry ${nextRetryCount} (backing off ${backoffDelay}ms)`,
          error.message
        );
      }

      setTimeout(() => {
        this.poll(nextRetryCount);
      }, backoffDelay);
    }

    updateStatusCounts(data) {
      const countElements = this.countsContainer.querySelectorAll('.big-number-number');

      if (countElements.length >= 4) {
        countElements[0].textContent = (data.total || 0).toLocaleString();
        countElements[1].textContent = (data.pending || 0).toLocaleString();
        countElements[2].textContent = (data.delivered || 0).toLocaleString();
        countElements[3].textContent = (data.failed || 0).toLocaleString();
      }
    }

    loadNotificationsTable() {
      const url = `${window.location.href.split('?')[0]}?_=${Date.now()}`;

      fetch(url, {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      })
        .then(response => response.text())
        .then(html => {
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, 'text/html');
          const notificationsTable = doc.querySelector('.job-status-table');

          if (notificationsTable) {
            const insertPoint = document.querySelector('.notification-status');
            if (insertPoint) {
              insertPoint.insertAdjacentElement('afterend', notificationsTable);
            } else {
              window.location.reload();
            }
          } else {
            window.location.reload();
          }
        })
        .catch(error => {
          console.error('Failed to load notifications:', error);
          window.location.reload();
        });
    }

    reschedulePolling() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval);
      }

      this.pollInterval = setInterval(() => {
        this.poll();
      }, this.currentInterval);
    }

    async start() {
      await this.poll();

      this.pollInterval = setInterval(() => {
        this.poll();
      }, this.currentInterval);
    }

    stop() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval);
        this.pollInterval = null;
      }

      if (this.abortController) {
        this.abortController.abort();
        this.abortController = null;
      }
    }

    handleVisibilityChange() {
      if (document.hidden) {
        this.stop();
      } else if (!this.lastFinishedState) {
        this.start();
      }
    }
  }

  function initializeJobPolling() {
    const isJobPage = window.location.pathname.includes('/jobs/');
    if (!isJobPage) return;

    const countsContainer = document.querySelector('[data-key="counts"]');
    if (!countsContainer) return;

    const pathParts = window.location.pathname.split('/');
    if (pathParts.length < 5 || pathParts[1] !== 'services' || pathParts[3] !== 'jobs') {
      return;
    }

    const serviceId = pathParts[2];
    const jobId = pathParts[4];

    if (!UUID_REGEX.test(serviceId) || !UUID_REGEX.test(jobId)) {
      return;
    }

    const jobElement = document.querySelector('[data-job-id]');
    const isJobFinished = jobElement && jobElement.dataset.jobFinished === 'true';

    if (isJobFinished) {
      return;
    }

    const statusPoller = new StatusPoller(serviceId, jobId, countsContainer);

    document.addEventListener('visibilitychange', () => {
      statusPoller.handleVisibilityChange();
    });

    window.addEventListener('beforeunload', () => {
      statusPoller.stop();
    });

    statusPoller.start();
  }

  document.addEventListener('DOMContentLoaded', initializeJobPolling);
})();
