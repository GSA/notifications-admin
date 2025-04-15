/**
 * @jest-environment jsdom
 */

// Mock socket.io-client BEFORE importing your script
const onHandlers = {};

jest.mock("socket.io-client", () => {
  return jest.fn(() => ({
    on: jest.fn((event, cb) => {
      onHandlers[event] = cb;
    }),
    emit: jest.fn(),
    connected: true,
  }));
});

const io = require("socket.io-client");

// Import script AFTER mocks
require("../../app/assets/javascripts/socketio.js");

describe("job-socket.js", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () =>
          Promise.resolve({
            status: "<p>Status Updated</p>",
            counts: "<p>Counts Updated</p>",
            notifications: "<p>Notifications Updated</p>",
          }),
      })
    );
  });

  afterEach(() => {
    jest.clearAllMocks();
    jest.useRealTimers();
    Object.keys(onHandlers).forEach((key) => delete onHandlers[key]);
  });

  it("should initialize socket and update DOM on job_updated if feature flag is ON", () => {
    document.body.innerHTML = `
      <div data-job-id="123" data-feature="true"></div>
      <div data-socket-update="status" data-resource="/services/abc123/jobs/123.json"></div>
      <div data-socket-update="counts"></div>
      <div data-socket-update="notifications"></div>
    `;
    window.location.pathname = "/jobs/123";

    // Trigger DOMContentLoaded (after DOM is ready)
    document.dispatchEvent(new Event("DOMContentLoaded"));

    // Trigger socket connect + job update
    onHandlers.connect?.();
    onHandlers.job_updated?.({ job_id: "123" });

    // Flush debounce timer
    jest.runAllTimers();

    expect(global.fetch).toHaveBeenCalledWith("/services/abc123/jobs/123.json");
    expect(
      document.querySelector('[data-socket-update="status"]').innerHTML
    ).toBe("<p>Status Updated</p>");
    expect(
      document.querySelector('[data-socket-update="counts"]').innerHTML
    ).toBe("<p>Counts Updated</p>");
    expect(
      document.querySelector('[data-socket-update="notifications"]').innerHTML
    ).toBe("<p>Notifications Updated</p>");
  });

  it("should not connect or update if feature flag is OFF", () => {
    document.body.innerHTML = `
      <div data-job-id="123" data-feature="false"></div>
      <div data-socket-update="status" data-resource="/services/abc123/jobs/123.json"></div>
    `;
    window.location.pathname = "/jobs/123";

    document.dispatchEvent(new Event("DOMContentLoaded"));

    expect(global.fetch).not.toHaveBeenCalled();
    expect(onHandlers.connect).toBeUndefined();
  });

  it("should not connect or update if job ID is missing", () => {
    document.body.innerHTML = `
      <div data-feature="true"></div>
      <div data-socket-update="status" data-resource="/services/abc123/jobs/123.json"></div>
    `;
    window.location.pathname = "/jobs/123";

    document.dispatchEvent(new Event("DOMContentLoaded"));

    expect(global.fetch).not.toHaveBeenCalled();
    expect(onHandlers.connect).toBeUndefined();
  });
});
