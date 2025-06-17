// Fixes for browser features that JSDOM doesn't support or handles differently
//
// Jest 30 was a bit of a game changer for how window.location works in tests.
// The old tricks we used to use for mocking location don't work anymore, but
// honestly the new approach is cleaner once you get used to it.

// Stop JSDOM from complaining about navigation attempts
const originalConsoleError = console.error;
console.error = function(message, ...args) {
  if (typeof message === 'object' && message.message && message.message.includes('Not implemented: navigation')) {
    return; // Just ignore these, they're not helpful in tests
  }
  if (typeof message === 'string' && message.includes('Not implemented: navigation')) {
    return; // Just ignore these, they're not helpful in tests
  }
  originalConsoleError.apply(console, [message, ...args]);
};

// A helper for tests that need to fake window.location behavior
global.mockWindowLocation = function(mockValues = {}) {
  const originalLocation = window.location;

  // Jest 30 won't let us mess with href directly, so we work around it
  let hrefAssignments = [];
  let currentHref = mockValues.href || 'https://beta.notify.gov/';

  // Build a fake location object that behaves like the real thing
  const mockLocation = {
    href: currentHref,
    pathname: mockValues.pathname || '/',
    search: '',
    hash: '',
    host: 'beta.notify.gov',
    hostname: 'beta.notify.gov',
    protocol: 'https:',
    port: '',
    origin: 'https://beta.notify.gov',
    assign: mockValues.assign || jest.fn(),
    reload: mockValues.reload || jest.fn(),
    replace: mockValues.replace || jest.fn(),
    toString: () => currentHref,
    ...mockValues
  };

  // Make href track changes when code tries to navigate
  Object.defineProperty(mockLocation, 'href', {
    get() { return currentHref; },
    set(value) {
      currentHref = value;
      hrefAssignments.push(value);
    },
    configurable: true,
    enumerable: true
  });

  // Swap out the real location for our fake one
  delete window.location;
  window.location = mockLocation;

  // Return a function to put everything back when the test is done
  return () => {
    delete window.location;
    window.location = originalLocation;
    return { hrefAssignments, currentHref };
  };
};
