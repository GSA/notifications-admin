const baseUrl = 'http://localhost:6012';

// List of routes with paths and labels
const sublinks = [
  { label: 'Homepage', path: '/' },
  { label: 'Accounts', path: '/accounts' },
  { label: 'Add Service', path: '/add-service' },
  { label: 'Get Started', path: '/using-notify/get-started' },
  { label: 'Trial Mode', path: '/using-notify/trial-mode' },
  { label: 'Pricing', path: '/using-notify/pricing' },
  { label: 'Delivery Status', path: '/using-notify/delivery-status' },
  { label: 'Guidance', path: '/using-notify/guidance' },
  { label: 'Features', path: '/features' },
  { label: 'Roadmaps', path: '/features/roadmaps' },
  { label: 'Security', path: '/features/security' },
  { label: 'Support', path: '/support' },
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
