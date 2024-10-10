const baseUrl = 'http://localhost:6012';

// List of routes with paths and labels
const sublinks = [
  { label: 'Homepage', path: '/' },
  { label: 'Add Service', path: '/add-service' },
  { label: 'Get Started', path: '/using-notify/get-started' },
  { label: 'Trial Mode', path: '/using-notify/trial-mode' },
  { label: 'Pricing', path: '/using-notify/pricing' },
  { label: 'Delivery Status', path: '/using-notify/delivery-status' },
  { label: 'Guidance', path: '/using-notify/guidance' },
  { label: 'Features', path: '/features' },
  { label: 'Roadmap', path: '/features/roadmap' },
  { label: 'Security', path: '/features/security' },
  { label: 'Support', path: '/support' },
  { label: 'Guidance', path: '/guidance' },
  { label: 'Clear Goals', path: '/guidance/clear-goals' },
  { label: 'Rules And Regulations', path: '/guidance/rules-and-regulations' },
  { label: 'Establish Trust', path: '/guidance/establish-trust' },
  { label: 'Write For Action', path: '/guidance/write-for-action' },
  { label: 'Multiple Languages', path: '/guidance/multiple-languages' },
  { label: 'Benchmark Performance', path: '/guidance/benchmark-performance' },
  // Add more links here as needed
];

const createFullUrl = (base, path) => `${base}${path}`;

// Build url using base and path
const constructUrls = (base, sublinks) =>
  sublinks.reduce((acc, { label, path }) => {
    return { ...acc, [label]: createFullUrl(base, path) };
  }, {});

module.exports = {
  baseUrl,
  urls: constructUrls(baseUrl, sublinks),
};
