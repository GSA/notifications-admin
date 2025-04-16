require('../../app/assets/javascripts/fullscreenTable.js');

describe('fullscreenTable', () => {
  let wrapper, rightShadow;

  const setupDOM = (scrollLeft = 0, scrollWidth = 1000, clientWidth = 500) => {
    document.body.innerHTML = `
      <div class="fullscreen-table">
        <div class="table-wrapper" style="overflow-x: scroll;">
          <table>
            <tr><td>Test</td></tr>
          </table>
        </div>
        <div class="fullscreen-right-shadow"></div>
      </div>
    `;

    wrapper = document.querySelector('.table-wrapper');
    rightShadow = document.querySelector('.fullscreen-right-shadow');

    // Mock scroll values
    Object.defineProperty(wrapper, 'scrollLeft', {
      get: () => scrollLeft,
      configurable: true
    });
    Object.defineProperty(wrapper, 'scrollWidth', {
      get: () => scrollWidth,
      configurable: true
    });
    Object.defineProperty(wrapper, 'clientWidth', {
      get: () => clientWidth,
      configurable: true
    });

    // 👇 Now that DOM is ready, initialize the logic
    window.initFullscreenTables();

    // Force trigger scroll event if needed
    wrapper.dispatchEvent(new Event('scroll'));
  };

  afterEach(() => {
    document.body.innerHTML = '';
  });

  test('adds right shadow on initial load if scrollable', () => {
    setupDOM(0, 1000, 500);
    expect(wrapper.classList.contains('scrolled')).toBe(false);
    expect(rightShadow.classList.contains('visible')).toBe(true);
  });

  test('hides right shadow when scrolled to max', () => {
    setupDOM(500, 1000, 500);
    expect(wrapper.classList.contains('scrolled')).toBe(true);
    expect(rightShadow.classList.contains('visible')).toBe(false);
  });

  test('handles mid-scroll: left + right shadows active', () => {
    setupDOM(250, 1000, 500);
    expect(wrapper.classList.contains('scrolled')).toBe(true);
    expect(rightShadow.classList.contains('visible')).toBe(true);
  });

  test('gracefully handles missing right shadow', () => {
    document.body.innerHTML = `
      <div class="fullscreen-table">
        <div class="table-wrapper">
          <table>
            <tr><td>Only content</td></tr>
          </table>
        </div>
      </div>
    `;

    wrapper = document.querySelector('.table-wrapper');

    Object.defineProperty(wrapper, 'scrollLeft', { get: () => 100, configurable: true });
    Object.defineProperty(wrapper, 'scrollWidth', { get: () => 500, configurable: true });
    Object.defineProperty(wrapper, 'clientWidth', { get: () => 200, configurable: true });

    // 👇 Call after building DOM
    window.initFullscreenTables();
    wrapper.dispatchEvent(new Event('scroll'));

    expect(wrapper.classList.contains('scrolled')).toBe(true);
    // No error thrown for missing .fullscreen-right-shadow
  });
});
