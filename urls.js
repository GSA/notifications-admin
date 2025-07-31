const baseUrl = process.env.BACKSTOP_BASE_URL || 'http://localhost:6012';

// List of routes organized by section
const routes = {
  // Main pages
  main: [
    { label: 'Homepage', path: '/' },
    { label: 'Add Service', path: '/add-service' },
    { label: 'Support', path: '/support' },
    { label: 'Notify.gov Service Ending', path: '/notify-service-ending' },
    { label: 'Notify.gov Sign In', path: '/sign-in' },
    { label: 'Accessibility Statement', path: '/accessibility-statement' },
    { label: 'Privacy', path: '/privacy' },
    { label: 'Email Not Received', path: '/email-not-received' },
    { label: 'Text Not Received', path: '/text-not-received' },
    { label: 'Performance', path: '/performance' },
  ],

  authenticated: [
    {
      label: 'SMS Template Preview',
      path: '/services/829ac564-59e9-47c5-ad69-e91315641c31/send/9c2b7a55-8785-4dc6-84d6-eb0e0615590d/one-off/step-0',
    },
    // Pages with govuk buttons that need testing
    {
      label: 'API Keys',
      path: '/services/829ac564-59e9-47c5-ad69-e91315641c31/api/keys',
    },
    // Pages to test radio buttons before converting govukRadios to USWDS
    {
      label: 'API Keys Create',
      path: '/services/829ac564-59e9-47c5-ad69-e91315641c31/api/keys/create',
    },
    {
      label: 'Change User Auth',
      path: '/users/6af522d0-2915-4e52-83a3-3690455a5fe6/change_auth',
    },
    {
      label: 'User Profile Timezone',
      path: '/user-profile/preferred_timezone',
    },
    {
      label: 'Service Settings',
      path: '/services/829ac564-59e9-47c5-ad69-e91315641c31/service-settings',
    },
    {
      label: 'Service Send Files By Email',
      path: '/services/829ac564-59e9-47c5-ad69-e91315641c31/service-settings/send-files-by-email',
    },
    {
      label: 'Service SMS Prefix',
      path: '/services/829ac564-59e9-47c5-ad69-e91315641c31/service-settings/sms-prefix',
    },
    {
      label: 'Send One Off Step 2',
      path: '/services/829ac564-59e9-47c5-ad69-e91315641c31/send/9c2b7a55-8785-4dc6-84d6-eb0e0615590d/one-off/step-2',
    },
    {
      label: 'Choose Template',
      path: '/services/829ac564-59e9-47c5-ad69-e91315641c31/templates',
    },
    {
      label: 'Team Members',
      path: '/services/829ac564-59e9-47c5-ad69-e91315641c31/users',
    },
    {
      label: 'Invite User',
      path: '/services/829ac564-59e9-47c5-ad69-e91315641c31/users/invite',
    },
    // Platform admin pages with checkboxes
    {
      label: 'Platform Admin Live Services',
      path: '/platform-admin/live-services',
    },
    // Organization pages
    {
      label: 'Add Organization',
      path: '/organizations/add',
    },
  ],

  // Using Notify section
  usingNotify: [
    { label: 'Get Started', path: '/using-notify/get-started' },
    { label: 'Trial Mode', path: '/using-notify/trial-mode' },
    { label: 'Pricing', path: '/using-notify/pricing' },
    { label: 'Pricing Billing Details', path: '/pricing/billing-details' },
    { label: 'Delivery Status', path: '/using-notify/delivery-status' },
    { label: 'How To', path: '/using-notify/how-to' },
    { label: 'Best Practices', path: '/using-notify/best-practices' },
  ],

  // Best Practices subsection
  bestPractices: [
    { label: 'Clear Goals', path: '/using-notify/best-practices/clear-goals' },
    {
      label: 'Rules And Regulations',
      path: '/using-notify/best-practices/rules-and-regulations',
    },
    {
      label: 'Establish Trust',
      path: '/using-notify/best-practices/establish-trust',
    },
    {
      label: 'Write For Action',
      path: '/using-notify/best-practices/write-for-action',
    },
    {
      label: 'Multiple Languages',
      path: '/using-notify/best-practices/multiple-languages',
    },
    {
      label: 'Benchmark Performance',
      path: '/using-notify/best-practices/benchmark-performance',
    },
  ],

  // About section
  about: [
    { label: 'About', path: '/about' },
    { label: 'Why Text Messaging', path: '/about/why-text-messaging' },
    { label: 'Security', path: '/about/security' },
  ],
};

// Flatten all routes into a single array
const sublinks = [
  ...routes.main,
  ...routes.usingNotify,
  ...routes.bestPractices,
  ...routes.about,
  ...routes.authenticated,
  // Add more sections here as needed
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
