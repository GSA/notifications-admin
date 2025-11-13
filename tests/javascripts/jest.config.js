module.exports = {
  collectCoverage: true,
  coverageDirectory: './coverage',
  coveragePathIgnorePatterns: [
    'support/polyfills.js',
    'support/helpers/'
  ],
  coverageThreshold: {
    global: {
      branches: 75,
      functions: 90,
      lines: 90,
      statements: 90,
    }
  },
  setupFiles: ['./support/setup.js', './support/jest.setup.js'],
  testEnvironment: 'jsdom',
  testEnvironmentOptions: {
    url: 'https://beta.notify.gov',
  },
  transform: {
    '^.+\\.js$': ['babel-jest', { rootMode: 'upward' }],
  },
  transformIgnorePatterns: [
    'node_modules/(?!(d3|d3-array|d3-axis|d3-brush|d3-chord|d3-collection|d3-color|d3-contour|d3-dispatch|d3-drag|d3-dsv|d3-ease|d3-fetch|d3-force|d3-format|d3-geo|d3-hierarchy|d3-interpolate|d3-path|d3-polygon|d3-quadtree|d3-random|d3-scale|d3-scale-chromatic|d3-selection|d3-shape|d3-tile|d3-time|d3-time-format|d3-timer|d3-transition|d3-voronoi|d3-zoom)/)'
  ],
};
